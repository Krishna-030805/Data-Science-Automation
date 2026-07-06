"""
narrator.py  —  AutoNarrate engine: plain-English explanations for every automated step.
"""

import pandas as pd
from config import Z_SCORE_THRESHOLD, IQR_MULTIPLIER


def narrate_dataset(overview: dict) -> str:
    """Generate a plain-English summary of the uploaded dataset."""
    r, c = overview["rows"], overview["columns"]
    mp   = overview["missing_pct"]
    dup  = overview["duplicate_rows"]
    mem  = overview["memory_mb"]

    size_label = "small" if r < 1000 else "medium-sized" if r < 50000 else "large"

    lines = [
        f" **What we found:** Your dataset has **{r:,} rows** and **{c} columns** — "
        f"that's a {size_label} dataset ({mem} MB in memory).",

        f" Numeric columns: **{overview['numeric_cols']}** &nbsp;|&nbsp; "
        f" Categorical: **{overview['cat_cols']}** &nbsp;|&nbsp; "
        f" Datetime: **{overview['date_cols']}**",
    ]

    if mp == 0:
        lines.append(" **No missing values** — the dataset appears complete.")
    elif mp < 5:
        lines.append(f" **{mp}% missing data** — low, but worth checking which columns are affected.")
    elif mp < 20:
        lines.append(f" **{mp}% missing data** — moderate. Imputation or column dropping may be needed before ML.")
    else:
        lines.append(f" **{mp}% missing data** — high. ML models will struggle without careful imputation strategy.")

    if dup > 0:
        lines.append(f" **{dup} duplicate rows** detected — these can bias model training if not removed.")
    else:
        lines.append(" **No duplicate rows** found.")

    return "\n\n".join(lines)


def narrate_columns(col_info: dict) -> str:
    """Explain what column profiling found."""
    high_null = [c for c, v in col_info.items() if v.get("null_pct", 0) > 30]
    low_var   = [c for c, v in col_info.items() if v.get("nunique", 99) <= 1]

    lines = []
    if high_null:
        cols_str = ", ".join(f"`{c}`" for c in high_null[:5])
        lines.append(f" **High-null columns** (>30% missing): {cols_str} — consider dropping or imputing these carefully.")
    if low_var:
        cols_str = ", ".join(f"`{c}`" for c in low_var)
        lines.append(f" **Near-zero variance columns**: {cols_str} — these add little predictive value and can usually be dropped.")
    if not lines:
        lines.append(" **All columns look well-populated with sufficient variance.")
    return "\n\n".join(lines)


def narrate_outliers(outlier_summary: dict) -> str:
    """Explain what outlier detection found."""
    if not outlier_summary:
        return " No significant outliers detected across numeric columns."

    flagged = [(col, info) for col, info in outlier_summary.items() if info["count"] > 0]
    if not flagged:
        return " No significant outliers detected across numeric columns."

    lines = [
        f" **Outlier Detection** (IQR × {IQR_MULTIPLIER} + Z-score > {Z_SCORE_THRESHOLD}): "
        f"Found **{len(flagged)} column(s)** with notable outliers."
    ]
    for col, info in flagged[:5]:
        if "min" in info:
            lines.append(
                f"  • **`{col}`**: {info['count']} outlier row(s) | "
                f"min={info['min']:.2f}, max={info['max']:.2f}, threshold=[{info['lower']:.2f}, {info['upper']:.2f}]"
            )
        else:
            lines.append(f"  • **`{col}`**: {info['count']} outlier row(s) ({info.get('pct', 0)}%)")
    lines.append(
        "\n **What to do?** Outliers aren't always errors — they may represent real extreme events. "
        "Review them in context before removing. You can flag them here and note your observations."
    )
    return "\n\n".join(lines)


def narrate_model_choice(task: str, models: list, df_shape: tuple, target_col: str = None) -> str:
    """Explain why these models were selected for this task and data."""
    from config import MODEL_REASONS, MODEL_WARNINGS

    rows, cols = df_shape
    size_label = "small" if rows < 1000 else "medium" if rows < 50000 else "large"

    lines = [
        f" **Task Detected: `{task.upper()}`**",
        f"Your data has {rows:,} rows ({size_label} dataset) and {cols} features. "
        + (f"Target column: **`{target_col}`**." if target_col else ""),
        "",
        "**Why these models?**"
    ]
    for m in models:
        reason = MODEL_REASONS.get(m, "Standard model for this task type.")
        warning = MODEL_WARNINGS.get(m, "")
        badge = f"  • **{m}**: {reason}"
        if warning:
            badge += f"\n     *Note: {warning}*"
        lines.append(badge)

    lines.append(
        "\n **Your turn:** You can remove models you don't want, or add others. "
        "The system will train all selected models and compare them side by side."
    )
    return "\n\n".join(lines)


def narrate_results(metrics_df: pd.DataFrame, task: str, best_model: str) -> str:
    """Explain what the ML results mean in plain English."""
    lines = [
        f" **Best Model: `{best_model}`**",
    ]

    if task == "classification":
        lines.append(
            "We compared models using **F1-score** (balances precision & recall) and **ROC-AUC** "
            "(ability to distinguish classes). A score of 1.0 is perfect; 0.5 is random guessing."
        )
    elif task == "regression":
        lines.append(
            "We compared models using **R²** (proportion of variance explained — higher is better) "
            "and **RMSE** (average prediction error in the target's units — lower is better)."
        )
    elif task == "clustering":
        lines.append(
            "We used **Silhouette Score** (how well-separated clusters are — ranges from -1 to 1, "
            "higher is better) to evaluate cluster quality."
        )

    lines.append(
        " *Tip: The best metric depends on your goal. For imbalanced classes, F1 > Accuracy. "
        "For regression, R² tells you explanatory power while RMSE tells you practical error.*"
    )
    return "\n\n".join(lines)


def narrate_wrangling_step(action: str, before_shape: tuple, after_shape: tuple, detail: str = "") -> str:
    """Explain what a wrangling step did."""
    rows_removed = before_shape[0] - after_shape[0]
    cols_removed = before_shape[1] - after_shape[1]

    msg = f" **{action}** applied. "
    if rows_removed > 0:
        msg += f"Removed **{rows_removed} rows**. "
    if cols_removed > 0:
        msg += f"Removed **{cols_removed} columns**. "
    if rows_removed == 0 and cols_removed == 0:
        msg += "Shape unchanged (transformation was in-place). "
    if detail:
        msg += f"\n> {detail}"
    return msg


def narrate_analysis(test_name: str, result: dict) -> str:
    """Explain a statistical test result in plain English."""
    pval = result.get("p_value")
    stat = result.get("statistic")
    alpha = 0.05

    base = f"**{test_name}**: statistic = `{stat:.4f}`, p-value = `{pval:.4f}`  \n"
    if pval is not None:
        if pval < alpha:
            interpretation = (
                f" **Statistically significant** (p < {alpha}): "
                "There is strong evidence that this effect is real, not due to chance."
            )
        else:
            interpretation = (
                f" **Not statistically significant** (p ≥ {alpha}): "
                "Insufficient evidence to conclude a meaningful effect. "
                "This could be a real null result, or the sample may be too small."
            )
        return base + interpretation
    return base + "No p-value available for this test."


def narrate_insights(insights: list) -> str:
    """Convert a list of insight dicts into a human executive summary paragraph."""
    if not insights:
        return "No automatic insights generated. The data may need more cleaning or a clearer goal."

    bullets = "\n".join(f"• {i}" for i in insights)
    summary = (
        "**Executive Summary**\n\n"
        "The automated analysis has completed its full pipeline. "
        f"Here are the key findings from your data:\n\n{bullets}\n\n"
        "These are machine-generated observations. "
        "Your human annotations and flags (shown below) may reveal additional context "
        "that the algorithm cannot capture."
    )
    return summary
