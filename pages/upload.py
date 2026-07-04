"""pages/upload.py — Data upload, merge, preview, and AutoNarrate."""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from core.data_loader import load_multiple, merge_concat, merge_join, get_overview, infer_column_roles
from core.narrator import narrate_dataset
from core.ui_components import saas_kpi_card

def _log(msg): log(msg) if "log" in dir() else None  # noqa

st.markdown("# 📂 Data Upload")
st.markdown("Upload one or more files. The system will auto-detect formats and let you merge them.")

# ── Upload ────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drop files here (CSV, Excel, JSON, Parquet)",
    type=["csv", "xlsx", "xls", "json", "parquet"],
    accept_multiple_files=True,
)

if not uploaded:
    if st.session_state["df"] is not None:
        st.info("ℹ️ Data already loaded from a previous upload. Scroll down to preview.")
    else:
        st.info("👆 Upload at least one file to begin.")

if uploaded:
    dfs_named, errors = load_multiple(uploaded)

    if errors:
        for name, err in errors:
            st.error(f"❌ Could not load **{name}**: {err}")

    if not dfs_named:
        st.stop()

    file_names = [n for n, _ in dfs_named]
    dfs        = [d for _, d in dfs_named]

    st.success(f"✅ Loaded **{len(dfs)}** file(s): {', '.join(file_names)}")

    # ── Merge strategy ────────────────────────────────────────────────
    if len(dfs) > 1:
        st.markdown("### 🔀 Merge Strategy")
        st.markdown("""
        <div class='narrate-box'>
        <b>How should we combine these files?</b><br>
        • <b>Stack (Union)</b>: Place rows on top of each other — use when files have the same schema.<br>
        • <b>Join on Key</b>: Match rows by a shared ID column — use when files share a common identifier like <code>user_id</code>.
        </div>
        """, unsafe_allow_html=True)

        merge_strategy = st.radio("Choose merge strategy:", ["Stack (Union)", "Join on Key"], horizontal=True)

        if merge_strategy == "Join on Key":
            all_cols = list(set.intersection(*[set(d.columns) for d in dfs]))
            if all_cols:
                key_col = st.selectbox("Key column (shared column):", all_cols)
                how = st.selectbox("Join type:", ["inner", "left", "outer"])
                try:
                    df = merge_join(dfs, key_col, how)
                    st.success(f"✅ Joined on `{key_col}` ({how}) → {df.shape[0]:,} rows × {df.shape[1]} cols")
                except Exception as e:
                    st.error(f"Join failed: {e}")
                    df = dfs[0]
            else:
                st.warning("No common columns found. Falling back to Stack (Union).")
                df = merge_concat(dfs)
        else:
            df = merge_concat(dfs)
            st.success(f"✅ Stacked → {df.shape[0]:,} rows × {df.shape[1]} cols")
    else:
        df = dfs[0]

    # ── Save ──────────────────────────────────────────────────────────
    st.session_state["df"]          = df
    st.session_state["df_original"] = df.copy()
    st.session_state["file_names"]  = file_names
    overview = get_overview(df)
    st.session_state["overview"]    = overview
    log(f"Loaded {', '.join(file_names)} → {df.shape[0]}×{df.shape[1]}")

    # ── AutoNarrate ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🤖 AutoNarrate — What We Found")
    narrative = narrate_dataset(overview)
    st.markdown(f"<div class='narrate-box'>{narrative}</div>", unsafe_allow_html=True)

    # ── Metrics row ───────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: saas_kpi_card("Rows",       overview['rows'],              delay=0)
    with c2: saas_kpi_card("Columns",    overview["columns"],           delay=120)
    with c3: saas_kpi_card("Missing %",  overview['missing_pct'],       delay=240, suffix="%")
    with c4: saas_kpi_card("Duplicates", overview["duplicate_rows"],    delay=360)
    with c5: saas_kpi_card("Memory MB",  overview['memory_mb'],         delay=480)

    # ── Column type badges ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏷️ Column Roles")
    roles = infer_column_roles(df)
    badges_html = " ".join(
        f"<span class='badge'>{role} {col}</span>"
        for col, role in roles.items()
    )
    st.markdown(badges_html, unsafe_allow_html=True)

    # ── Preview ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 👁️ Data Preview")
    n_rows = st.slider("Show rows:", 5, min(200, len(df)), 10)
    st.dataframe(df.head(n_rows), use_container_width=True)

    # ── Per-file info ─────────────────────────────────────────────────
    if len(dfs) > 1:
        with st.expander("📄 Individual File Shapes"):
            for name, d in dfs_named:
                st.markdown(f"**{name}**: {d.shape[0]:,} rows × {d.shape[1]} cols")

    # ── User annotation ───────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📝 Your Notes & Observations about this dataset"):
        note = st.text_area("What do you notice at first glance?",
                            placeholder="e.g., 'The date column looks inconsistently formatted'",
                            key="upload_note")
        tag = st.selectbox("Tag:", ["suspected error", "interesting pattern",
                                     "need more context", "confirmed valid"], key="upload_tag")
        if st.button("💾 Save Note", key="save_upload_note"):
            st.session_state["user_notes"].append({
                "page": "Data Upload", "note": note, "tag": tag
            })
            st.success("Note saved!")

    st.markdown("---")
    st.success("✅ Data loaded! Next step → **🎯 Insight Goals** in the sidebar.")
