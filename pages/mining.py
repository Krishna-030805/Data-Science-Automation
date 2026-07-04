"""pages/mining.py — Data Mining & Profiling page."""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from core.data_miner import (profile_columns, detect_outliers_iqr, detect_outliers_zscore,
                         compute_correlation, top_correlations, quality_score, get_outlier_rows)
from core.narrator import narrate_columns, narrate_outliers
from core.visualizer import correlation_heatmap, box_plot, histogram
from core.ui_components import saas_radial_gauge, correlation_physics_universe

if "log" not in dir():
    def log(msg, status="✅"): pass  # noqa

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ Please upload data first."); st.stop()

st.markdown("# 🔍 Data Mining & Profiling")
st.markdown("Automated deep-dive into every column: distributions, nulls, outliers, and correlations.")

# ── Quality score ─────────────────────────────────────────────────────
qs = quality_score(df)
col1, col2 = st.columns([1, 3])
with col1:
    saas_radial_gauge(qs['score'], label="Data Quality Score", details=qs.get('details', []))
with col2:
    st.markdown("**Quality Deductions:**")
    if qs["details"]:
        for d in qs["details"]:
            st.markdown(f"- {d}")
    else:
        st.markdown("✅ No deductions — perfect score!")

# ── Column profiling ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Column Profiling")
profiling_df = profile_columns(df)
st.session_state["profiling_df"] = profiling_df

col_info = profiling_df.set_index("Column").to_dict(orient="index")
narration = narrate_columns({c: {"null_pct": v["Null %"], "nunique": v["Unique"]}
                              for c, v in col_info.items()})
st.markdown(f"<div class='narrate-box'>{narration}</div>", unsafe_allow_html=True)
st.dataframe(profiling_df, use_container_width=True)

# ── AI Auto-Summary (ProfilerAgent) ──────────────────────────────────
import os as _mining_os
if _mining_os.environ.get("GEMINI_API_KEY"):
    st.markdown("---")
    st.markdown("### 🧠 AI Dataset Summary")
    _cached_summary = st.session_state.get("ai_profile_summary")
    if _cached_summary:
        st.markdown(f"<div class='narrate-box'>{_cached_summary}</div>", unsafe_allow_html=True)
        if st.button("🔄 Re-run AI Profiler", key="rerun_profiler"):
            st.session_state.pop("ai_profile_summary", None)
            st.rerun()
    else:
        if st.button("🧠 Generate AI Summary", type="primary", key="run_profiler"):
            with st.spinner("AI is analysing your dataset..."):
                try:
                    from core.llm_engine import profiler_agent, setup_gemini
                    setup_gemini()
                    summary = profiler_agent(df)
                    st.session_state["ai_profile_summary"] = summary
                    st.session_state["all_insights"].append(summary)
                    log("AI ProfilerAgent: auto-summary generated")
                    st.rerun()
                except Exception as e:
                    st.warning(f"AI profiler unavailable: {e}")

# ── Outlier detection ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🚨 Outlier Detection")

method = st.radio("Detection method:", ["IQR (Interquartile Range)", "Z-Score"], horizontal=True)
outlier_summary = detect_outliers_iqr(df) if "IQR" in method else detect_outliers_zscore(df)
st.session_state["outlier_summary"] = outlier_summary

narration_out = narrate_outliers(outlier_summary)
st.markdown(f"<div class='narrate-box'>{narration_out}</div>", unsafe_allow_html=True)

if outlier_summary:
    sel_col = st.selectbox("Inspect outliers for column:", list(outlier_summary.keys()))
    if sel_col:
        st.markdown(f"**Outlier rows in `{sel_col}`:**")
        out_rows = get_outlier_rows(df, sel_col)
        st.dataframe(out_rows, use_container_width=True)
        st.plotly_chart(box_plot(df, sel_col), use_container_width=True)

        # Flag outliers
        with st.expander("🚩 Flag these outliers"):
            flag_desc = st.text_input("Describe what you observe:", key="flag_outlier_desc")
            flag_type = st.selectbox("Flag type:", ["anomaly", "pattern", "question", "domain knowledge"],
                                      key="flag_outlier_type")
            if st.button("🚩 Add Flag", key="add_outlier_flag"):
                st.session_state["flags"].append({
                    "page": "Data Mining", "column": sel_col,
                    "description": flag_desc, "type": flag_type
                })
                log(f"Flag added on '{sel_col}' outliers: {flag_type}")
                st.success("Flag saved!")

# ── Correlation ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔗 Correlation Analysis")
corr_method = st.selectbox("Correlation method:", ["pearson", "spearman"])
corr = compute_correlation(df, method=corr_method)
st.session_state["corr_matrix"] = corr

corr_tab1, corr_tab2 = st.tabs(["🧠 Heatmap Matrix", "🌌 Dynamic Physics Universe"])

with corr_tab1:
    if not corr.empty:
        st.plotly_chart(correlation_heatmap(corr), use_container_width=True)
        st.markdown("**Top Correlated Pairs:**")
        st.dataframe(top_correlations(corr), use_container_width=True)
    else:
        st.info("No numeric columns available for correlation.")

with corr_tab2:
    st.markdown(
        "<div class='narrate-box'>"
        "🌌 Drag the glowing nodes to feel how correlated columns pull towards each other. "
        "Green links = positive correlation, red = negative. Spring tension ∝ |correlation|."
        "</div>",
        unsafe_allow_html=True)
    correlation_physics_universe(df)

# ── User annotation ───────────────────────────────────────────────────
st.markdown("---")
with st.expander("📝 Your Notes & Observations (Mining)"):
    note = st.text_area("What patterns do you notice here?",
                         placeholder="e.g., 'Column X has suspiciously round numbers — might be imputed data'",
                         key="mining_note")
    tag = st.selectbox("Tag:", ["suspected error", "interesting pattern",
                                 "need more context", "confirmed valid"], key="mining_tag")
    if st.button("💾 Save Note", key="save_mining_note"):
        st.session_state["user_notes"].append({"page": "Data Mining", "note": note, "tag": tag})
        log("User note added on Data Mining page")
        st.success("Note saved!")

log("Data Mining completed")
