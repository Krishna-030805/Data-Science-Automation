"""
insight_generator.py  —  Rule-based insight engine.
Generates bullet insights and an executive summary from analysis artifacts.
"""

import os
import pandas as pd
import numpy as np
from config import Z_SCORE_THRESHOLD


def _llm_available() -> bool:
    """Check if Gemini is configured (API key set)."""
    return bool(os.environ.get("GEMINI_API_KEY", ""))


def generate_data_insights(overview: dict, profiling_df: pd.DataFrame) -> list:
    """Insights about data quality and structure."""
    insights = []

    if overview["missing_pct"] > 20:
        insights.append(
            f"🔴 High missingness: {overview['missing_pct']}% of all cells are null. "
            "Imputation strategy is critical before any modelling."
        )
    elif overview["missing_pct"] > 0:
        insights.append(
            f"🟡 The dataset has {overview['missing_pct']}% missing values. "
            "Low enough to handle with mean/median imputation."
        )
    else:
        insights.append("✅ Dataset is complete — no missing values detected.")

    if overview["duplicate_rows"] > 0:
        pct = round(overview["duplicate_rows"] / overview["rows"] * 100, 1)
        insights.append(
            f"⚠️ {overview['duplicate_rows']} duplicate rows ({pct}% of data) found. "
            "Removing them is recommended to prevent model bias."
        )

    # Skewed columns
    if profiling_df is not None and "Skewness" in profiling_df.columns:
        high_skew = profiling_df[profiling_df["Skewness"].abs() > 1]["Column"].tolist()
        if high_skew:
            cols_str = ", ".join(f"`{c}`" for c in high_skew[:5])
            insights.append(
                f"📐 Highly skewed columns (|skew| > 1): {cols_str}. "
                "Log or Box-Cox transformation may improve ML performance."
            )

    return insights


def generate_correlation_insights(corr_matrix: pd.DataFrame, threshold: float = 0.8) -> list:
    """Insights about strong feature correlations."""
    insights = []
    if corr_matrix is None or corr_matrix.empty:
        return insights

    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    strong = [(col, row, upper.loc[row, col])
              for col in upper.columns
              for row in upper.index
              if abs(upper.loc[row, col]) >= threshold]

    if strong:
        for c1, c2, r in strong[:5]:
            direction = "positively" if r > 0 else "negatively"
            insights.append(
                f"🔗 **`{c1}`** and **`{c2}`** are strongly {direction} correlated (r = {r:.2f}). "
                "Consider removing one to reduce multicollinearity."
            )
    else:
        insights.append("✅ No strong multicollinearity detected among numeric features (threshold: r ≥ 0.8).")

    return insights


def generate_outlier_insights(outlier_summary: dict) -> list:
    """Insights from outlier detection."""
    insights = []
    flagged = [(col, info) for col, info in outlier_summary.items() if info["count"] > 0]

    if not flagged:
        insights.append("✅ No significant outliers detected across numeric columns.")
    else:
        total = sum(v["count"] for _, v in flagged)
        insights.append(
            f"🚨 **{len(flagged)} column(s)** contain outliers — "
            f"totaling **{total} rows** flagged. Review before training."
        )
        worst = max(flagged, key=lambda x: x[1]["pct"])
        insights.append(
            f"  ⬆️ Most affected: **`{worst[0]}`** — {worst[1]['count']} outlier rows ({worst[1]['pct']}%)."
        )
    return insights


def generate_ml_insights(results: dict, task: str, best_model: str,
                          feature_imp_df: pd.DataFrame = None) -> list:
    """Insights from ML training results."""
    insights = []
    if not results or best_model == "None":
        return ["⚠️ No ML results available."]

    best = results[best_model]
    if task == "classification":
        insights.append(
            f"🏆 Best model: **{best_model}** with "
            f"F1 = {best.get('F1 (weighted)', 'N/A')}, "
            f"Accuracy = {best.get('Accuracy', 'N/A')}, "
            f"ROC-AUC = {best.get('ROC-AUC', 'N/A')}."
        )
    elif task == "regression":
        insights.append(
            f"🏆 Best model: **{best_model}** with "
            f"R² = {best.get('R²', 'N/A')}, "
            f"RMSE = {best.get('RMSE', 'N/A')}."
        )

    if feature_imp_df is not None and not feature_imp_df.empty:
        top3 = feature_imp_df.head(3)["Feature"].tolist()
        cols_str = ", ".join(f"`{c}`" for c in top3)
        insights.append(
            f"📌 Top predictive features: {cols_str}. "
            "These drive most of the model's decisions."
        )

    # Model spread analysis
    valid = {k: v for k, v in results.items() if not v.get("error")}
    if len(valid) > 1 and task == "classification":
        f1_vals = [v["F1 (weighted)"] for v in valid.values()
                   if isinstance(v.get("F1 (weighted)"), float)]
        if f1_vals:
            spread = round(max(f1_vals) - min(f1_vals), 3)
            if spread < 0.05:
                insights.append("📊 All models perform similarly — the problem may be well-defined or simple.")
            else:
                insights.append(
                    f"📊 Model performance spread is {spread:.3f} — the choice of model matters significantly for this dataset."
                )

    return insights


def generate_hypothesis_verdict(hypothesis: str, insights: list) -> dict:
    """
    Compare user's hypothesis against findings.
    Uses the LLM HypothesisAgent when Gemini API key is set.
    Falls back to a neutral stub when not connected.
    """
    if not hypothesis or not insights:
        return {"matched": [], "not_found": [], "verdict": "No hypothesis or insights to compare."}

    if _llm_available():
        try:
            from llm_engine import hypothesis_agent, setup_gemini
            setup_gemini()
            result = hypothesis_agent(hypothesis, insights)
            # Normalise to the shape the insights.py page expects
            return {
                "matched": result.get("matched_insights", []),
                "not_found": [],
                "verdict": (
                    f"{result.get('verdict', 'INCONCLUSIVE')} "
                    f"({result.get('confidence', 'LOW')} confidence) — "
                    f"{result.get('explanation', '')}"
                ),
            }
        except Exception:
            pass  # fall through to stub

    return {
        "matched": [],
        "not_found": [],
        "verdict": (
            "Hypothesis evaluation requires the AI Agent. "
            "Go to the **AI Agent** page → Hypothesis Validator tab."
        ),
    }


def build_full_insight_list(overview: dict, profiling_df: pd.DataFrame,
                             corr_matrix, outlier_summary: dict,
                             ml_results: dict, task: str, best_model: str,
                             feature_imp_df: pd.DataFrame) -> list:
    """Compile all insights into a single prioritized list."""
    all_insights = []
    all_insights += generate_data_insights(overview, profiling_df)
    all_insights += generate_outlier_insights(outlier_summary or {})
    if corr_matrix is not None:
        all_insights += generate_correlation_insights(corr_matrix)
    if ml_results:
        all_insights += generate_ml_insights(ml_results, task, best_model, feature_imp_df)
    return all_insights
