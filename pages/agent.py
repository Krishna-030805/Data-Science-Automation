"""pages/agent.py — Multi-Agent Workspace for DataSense AI."""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from core.llm_engine import (
    setup_gemini, ask_data_agent, safe_execute,
    profiler_agent, wrangling_agent, ml_strategy_agent,
    hypothesis_agent, narrator_agent
)
from core.data_wrangler import (
    fill_missing, drop_duplicates, drop_columns,
    label_encode, clip_outliers, extract_date_features, clean_text_col
)
from core.narrator import narrate_wrangling_step

if "log" not in dir():
    def log(msg, status="✅"): pass  # noqa

# ── Guard: data required ──────────────────────────────────────────────
df = st.session_state.get("df")
if df is None:
    st.warning("Please upload a dataset first.")
    st.stop()

# ── Guard: init Gemini from server env ────────────────────────────────
import os as _os
_api_key = _os.environ.get("GEMINI_API_KEY", "")
if not _api_key:
    st.error("AI Agents are temporarily unavailable. Please contact support.")
    st.stop()
try:
    setup_gemini(_api_key)
except Exception as e:
    st.error(f"Failed to initialize AI Agents: {e}")
    st.stop()

# ── Page header ───────────────────────────────────────────────────────
st.markdown("# AI Agent Workspace")
st.markdown(
    "Six specialized agents work together to analyse, clean, model, and explain your data. "
    "Each agent is powered by **Gemini 1.5 Flash**."
)

agent_tabs = st.tabs([
    "💬 Data Q&A",
    "🔍 Auto Profiler",
    "🔧 Auto Wrangler",
    "🤖 ML Strategy",
    "🧪 Hypothesis Validator",
    "📝 Narrator",
])


# ════════════════════════════════════════════════════════════════════════
# TAB 1 — Q&A Agent
# ════════════════════════════════════════════════════════════════════════
with agent_tabs[0]:
    st.markdown("### 💬 Ask Anything About Your Data")
    st.markdown("Type a question in plain English. The agent will either answer it directly or run a safe pandas calculation.")

    if "qa_messages" not in st.session_state:
        st.session_state["qa_messages"] = [
            {"role": "assistant", "content": (
                "Hello! Ask me anything about your dataset — e.g.\n\n"
                "- *What is the average salary?*\n"
                "- *Show total revenue by region*\n"
                "- *Which column has the most missing values?*"
            )}
        ]

    for msg in st.session_state["qa_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a question about your data...", key="qa_input"):
        st.chat_message("user").markdown(prompt)
        st.session_state["qa_messages"].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ask_data_agent(df, prompt)
                is_code = (
                    response.strip().startswith("df")
                    and "\n" not in response.strip()
                    and len(response.strip()) < 300
                )
                if is_code:
                    st.markdown(f"**Computing:** `{response.strip()}`")
                    result, err = safe_execute(response.strip(), df)
                    if err:
                        out = f"Couldn't execute: {err}"
                        st.warning(out)
                    else:
                        st.write(result)
                        out = f"Result of `{response.strip()}`:\n```\n{str(result)[:400]}\n```"
                else:
                    st.markdown(response)
                    out = response
                st.session_state["qa_messages"].append({"role": "assistant", "content": out})
                log("AI Agent: Q&A query answered")


# ════════════════════════════════════════════════════════════════════════
# TAB 2 — Profiler Agent
# ════════════════════════════════════════════════════════════════════════
with agent_tabs[1]:
    st.markdown("### 🔍 Autonomous Dataset Profiler")
    st.markdown(
        "The Profiler Agent reads your dataset and writes a full executive summary — "
        "domain, data quality, interesting columns, and suggested ML direction."
    )
    if st.button("Run Auto-Profiler", type="primary", use_container_width=True):
        with st.spinner("Analysing your dataset..."):
            summary = profiler_agent(df)
        st.markdown("---")
        st.markdown(f"<div class='narrate-box'>{summary}</div>", unsafe_allow_html=True)
        st.session_state["all_insights"].append(summary)
        log("AI Agent: Auto-profiler ran")

    st.markdown("---")
    st.caption(f"Dataset: {df.shape[0]:,} rows × {df.shape[1]} columns | Columns: {', '.join(df.columns[:8].tolist())}{'...' if len(df.columns) > 8 else ''}")


# ════════════════════════════════════════════════════════════════════════
# TAB 3 — Auto Wrangler Agent
# ════════════════════════════════════════════════════════════════════════
with agent_tabs[2]:
    st.markdown("###  Natural Language Auto-Wrangler")
    st.markdown(
        "Describe what you want to do with your data in plain English. "
        "The agent will plan the steps and apply them automatically."
    )

    wrangle_instruction = st.text_area(
        "What should the agent do?",
        placeholder=(
            "e.g. 'Fill all missing numeric values with the median, "
            "drop duplicates, and encode all categorical columns'"
        ),
        height=100,
        key="wrangle_instruction"
    )

    if "planned_wrangle_actions" not in st.session_state:
        st.session_state["planned_wrangle_actions"] = None

    if st.button("Plan & Execute", type="primary", use_container_width=True, key="run_wrangle_agent"):
        if not wrangle_instruction.strip():
            st.warning("Please describe what you want to do.")
        else:
            with st.spinner("Planning wrangling steps..."):
                actions = wrangling_agent(df, wrangle_instruction)

            if not actions:
                st.error("The agent could not parse a clear set of actions. Please rephrase your instruction.")
                st.session_state["planned_wrangle_actions"] = None
            else:
                st.session_state["planned_wrangle_actions"] = actions

    if st.session_state["planned_wrangle_actions"]:
        actions = st.session_state["planned_wrangle_actions"]
        st.markdown("**Planned Actions:**")
        for i, a in enumerate(actions, 1):
            col_info = f" → `{a.get('column')}`" if a.get("column") else ""
            st.markdown(f"{i}. `{a['action']}`{col_info}")

        st.markdown("---")
        if st.button("Confirm & Apply All Steps", key="confirm_wrangle"):
            current_df = st.session_state["df"].copy()
            applied = []
            errors = []

            for action in actions:
                act = action.get("action", "")
                col = action.get("column")
                before = current_df.copy()
                try:
                    if act == "fill_missing_mean":
                        cols = [col] if col else current_df.select_dtypes("number").columns.tolist()
                        for c in cols:
                            current_df = fill_missing(current_df, c, "mean")
                    elif act == "fill_missing_median":
                        cols = [col] if col else current_df.select_dtypes("number").columns.tolist()
                        for c in cols:
                            current_df = fill_missing(current_df, c, "median")
                    elif act == "fill_missing_mode":
                        cols = [col] if col else current_df.columns.tolist()
                        for c in cols:
                            current_df = fill_missing(current_df, c, "mode")
                    elif act == "drop_duplicates":
                        current_df = drop_duplicates(current_df)
                    elif act == "label_encode_categoricals":
                        cat = [col] if col else current_df.select_dtypes(["object", "category"]).columns.tolist()
                        if cat:
                            current_df = label_encode(current_df, cat)
                    elif act == "drop_column" and col:
                        current_df = drop_columns(current_df, [col])
                    elif act == "clip_outliers_iqr" and col:
                        current_df = clip_outliers(current_df, col)
                    elif act == "extract_date_features" and col:
                        current_df = extract_date_features(current_df, col)
                    elif act == "clean_text" and col:
                        current_df = clean_text_col(current_df, col)
                    else:
                        errors.append(f"Skipped unknown action: `{act}`")
                        continue

                    msg = narrate_wrangling_step(act, before.shape, current_df.shape)
                    st.session_state["df_stack"].append(before)
                    st.session_state["wrangling_history"].append(f"[AI Agent] {msg}")
                    applied.append(act)
                except Exception as e:
                    errors.append(f"`{act}` failed: {e}")

            st.session_state["df"] = current_df
            if applied:
                st.success(f"Applied {len(applied)} steps: {', '.join(applied)}")
            if errors:
                for err in errors:
                    st.warning(err)
            log(f"AI WranglingAgent applied {len(applied)} steps")
            st.session_state["planned_wrangle_actions"] = None
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
# TAB 4 — ML Strategy Agent
# ════════════════════════════════════════════════════════════════════════
with agent_tabs[3]:
    st.markdown("###  ML Strategy Advisor")
    st.markdown("The agent analyses your dataset characteristics and recommends the best models to train — and explains why.")

    target_col = st.session_state.get("target_col")
    ml_task = st.session_state.get("ml_task")

    if not target_col:
        st.warning("No target column set yet. Go to **Insight Goals** to set one first.")
    else:
        st.markdown(f"**Target:** `{target_col}` | **Task:** `{ml_task or 'Not determined yet'}`")
        if st.button("Get ML Strategy Recommendation", type="primary", use_container_width=True):
            with st.spinner("Analysing dataset for ML strategy..."):
                rec = ml_strategy_agent(df, target_col, ml_task or "unknown")
            st.markdown("---")
            st.markdown(f"<div class='narrate-box'>{rec}</div>", unsafe_allow_html=True)
            log("AI Agent: ML strategy generated")


# ════════════════════════════════════════════════════════════════════════
# TAB 5 — Hypothesis Agent
# ════════════════════════════════════════════════════════════════════════
with agent_tabs[4]:
    st.markdown("###  Hypothesis Validator")
    st.markdown(
        "Write your hypothesis and the agent will semantically compare it against "
        "all machine-generated findings to give a verdict."
    )

    hypothesis = st.session_state.get("hypothesis", "")
    hyp_input = st.text_area(
        "Your Hypothesis:",
        value=hypothesis,
        placeholder="e.g. 'Older customers are more likely to churn than younger ones'",
        height=100,
        key="hypothesis_agent_input"
    )

    all_insights = st.session_state.get("all_insights", [])
    if not all_insights:
        st.info("No machine-generated insights available yet. Run **Data Mining** and **ML Models** first.")
    elif st.button("Validate Hypothesis", type="primary", use_container_width=True):
        with st.spinner("Comparing hypothesis against findings..."):
            verdict = hypothesis_agent(hyp_input, all_insights)

        v = verdict.get("verdict", "INCONCLUSIVE")
        conf = verdict.get("confidence", "LOW")
        explanation = verdict.get("explanation", "")
        matched = verdict.get("matched_insights", [])

        color = {"SUPPORTED": "#43B89C", "CONTRADICTED": "#FF6584", "INCONCLUSIVE": "#FFD166"}.get(v, "#aaa")

        st.markdown(
            f"<div class='narrate-box'>"
            f"<span style='color:{color};font-weight:700;font-size:1.1rem'>{v}</span> "
            f"<span style='color:#888;font-size:0.85rem'>({conf} confidence)</span><br><br>"
            f"{explanation}"
            f"</div>",
            unsafe_allow_html=True
        )
        if matched:
            st.markdown("**Most relevant finding:**")
            for m in matched:
                st.markdown(f"> {m}")
        log(f"AI Agent: Hypothesis validated — {v}")


# ════════════════════════════════════════════════════════════════════════
# TAB 6 — Narrator Agent
# ════════════════════════════════════════════════════════════════════════
with agent_tabs[5]:
    st.markdown("###  Live AI Narrator")
    st.markdown(
        "Describe any event or finding and the Narrator Agent will write "
        "a clear, context-aware explanation for it in plain English."
    )

    c1, c2 = st.columns(2)
    event_label = c1.selectbox(
        "Event type:",
        ["wrangling_step", "outlier_detected", "model_trained", "feature_important",
         "correlation_found", "missing_data_handled", "custom"],
        key="narrator_event"
    )
    if event_label == "custom":
        event_label = st.text_input("Custom event name:", key="narrator_custom_event")

    context_raw = c2.text_area(
        "Context (key: value pairs):",
        placeholder="action: Fill Missing\ncolumn: Age\nstrategy: median",
        height=120,
        key="narrator_context"
    )

    if st.button("Generate Narration", type="primary", use_container_width=True):
        # Parse context_raw into dict
        ctx = {}
        for line in context_raw.strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                ctx[k.strip()] = v.strip()

        if not ctx:
            st.warning("Please add at least one context key:value pair.")
        else:
            with st.spinner("Generating narration..."):
                narration = narrator_agent(event_label, ctx)
            st.markdown("---")
            st.markdown(f"<div class='narrate-box'>{narration}</div>", unsafe_allow_html=True)
            log("AI Agent: Narrator generated explanation")
