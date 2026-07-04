"""
core/llm_engine.py — Unified Multi-Agent Engine for DataSense AI.

All agents are powered by Google Gemini 1.5 Flash (free tier).
The API key is loaded from the GEMINI_API_KEY environment variable.

Agents:
  - ProfilerAgent    : Auto-summarizes uploaded datasets in natural language
  - WranglingAgent   : Converts natural language cleaning commands → wrangling actions
  - MLStrategyAgent  : Recommends ML models and explains why for a given dataset
  - NarratorAgent    : Replaces template-based narration with dynamic LLM explanations
  - HypothesisAgent  : Semantically validates user hypotheses against findings
  - QAAgent          : Answers free-form user questions about the data with safe code exec
"""

import os
import ast
import pandas as pd
import numpy as np

try:
    from google import genai
    _GENAI_AVAILABLE = True
    _genai_client = None
except ImportError:
    _GENAI_AVAILABLE = False

# ── Gemini setup ─────────────────────────────────────────────────────────────

def setup_gemini(api_key: str = None):
    """Configure Gemini. Uses env var if no key provided."""
    global _genai_client
    if not _GENAI_AVAILABLE:
        raise ImportError("google-genai is not installed. Run: pip install google-genai")
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    _genai_client = genai.Client(api_key=key)

def _call(prompt: str, fallback: str = "") -> str:
    """Single-shot Gemini call with graceful fallback."""
    try:
        resp = _genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return resp.text.strip()
    except Exception as e:
        return fallback or f"[AI unavailable: {e}]"

def _df_context(df: pd.DataFrame, max_rows: int = 3) -> str:
    """Build a compact dataset context string for prompts."""
    ctx  = f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
    ctx += f"Columns & dtypes:\n{df.dtypes.to_string()}\n\n"
    ctx += f"Sample rows:\n{df.head(max_rows).to_string()}\n\n"
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if not nulls.empty:
        ctx += f"Missing values:\n{nulls.to_string()}\n"
    return ctx


# ── Agent 1: Profiler Agent ───────────────────────────────────────────────────

def profiler_agent(df: pd.DataFrame) -> str:
    """
    ProfilerAgent — Auto-generates a rich natural-language summary of the dataset.
    Called automatically on the Data Mining page after upload.
    """
    prompt = f"""
You are an expert data scientist and communicator.
Analyze this dataset and write a 3-4 paragraph executive summary.

Cover:
1. What this dataset likely represents (domain guess from column names)
2. Data quality issues (missing values, duplicates, high-cardinality columns)
3. The most interesting columns and relationships you can infer from names/types
4. What type of ML problem this might suit (classification, regression, clustering)

Be specific, use the column names, and write as if briefing a non-technical stakeholder.

{_df_context(df, max_rows=5)}

Stats summary:
{df.describe(include='all').to_string()}
"""
    return _call(prompt, fallback="Could not auto-profile this dataset.")


# ── Agent 2: Wrangling Agent ──────────────────────────────────────────────────

WRANGLING_ACTIONS = [
    "fill_missing_mean", "fill_missing_median", "fill_missing_mode",
    "drop_duplicates", "drop_high_null_columns",
    "label_encode_categoricals", "drop_column",
    "clip_outliers_iqr", "extract_date_features", "clean_text"
]

def wrangling_agent(df: pd.DataFrame, user_instruction: str) -> list[dict]:
    """
    WranglingAgent — Converts a natural language cleaning instruction into a
    structured list of wrangling actions that the wrangling.py page can execute.

    Returns a list of action dicts: [{"action": "...", "column": "..."}]
    """
    prompt = f"""
You are an expert data cleaning agent.
The user said: "{user_instruction}"

Dataset context:
{_df_context(df)}

Based on the instruction, output a JSON array of wrangling steps to perform.
Each step must be one of these actions: {WRANGLING_ACTIONS}
For actions targeting a column, include a "column" key.

Output ONLY valid JSON. No explanation, no markdown. Example:
[
  {{"action": "drop_duplicates"}},
  {{"action": "fill_missing_median", "column": "Age"}},
  {{"action": "label_encode_categoricals", "column": "Gender"}}
]
"""
    raw = _call(prompt, fallback="[]")
    # Strip any accidental markdown code fences
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        actions = __import__("json").loads(raw)
        if isinstance(actions, list):
            return actions
    except Exception:
        pass
    return []


# ── Agent 3: ML Strategy Agent ────────────────────────────────────────────────

def ml_strategy_agent(df: pd.DataFrame, target_col: str, ml_task: str) -> str:
    """
    MLStrategyAgent — Recommends which ML models to use and explains why,
    given the dataset characteristics and the problem type.
    """
    n_rows, n_cols = df.shape
    prompt = f"""
You are a senior ML engineer advising a data scientist.

Dataset facts:
- Shape: {n_rows} rows × {n_cols} columns
- Target column: '{target_col}'
- Task type: {ml_task}
- Feature types: {dict(df.dtypes.value_counts().astype(str))}
- Missing values: {int(df.isnull().sum().sum())} cells

{_df_context(df)}

Give a 3-5 sentence recommendation on which ML models to try first and why.
Then list 2-3 specific risks or things to watch out for with this dataset.
Be concise, specific, and technical. Mention class imbalance if the task is classification.
"""
    return _call(prompt, fallback="Could not generate ML strategy recommendation.")


# ── Agent 4: Narrator Agent ───────────────────────────────────────────────────

def narrator_agent(event: str, context: dict) -> str:
    """
    NarratorAgent — Generates dynamic, context-aware plain-English explanations
    for any platform event. Replaces static templates in narrator.py.

    event: short label like "wrangling_step", "outlier_detected", "model_trained"
    context: dict of relevant data (e.g. {"action": "Fill Missing", "column": "Age"})
    """
    ctx_str = "\n".join(f"  {k}: {v}" for k, v in context.items())
    prompt = f"""
You are an AI data science narrator embedded in a data science platform.
Write a 1-2 sentence plain-English explanation of what just happened.

Event: {event}
Details:
{ctx_str}

Rules:
- Do NOT use bullet points or headings
- Be specific about the column/model names from the context
- Explain WHY this step matters for the analysis
- Write as if explaining to a junior analyst
"""
    return _call(prompt, fallback=f"{event}: {context}")


# ── Agent 5: Hypothesis Agent ─────────────────────────────────────────────────

def hypothesis_agent(hypothesis: str, insights: list) -> dict:
    """
    HypothesisAgent — Semantically validates a user's hypothesis against
    the machine-generated insights. Returns a verdict dict.
    """
    insights_text = "\n".join(f"- {i}" for i in insights[:20])
    prompt = f"""
You are a critical analyst validating a data hypothesis.

User's Hypothesis:
"{hypothesis}"

Machine-Generated Findings:
{insights_text}

Analyze whether the findings support, contradict, or are inconclusive about the hypothesis.

Respond in this exact JSON format:
{{
  "verdict": "SUPPORTED" | "CONTRADICTED" | "INCONCLUSIVE",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "explanation": "2-3 sentences explaining why",
  "matched_insights": ["quote the specific finding that is most relevant"]
}}

Output ONLY valid JSON, no markdown.
"""
    raw = _call(prompt, fallback="{}")
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        result = __import__("json").loads(raw)
        return result
    except Exception:
        return {
            "verdict": "INCONCLUSIVE",
            "confidence": "LOW",
            "explanation": "Could not evaluate hypothesis automatically.",
            "matched_insights": []
        }


# ── Agent 6: Q&A Agent (with safe code execution) ────────────────────────────

def ask_data_agent(df: pd.DataFrame, user_prompt: str) -> str:
    """
    QAAgent — Answers free-form user questions about the dataset.
    Returns either a plain text answer or a single safe pandas expression.
    """
    prompt = f"""
You are an expert Data Science AI Agent embedded in a data analytics platform.
The user asked: "{user_prompt}"

Dataset context:
{_df_context(df)}

Rules:
1. If the question can be answered by READING the schema or sample rows, answer in plain text.
2. If the question REQUIRES computation (mean, sum, filter, count, groupby etc.), output EXACTLY ONE line of pandas code. Assume the dataframe is named `df`.
3. DO NOT output markdown code blocks. DO NOT output any explanation alongside the code.
4. Never use import, open(), os., sys., or __ in code output.

Example code output: df.groupby('Region')['Revenue'].sum().sort_values(ascending=False)
"""
    return _call(prompt, fallback="Could not process your question.")


def safe_execute(code_str: str, df: pd.DataFrame):
    """
    Safely execute a single pandas expression.
    AST-validated; only `df`, `pd`, `np` are in scope.
    Returns (result, error_message).
    """
    BLOCKED = ["import", "open(", "os.", "sys.", "__", "exec(", "eval(", "subprocess", "shutil"]
    for kw in BLOCKED:
        if kw in code_str:
            return None, f"Blocked: forbidden keyword `{kw}`"
    try:
        tree = ast.parse(code_str, mode="eval")
    except SyntaxError as e:
        return None, f"Syntax error: {e}"

    allowed = {"df", "pd", "np", "len", "sum", "max", "min", "round", "abs", "list", "str", "int", "float"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in allowed:
            return None, f"Blocked: `{node.id}` is not an allowed variable."
    try:
        result = eval(compile(tree, "<agent>", "eval"), {"df": df, "pd": pd, "np": np})
        return result, None
    except Exception as e:
        return None, str(e)


# ── Agent 7: Correction Agent ────────────────────────────────────────────────
def correction_agent(raw_text: str, context: str = "") -> str:
    """
    CorrectionAgent — Fixes transcription errors, grammar, and formatting.
    Especially useful for data science terminology (e.g., 'eggy boost' -> 'XGBoost').
    """
    prompt = f"""
    You are an expert speech-to-text correction agent.
    The following text was transcribed from a voice recording in a data science context.
    
    Context: {context}
    Raw Text: "{raw_text}"
    
    Rules:
    1. Fix spelling, grammar, and punctuation.
    2. Correct data science terminology (e.g., "heteroskedasticity", "XGBoost", "pandas", "impute").
    3. Maintain the user's original intent and tone.
    4. If the text is already perfect, return it as is.
    5. Output ONLY the corrected text. No explanations.
    """
    return _call(prompt, fallback=raw_text)
