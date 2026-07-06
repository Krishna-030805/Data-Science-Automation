"""
insight_goals.py  —  Captures what the user wants to discover and gates all downstream analysis.
"""

import streamlit as st
from config import INSIGHT_GOALS


def render_goals_page():
    """
    Full Streamlit page: user selects insight goals, sets target col,
    writes hypothesis, and confirms the plan.
    """
    st.markdown("## What Do You Want to Find?")
    st.markdown(
        "> Before we run a single analysis, tell us your **intent**. "
        "This shapes everything — which tests run, which models are suggested, "
        "and what the final report focuses on."
    )

    # ── Goal selector ────────────────────────────────────────────────
    st.markdown("### Step 1 — Select Your Insight Goal(s)")
    selected_goals = []
    cols = st.columns(2)
    for i, (goal, desc) in enumerate(INSIGHT_GOALS.items()):
        with cols[i % 2]:
            checked = st.checkbox(f"**{goal}**", help=desc, key=f"goal_{goal}")
            if checked:
                selected_goals.append(goal)
                st.caption(desc)

    if not selected_goals:
        st.info(" Select at least one goal to continue.")
        return

    st.success(f" Selected: {', '.join(selected_goals)}")

    # ── Target variable (only for predictive) ───────────────────────
    target_col = None
    df = st.session_state.get("df")

    needs_target = any("Predictive" in g or "Prescriptive" in g for g in selected_goals)

    if needs_target and df is not None:
        st.markdown("### Step 2 — Choose a Target Column")
        st.markdown(
            "Since you chose **Predictive** or **Prescriptive** analysis, "
            "the system needs to know which column you want to predict or segment by."
        )
        target_col = st.selectbox(
            "Target column (what you want to predict):",
            options=["— select —"] + list(df.columns),
        )
        if target_col == "— select —":
            target_col = None
            st.warning("Please select your target column to proceed.")
        else:
            dtype = df[target_col].dtype
            nuniq = df[target_col].nunique()
            if pd.api.types.is_numeric_dtype(df[target_col]) and nuniq > 10:
                st.info(
                    f" **`{target_col}`** looks **continuous** (numeric, {nuniq} unique values) "
                    "→ we'll suggest **Regression** models."
                )
                st.session_state["ml_task"] = "regression"
            else:
                st.info(
                    f" **`{target_col}`** looks **categorical** ({nuniq} unique values) "
                    "→ we'll suggest **Classification** models."
                )
                st.session_state["ml_task"] = "classification"
    elif not needs_target:
        st.markdown("### Step 2 — Target Column")
        st.info("No target column needed for your selected goal(s).")
        if any("Prescriptive" in g for g in selected_goals):
            st.session_state["ml_task"] = "clustering"
        else:
            st.session_state["ml_task"] = None

    # ── Hypothesis ───────────────────────────────────────────────────
    st.markdown("### Step 3 — Your Hypothesis (Optional but Powerful)")
    st.markdown(
        "Write down what you **expect to find** before seeing results. "
        "The system will compare your hypothesis against the actual findings and highlight "
        "**matches**  and **surprises** ."
    )
    hypothesis = st.text_area(
        "What do you expect to find in this data?",
        placeholder="e.g., 'I think older customers churn more. I expect age to be the top feature.'",
        height=100,
        key="hypothesis_input",
    )

    # ── Domain context ───────────────────────────────────────────────
    st.markdown("### Step 4 — Domain Context (Optional)")
    domain_context = st.text_area(
        "Any domain knowledge about this data we should factor in?",
        placeholder="e.g., 'This is medical data — outliers in blood pressure may be real critical values, not errors.'",
        height=80,
        key="domain_context_input",
    )

    # ── Plan preview ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("###  Here's What the System Will Do")

    plan_items = _generate_plan(selected_goals, target_col)
    for item in plan_items:
        st.markdown(item)

    # ── Confirm ──────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        confirmed = st.button(" Confirm & Start Analysis", type="primary", use_container_width=True)
    with col2:
        st.caption("You can come back and change your goals at any time during the session.")

    if confirmed:
        st.session_state["goals"]           = selected_goals
        st.session_state["target_col"]      = target_col
        st.session_state["hypothesis"]      = hypothesis
        st.session_state["domain_context"]  = domain_context
        st.session_state["goals_confirmed"] = True
        _log_action(f"Insight goals set: {', '.join(selected_goals)}"
                    + (f" | Target: {target_col}" if target_col else ""))
        st.success(" Goals confirmed! Navigate to **Data Mining** to begin analysis.")
        st.balloons()


def _generate_plan(goals: list, target_col) -> list:
    """Generate a bullet-point plan based on selected goals."""
    items = []
    for g in goals:
        if "Descriptive" in g:
            items += [
                " **Descriptive**: Run full column profiling, distribution analysis, value frequencies.",
            ]
        if "Diagnostic" in g:
            items += [
                " **Diagnostic**: Compute correlations, run group comparison tests (ANOVA, t-test), flag root-cause candidates.",
            ]
        if "Predictive" in g:
            col_note = f" predicting **`{target_col}`**" if target_col else ""
            items += [
                f" **Predictive**: Train & evaluate multiple ML models{col_note}. Compare metrics. Show feature importances.",
            ]
        if "Prescriptive" in g:
            items += [
                " **Prescriptive**: Run clustering (KMeans + DBSCAN). Segment data. Surface actionable group profiles.",
            ]
        if "Exploratory" in g:
            items += [
                " **Exploratory**: Full EDA — all stats, all charts. You annotate what you find.",
            ]
        if "Anomaly" in g:
            items += [
                " **Anomaly / QA**: Deep outlier analysis (IQR + Z-score), duplicate detection, schema validation, data quality score.",
            ]

    if not items:
        items = [" All modules will run in general mode."]
    return items


def _log_action(msg: str):
    import datetime
    if "action_log" not in st.session_state:
        st.session_state["action_log"] = []
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state["action_log"].append({"time": ts, "action": msg, "status": "✅"})


def goal_active(goal_key: str) -> bool:
    """Check if a given goal keyword is in the confirmed goals."""
    goals = st.session_state.get("goals", [])
    return any(goal_key.lower() in g.lower() for g in goals)


import pandas as pd
