"""pages/viz.py — Visualizations Gallery page."""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from visualizer import (histogram, box_plot, violin_plot, bar_chart, pie_chart,
                         correlation_heatmap, scatter_plot, pair_plot, time_series,
                         sunburst_chart, animated_bubble_chart)
from data_miner import compute_correlation

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ Please upload data first."); st.stop()

st.markdown("# 📈 Visualizations Gallery")
st.markdown("Interactive charts — explore your data visually. Flag anything interesting.")

num_cols  = df.select_dtypes(include="number").columns.tolist()
cat_cols  = df.select_dtypes(include=["object","category"]).columns.tolist()
date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()


def add_flag_panel(key_prefix: str, context: str):
    with st.expander("🚩 Flag this chart"):
        desc = st.text_input("What do you see?", key=f"{key_prefix}_desc",
                              placeholder="e.g., 'Bimodal distribution — may indicate two subpopulations'")
        ftype = st.selectbox("Flag type:", ["pattern", "anomaly", "question", "domain knowledge"],
                              key=f"{key_prefix}_type")
        if st.button("🚩 Add Flag", key=f"{key_prefix}_flag"):
            st.session_state["flags"].append({"page": "Visualizations", "context": context,
                                               "description": desc, "type": ftype})
            log(f"Chart flag added: {context} — {ftype}")
            st.success("Flag saved!")


tabs = st.tabs([
    "📊 Distributions", "📦 Box / Violin", "🏷️ Categoricals",
    "🔗 Scatter / Pairs", "🌡️ Heatmap", "⏱️ Time Series",
    "☀️ Hierarchical", "🫧 Multi-Dim"
])

# ── Tab 1: Distributions ─────────────────────────────────────────────
with tabs[0]:
    st.markdown("### Histograms")
    if not num_cols:
        st.info("No numeric columns.")
    else:
        col = st.selectbox("Column:", num_cols, key="hist_col")
        fig = histogram(df, col)
        st.plotly_chart(fig, use_container_width=True)
        add_flag_panel("hist", f"Histogram of {col}")

# ── Tab 2: Box / Violin ───────────────────────────────────────────────
with tabs[1]:
    st.markdown("### Box & Violin Plots")
    if not num_cols:
        st.info("No numeric columns.")
    else:
        col = st.selectbox("Column:", num_cols, key="box_col")
        grp = st.selectbox("Group by (optional):", ["None"] + cat_cols, key="box_grp")
        plot_type = st.radio("Chart type:", ["Box", "Violin"], horizontal=True, key="box_type")
        group_col = None if grp == "None" else grp
        if plot_type == "Box":
            fig = box_plot(df, col, group_col)
        else:
            fig = violin_plot(df, col, group_col)
        st.plotly_chart(fig, use_container_width=True)
        add_flag_panel("box", f"{plot_type} of {col}")

# ── Tab 3: Categoricals ───────────────────────────────────────────────
with tabs[2]:
    st.markdown("### Bar & Pie Charts")
    if not cat_cols:
        st.info("No categorical columns.")
    else:
        col = st.selectbox("Column:", cat_cols, key="cat_col")
        chart_type = st.radio("Type:", ["Bar", "Pie"], horizontal=True, key="cat_type")
        top_n = st.slider("Top N values:", 3, 30, 10, key="cat_topn")
        if chart_type == "Bar":
            fig = bar_chart(df, col, top_n)
        else:
            fig = pie_chart(df, col, top_n)
        st.plotly_chart(fig, use_container_width=True)
        add_flag_panel("cat", f"{chart_type} of {col}")

# ── Tab 4: Scatter / Pairs ────────────────────────────────────────────
with tabs[3]:
    st.markdown("### Scatter Plot & Pair Matrix")
    if len(num_cols) < 2:
        st.info("Need at least 2 numeric columns.")
    else:
        sub_tab_s, sub_tab_p = st.tabs(["Scatter", "Pair Matrix"])
        with sub_tab_s:
            x_col = st.selectbox("X axis:", num_cols, key="scatter_x")
            y_col = st.selectbox("Y axis:", [c for c in num_cols if c != x_col], key="scatter_y")
            color_col = st.selectbox("Color by:", ["None"] + cat_cols, key="scatter_color")
            fig = scatter_plot(df, x_col, y_col, None if color_col == "None" else color_col)
            st.plotly_chart(fig, use_container_width=True)
            add_flag_panel("scatter", f"Scatter {x_col} vs {y_col}")

        with sub_tab_p:
            pair_cols = st.multiselect("Select columns (max 6):", num_cols,
                                        default=num_cols[:min(4, len(num_cols))], key="pair_cols")
            color_col_p = st.selectbox("Color by:", ["None"] + cat_cols, key="pair_color")
            if len(pair_cols) >= 2:
                fig = pair_plot(df, pair_cols, None if color_col_p == "None" else color_col_p)
                st.plotly_chart(fig, use_container_width=True)
                add_flag_panel("pair", f"Pair plot: {', '.join(pair_cols)}")

# ── Tab 5: Heatmap ────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("### Correlation Heatmap")
    if len(num_cols) < 2:
        st.info("Need at least 2 numeric columns for a heatmap.")
    else:
        method = st.radio("Method:", ["pearson", "spearman"], horizontal=True, key="heatmap_method")
        corr = compute_correlation(df, method)
        fig = correlation_heatmap(corr)
        st.plotly_chart(fig, use_container_width=True)
        add_flag_panel("heatmap", "Correlation Heatmap")

# ── Tab 6: Time Series ────────────────────────────────────────────────
with tabs[5]:
    st.markdown("### Time Series")
    if not date_cols and not any(df[c].dtype == object for c in df.columns):
        st.info("No datetime columns detected. Parse a date column first in Wrangling.")
    else:
        all_potential_dates = date_cols + [c for c in df.columns
                                            if "date" in c.lower() or "time" in c.lower()]
        if all_potential_dates and num_cols:
            date_col = st.selectbox("Date column:", all_potential_dates, key="ts_date")
            val_col  = st.selectbox("Value column:", num_cols, key="ts_val")
            try:
                df_ts = df.copy()
                df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce")
                fig = time_series(df_ts, date_col, val_col)
                st.plotly_chart(fig, use_container_width=True)
                add_flag_panel("ts", f"Time series: {val_col} over {date_col}")
            except Exception as e:
                st.error(f"Could not render time series: {e}")
        else:
            st.info("No suitable date + numeric column pair found.")
# 5. Hierarchical (Sunburst)
with tabs[6]:
    st.markdown("### ☀️ Sunburst Hierarchy")
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if len(cat_cols) < 2:
        st.warning("Needs at least 2 categorical columns.")
    else:
        path = st.multiselect("Select hierarchy (order matters):", cat_cols, default=cat_cols[:2])
        val_col = st.selectbox("Size by (numeric):", [None] + num_cols)
        if path and st.button("Generate Sunburst"):
            fig = sunburst_chart(df, path, val_col)
            st.plotly_chart(fig, use_container_width=True)
            if st.button("🚩 Flag Sunburst", key="flag_sun"):
                st.session_state["flagged_charts"].append({"page": "Viz", "title": f"Sunburst: {path}", "fig": fig})
                st.success("Flagged!")

# 6. Multi-Dim (Bubble)
with tabs[7]:
    st.markdown("### 🫧 Bubble Analysis")
    if len(num_cols) < 3:
        st.warning("Needs at least 3 numeric columns (X, Y, Size).")
    else:
        c1, c2 = st.columns(2)
        bx = c1.selectbox("X Axis:", num_cols, index=0)
        by = c2.selectbox("Y Axis:", num_cols, index=1 if len(num_cols)>1 else 0)
        c3, c4 = st.columns(2)
        bs = c3.selectbox("Size Axis:", num_cols, index=2 if len(num_cols)>2 else 0)
        bc = c4.selectbox("Color By:", [None] + cat_cols + num_cols)
        bh = st.selectbox("Hover Name:", [None] + cat_cols)
        
        if st.button("Generate Bubble Chart"):
            fig = animated_bubble_chart(df, bx, by, bs, bc, bh)
            st.plotly_chart(fig, use_container_width=True)
            if st.button("🚩 Flag Bubble", key="flag_bub"):
                st.session_state["flagged_charts"].append({"page": "Viz", "title": "Bubble Chart", "fig": fig})
                st.success("Flagged!")
