"""pages/analysis.py — Statistical Analysis page."""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from core.analyzer import (univariate_stats, value_counts_table, test_normality,
                       pearson_test, spearman_test, t_test, anova_test, chi_square_test)
from core.narrator import narrate_analysis
from core.visualizer import histogram, bar_chart
from core.ui_components import saas_kpi_card

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ Please upload data first."); st.stop()

st.markdown("# 📊 Statistical Analysis")
st.markdown("Deep statistical examination of your data — every test result interpreted in plain English.")

num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(include=["object","category"]).columns.tolist()

# ── 1. Univariate Stats ───────────────────────────────────────────────
st.markdown("### 1️⃣ Univariate Statistics")
st.markdown("""
<div class='narrate-box'>
<b>What is this?</b> Per-column descriptive statistics. Skewness > 1 means right-skewed (tail on the right).
Kurtosis > 3 means heavy tails compared to a normal distribution. IQR = Q3 - Q1 = spread of the middle 50%.
</div>
""", unsafe_allow_html=True)
if num_cols:
    stats_df = univariate_stats(df)
    st.dataframe(stats_df, use_container_width=True)
else:
    st.info("No numeric columns available.")

# ── 2. Normality Test ─────────────────────────────────────────────────
if num_cols:
    st.markdown("---")
    st.markdown("### 2️⃣ Normality Test (Shapiro-Wilk)")
    st.markdown("""
    <div class='narrate-box'>
    Tests whether a column follows a normal distribution (bell curve). 
    This matters because many ML models and statistical tests assume normality.
    </div>
    """, unsafe_allow_html=True)
    norm_col = st.selectbox("Select column:", num_cols, key="norm_col")
    if st.button("▶ Run Normality Test", key="run_norm"):
        result = test_normality(df, norm_col)
        st.markdown(f"<div class='narrate-box'>{result['interpretation']}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: saas_kpi_card("Test Statistic", result["statistic"])
        with c2: saas_kpi_card("P-Value", result["p_value"])
        st.plotly_chart(histogram(df, norm_col), use_container_width=True)

# ── 3. Correlation Test ───────────────────────────────────────────────
if len(num_cols) >= 2:
    st.markdown("---")
    st.markdown("### 3️⃣ Bivariate Correlation Test")
    col_a = st.selectbox("Feature A:", num_cols, key="corr_a")
    col_b = st.selectbox("Feature B:", [c for c in num_cols if c != col_a], key="corr_b")
    corr_type = st.radio("Test:", ["Pearson (linear)", "Spearman (rank)"], horizontal=True, key="corr_type")
    if st.button("▶ Run Correlation Test", key="run_corr"):
        result = pearson_test(df, col_a, col_b) if "Pearson" in corr_type else spearman_test(df, col_a, col_b)
        narration = narrate_analysis(result["test"], result)
        st.markdown(f"<div class='narrate-box'>{narration}</div>", unsafe_allow_html=True)

# ── 4. Group Comparison ───────────────────────────────────────────────
if num_cols and cat_cols:
    st.markdown("---")
    st.markdown("### 4️⃣ Group Comparison Test")
    st.markdown("""
    <div class='narrate-box'>
    Compare the mean of a numeric column across different groups. 
    T-test: for 2 groups. ANOVA: for 3+ groups.
    </div>
    """, unsafe_allow_html=True)
    gc_num = st.selectbox("Numeric column:", num_cols, key="gc_num")
    gc_cat = st.selectbox("Group by:", cat_cols, key="gc_cat")
    n_groups = df[gc_cat].nunique()
    test_type = "ANOVA" if n_groups > 2 else "T-Test"
    st.caption(f"Detected {n_groups} groups → will run **{test_type}**")
    if st.button("▶ Run Group Test", key="run_group"):
        result = anova_test(df, gc_num, gc_cat) if n_groups > 2 else t_test(df, gc_num, gc_cat)
        narration = narrate_analysis(result["test"], result)
        st.markdown(f"<div class='narrate-box'>{narration}</div>", unsafe_allow_html=True)

# ── 5. Chi-Squared ────────────────────────────────────────────────────
if len(cat_cols) >= 2:
    st.markdown("---")
    st.markdown("### 5️⃣ Chi-Squared Test (Categorical Association)")
    st.markdown("""
    <div class='narrate-box'>
    Tests whether two categorical columns are statistically independent of each other.
    A significant result means knowing one variable's value helps predict the other.
    </div>
    """, unsafe_allow_html=True)
    chi_a = st.selectbox("Categorical A:", cat_cols, key="chi_a")
    chi_b = st.selectbox("Categorical B:", [c for c in cat_cols if c != chi_a], key="chi_b")
    if chi_b and st.button("▶ Run Chi-Squared Test", key="run_chi"):
        result = chi_square_test(df, chi_a, chi_b)
        narration = narrate_analysis(result["test"], result)
        st.markdown(f"<div class='narrate-box'>{narration}</div>", unsafe_allow_html=True)
        st.markdown("**Contingency Table:**")
        st.dataframe(pd.crosstab(df[chi_a], df[chi_b]), use_container_width=True)

# ── Value Counts ──────────────────────────────────────────────────────
if cat_cols:
    st.markdown("---")
    st.markdown("### 6️⃣ Value Frequency Analysis")
    vc_col = st.selectbox("Select column:", cat_cols, key="vc_col")
    vc_df = value_counts_table(df, vc_col)
    st.dataframe(vc_df, use_container_width=True)
    st.plotly_chart(bar_chart(df, vc_col), use_container_width=True)

# ── Annotation ────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📝 Your Notes & Observations (Analysis)"):
    note = st.text_area("Anything notable from the tests?",
                         placeholder="e.g., 'Age and income are highly correlated — might cause multicollinearity'",
                         key="analysis_note")
    tag = st.selectbox("Tag:", ["suspected error", "interesting pattern",
                                 "need more context", "confirmed valid"], key="analysis_tag")
    if st.button("💾 Save Note", key="save_analysis_note"):
        st.session_state["user_notes"].append({"page": "Analysis", "note": note, "tag": tag})
        log("User note added on Analysis page")
        st.success("Note saved!")
