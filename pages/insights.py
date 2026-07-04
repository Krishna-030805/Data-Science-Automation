"""pages/insights.py — Session Report & Insights page."""

import streamlit as st
import pandas as pd
import datetime
import io
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from core.insight_generator import build_full_insight_list, generate_hypothesis_verdict
from core.narrator import narrate_insights
from core.ui_components import saas_kpi_card

if "log" not in dir():
    def log(msg, status="✅"): pass  # noqa

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ Please upload data first."); st.stop()

st.markdown("# 💡 Insights & Session Report")
st.markdown("The complete picture — automated findings + your human observations, all in one place.")

# ── Generate insights ─────────────────────────────────────────────────
overview      = st.session_state.get("overview", {})
profiling_df  = st.session_state.get("profiling_df")
corr_matrix   = st.session_state.get("corr_matrix")
outlier_sum   = st.session_state.get("outlier_summary", {})
ml_results    = st.session_state.get("ml_results")
best_model    = st.session_state.get("best_model")
ml_task       = st.session_state.get("ml_task")
feat_imp      = st.session_state.get("feature_imp_df")
hypothesis    = st.session_state.get("hypothesis", "")
goals         = st.session_state.get("goals", [])
user_notes    = st.session_state.get("user_notes", [])
flags         = st.session_state.get("flags", [])

if st.button("🔄 Regenerate Insights", type="primary", key="regen_insights"):
    all_insights = build_full_insight_list(
        overview, profiling_df, corr_matrix, outlier_sum,
        ml_results, ml_task or "", best_model or "None", feat_imp
    )
    st.session_state["all_insights"] = all_insights
    log("Insights regenerated")
    st.rerun()

all_insights = st.session_state.get("all_insights", [])
if not all_insights:
    all_insights = build_full_insight_list(
        overview, profiling_df, corr_matrix, outlier_sum,
        ml_results, ml_task or "", best_model or "None", feat_imp
    )
    st.session_state["all_insights"] = all_insights

# ── Executive Summary ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📝 Executive Summary")
summary = narrate_insights(all_insights)
st.markdown(f"<div class='narrate-box'>{summary}</div>", unsafe_allow_html=True)

# ── Key Metrics ─────────────────────────────────────────────────────
if overview:
    c1, c2, c3, c4 = st.columns(4)
    with c1: saas_kpi_card("Rows",       overview.get('rows', 0),          delay=0)
    with c2: saas_kpi_card("Columns",    overview.get("columns", 0),       delay=120)
    with c3: saas_kpi_card("Missing %",  overview.get('missing_pct', 0),   delay=240, suffix="%")
    with c4: saas_kpi_card("Best Model", best_model or "N/A",   delay=360)

# ── Automated Insights ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🤖 Automated Findings")
if all_insights:
    for insight in all_insights:
        st.markdown(f"<div class='ds-card'>{insight}</div>", unsafe_allow_html=True)
else:
    st.info("No insights yet. Run Data Mining and ML Models first.")

# ── Hypothesis Verdict ────────────────────────────────────────────────
if hypothesis:
    st.markdown("---")
    st.markdown("### 🧪 Your Hypothesis vs. Findings")
    st.markdown(f"**You wrote:** *\"{hypothesis}\"*")
    verdict = generate_hypothesis_verdict(hypothesis, all_insights)
    st.markdown(f"<div class='narrate-box'><b>Verdict:</b> {verdict['verdict']}</div>",
                unsafe_allow_html=True)
    if verdict["matched"]:
        st.markdown("**✅ Keywords found in findings:** " +
                    ", ".join(f"`{w}`" for w in verdict["matched"]))
    if verdict["not_found"]:
        st.markdown("**🔴 Keywords NOT found:** " +
                    ", ".join(f"`{w}`" for w in verdict["not_found"]) +
                    " — these aspects may need further investigation.")
else:
    st.markdown("---")
    st.info("💡 No hypothesis was set. Go to **🎯 Insight Goals** to add one before running analysis.")

# ── Human Flags ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🚩 Your Human Observations & Flags")
if flags:
    for f in flags:
        badge_color = {"anomaly": "#FF6584", "pattern": "#43B89C",
                       "question": "#FFD166", "domain knowledge": "#6C63FF"}.get(f["type"], "#aaa")
        st.markdown(
            f"<div class='flag-box'>"
            f"<span style='color:{badge_color};font-weight:700'>[{f['type'].upper()}]</span> "
            f"<b>Page:</b> {f.get('page','?')} | <b>Context:</b> {f.get('context', f.get('column','?'))}<br>"
            f"{f['description']}"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    st.info("No flags added yet. Use the 🚩 flag buttons on any chart or outlier table.")

# ── User Annotations ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📝 Your Annotations & Notes")
if user_notes:
    for note in user_notes:
        tag_color = {"suspected error": "#FF6584", "interesting pattern": "#43B89C",
                     "need more context": "#FFD166", "confirmed valid": "#6C63FF"}.get(note["tag"], "#aaa")
        st.markdown(
            f"<div class='human-note'>"
            f"<span style='color:{tag_color};font-weight:700'>[{note['tag']}]</span> "
            f"<b>{note['page']}</b>: {note['note']}"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    st.info("No annotations yet. Use the 📝 panels on each page to add your observations.")

# ── Domain Context ────────────────────────────────────────────────────
domain_context = st.session_state.get("domain_context", "")
if domain_context:
    st.markdown("---")
    st.markdown("### 🌐 Domain Context You Provided")
    st.markdown(f"<div class='narrate-box'>{domain_context}</div>", unsafe_allow_html=True)

# ── Wrangling History ─────────────────────────────────────────────────
wrangling_history = st.session_state.get("wrangling_history", [])
if wrangling_history:
    st.markdown("---")
    with st.expander("🔧 Wrangling Steps Applied"):
        for i, step in enumerate(wrangling_history, 1):
            st.markdown(f"**Step {i}:** {step}")

# ── Goals Summary ─────────────────────────────────────────────────────
if goals:
    st.markdown("---")
    st.markdown("### 🎯 Insight Goals Pursued")
    for g in goals:
        st.markdown(f"<span class='badge'>{g}</span>", unsafe_allow_html=True)

st.markdown("---")

# ── Export Options ────────────────────────────────────────────────────
st.markdown("## 📥 Export & Share")
col1, col2 = st.columns(2)

# 1. CSV Data Export
with col1:
    st.markdown("### 📊 Structured Data (CSV)")
    st.markdown("Export all flags, notes, and machine-generated insights as a CSV.")
    
    export_data = []
    # Machine insights
    for ins in all_insights:
        export_data.append({"Type": "Machine Insight", "Content": str(ins)})
    # User flags
    for flag in flags:
        export_data.append({"Type": "User Flag", "Source": flag.get("page", "N/A"), "Content": flag.get("description", ""), "Tag": flag.get("type", "")})
    # User notes
    for note in user_notes:
        export_data.append({"Type": "User Note", "Source": note.get("page", "N/A"), "Content": note.get("note", ""), "Tag": note.get("tag", "")})
        
    if export_data:
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Insights CSV", data=csv, file_name="datasense_insights.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("No insights or flags to export yet.")

# 2. HTML Report
with col2:
    st.markdown("### 📄 Professional Report (HTML)")
    st.markdown("Generate a multi-section report including all flagged findings.")
    
    def build_fancy_report():
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        rows_info = overview.get("rows", "?")
        cols_info = overview.get("columns", "?")
        
        insights_html = "".join(f"<div class='insight-box'>{i}</div>" for i in all_insights)
        flags_html    = "".join(
            f"<div class='insight-box'><span class='flag-tag'>{f.get('type','?').upper()}</span> <b>{f.get('page','?')}</b> — {f.get('description','')}</div>"
            for f in flags
        ) or "<p>No flags.</p>"
        
        # ML metrics table
        metrics_html = "<table><tr><th>Metric</th><th>Value</th></tr>"
        best_data = ml_results.get(best_model, {}) if ml_results else {}
        for k, v in best_data.items():
            if isinstance(v, (float, int, str)) and k != "model":
                metrics_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
        metrics_html += "</table>"

        return f"""
        <html>
        <head>
            <title>DataSense AI Report</title>
            <style>
                body {{ font-family: -apple-system, system-ui, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 20px; }}
                h1 {{ color: #6C63FF; border-bottom: 2px solid #6C63FF; padding-bottom: 5px; }}
                h2 {{ color: #1a1d27; margin-top: 30px; border-left: 5px solid #6C63FF; padding-left: 10px; }}
                .meta {{ color: #666; font-size: 0.85rem; margin-bottom: 30px; }}
                .insight-box {{ background: #f9f9fb; border: 1px solid #eee; border-radius: 6px; padding: 12px; margin-bottom: 8px; }}
                .flag-tag {{ background: #6C63FF; color: white; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; font-weight: bold; margin-right: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background: #f4f4f4; }}
                .footer {{ margin-top: 50px; text-align: center; color: #999; font-size: 0.75rem; }}
            </style>
        </head>
        <body>
            <h1>🧠 DataSense AI — Executive Report</h1>
            <div class="meta">Generated: {now} | Dataset: {rows_info} x {cols_info}</div>
            
            <h2>🎯 Goals</h2>
            <ul>{''.join([f"<li>{g}</li>" for g in goals])}</ul>

            <h2>🤖 Machine Insights</h2>
            {insights_html}

            <h2>🚩 Human Observations</h2>
            {flags_html}

            <h2>🤖 Model: {best_model}</h2>
            {metrics_html}

            <div class="footer">Created with DataSense AI</div>
        </body>
        </html>
        """

    if st.button("📝 Generate HTML Report", type="primary", use_container_width=True):
        html = build_fancy_report()
        st.download_button("💾 Save HTML Report", data=html, file_name="datasense_report.html", mime="text/html", use_container_width=True)

st.markdown("---")

# 3. Share Summary
st.markdown("## 🔗 Quick Copy Summary")
summary_txt = f"DataSense AI Report Summary\n{'='*30}\n"
summary_txt += f"Goal: {', '.join(goals)}\n"
summary_txt += f"Best Model: {best_model or 'N/A'}\n\n"
summary_txt += "Key Insights:\n"
for ins in all_insights[:3]:
    summary_txt += f"- {ins}\n"

st.text_area("Copy and share this summary:", summary_txt, height=150)

log("Insights page viewed — session report ready")
