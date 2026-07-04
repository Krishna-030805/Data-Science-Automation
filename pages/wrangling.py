"""pages/wrangling.py — Data Wrangling page with before/after diff view."""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from data_wrangler import (fill_missing, drop_duplicates, drop_columns, label_encode,
                            one_hot_encode, scale_minmax, scale_standard,
                            create_column_from_expr, extract_date_features,
                            drop_high_null_columns, compute_diff, clean_text_col,
                            clip_outliers, drop_outlier_rows)
from narrator import narrate_wrangling_step

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ Please upload data first."); st.stop()

st.markdown("# 🔧 Data Wrangling")
st.markdown("Clean, transform, and prepare your data. Every change is tracked and explained.")

# ── Shape summary ─────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Rows", f"{df.shape[0]:,}")
c2.metric("Columns", df.shape[1])
c3.metric("Missing Cells", int(df.isnull().sum().sum()))

# ── Undo last step ───────────────────────────────────────────────────
if st.session_state["df_stack"]:
    if st.button("↩️ Undo Last Step", type="secondary", use_container_width=True):
        st.session_state["df"] = st.session_state["df_stack"].pop()
        st.session_state["wrangling_history"].pop()
        log("Wrangling: Undid last step", status="⚠️")
        st.rerun()

# ── Wrangling sections ────────────────────────────────────────────────

# 1. Handle Missing Values
st.markdown("---")
st.markdown("### 1️⃣ Handle Missing Values")
null_cols = [c for c in df.columns if df[c].isnull().sum() > 0]
if not null_cols:
    st.success("✅ No missing values in the current dataset.")
else:
    st.markdown(f"Columns with missing values: {', '.join(f'`{c}`' for c in null_cols)}")
    fill_col = st.selectbox("Column to fill:", ["ALL (bulk fill)"] + null_cols, key="fill_col")
    strategies = ["mean", "median", "mode", "forward fill", "backward fill", "custom", "drop rows"]
    fill_strat = st.selectbox("Strategy:", strategies, key="fill_strat")
    custom_val = None
    if fill_strat == "custom":
        custom_val = st.text_input("Custom fill value:", key="custom_fill")

    if st.button("▶ Apply Fill", key="apply_fill"):
        before = df.copy()
        if fill_col == "ALL (bulk fill)":
            from data_wrangler import fill_all_missing
            df = fill_all_missing(df, strategy=fill_strat if fill_strat not in ["custom", "drop rows"] else "median")
        else:
            df = fill_missing(df, fill_col, fill_strat, custom_val)
        diff = compute_diff(before, df)
        msg = narrate_wrangling_step(f"Fill Missing ({fill_strat})", before.shape, df.shape,
                                      f"Rows removed: {diff['rows_delta']}")
        st.session_state["df_stack"].append(before)
        st.session_state["df"] = df
        st.session_state["wrangling_history"].append(msg)
        log(f"Wrangling: Fill missing — {fill_col} ({fill_strat})")
        st.success(msg)
        st.rerun()

# 2. Remove Duplicates
st.markdown("---")
st.markdown("### 2️⃣ Remove Duplicate Rows")
dup_count = df.duplicated().sum()
st.markdown(f"Duplicate rows detected: **{dup_count}**")
if dup_count > 0:
    if st.button("🗑️ Drop Duplicates", key="drop_dups"):
        before = df.copy()
        df = drop_duplicates(df)
        diff = compute_diff(before, df)
        msg = narrate_wrangling_step("Drop Duplicates", before.shape, df.shape)
        st.session_state["df_stack"].append(before)
        st.session_state["df"] = df
        st.session_state["wrangling_history"].append(msg)
        log(f"Wrangling: Dropped {diff['rows_delta']} duplicate rows")
        st.success(msg)
        st.rerun()

# 3. Drop Columns
st.markdown("---")
st.markdown("### 3️⃣ Drop Columns")
drop_cols = st.multiselect("Select columns to drop:", df.columns.tolist(), key="drop_cols_sel")
if drop_cols and st.button("🗑️ Drop Selected Columns", key="apply_drop_cols"):
    before = df.copy()
    df = drop_columns(df, drop_cols)
    msg = narrate_wrangling_step("Drop Columns", before.shape, df.shape,
                                  f"Dropped: {', '.join(drop_cols)}")
    st.session_state["df_stack"].append(before)
    st.session_state["df"] = df
    st.session_state["wrangling_history"].append(msg)
    log(f"Wrangling: Dropped columns {drop_cols}")
    st.success(msg)
    st.rerun()

# 4. Drop High-Null Columns
st.markdown("---")
st.markdown("### 4️⃣ Auto-Drop High-Null Columns")
null_thresh = st.slider("Drop columns with more than X% null:", 30, 100, 50, key="null_thresh_slider")
if st.button("▶ Apply", key="apply_null_thresh"):
    before = df.copy()
    df = drop_high_null_columns(df, threshold=null_thresh/100)
    msg = narrate_wrangling_step(f"Drop >{null_thresh}% Null Columns", before.shape, df.shape)
    st.session_state["df_stack"].append(before)
    st.session_state["df"] = df
    st.session_state["wrangling_history"].append(msg)
    log(f"Wrangling: Dropped columns with >{null_thresh}% nulls")
    st.success(msg)
    st.rerun()

# 5. Encode Categoricals
st.markdown("---")
st.markdown("### 5️⃣ Encode Categorical Columns")
cat_cols = df.select_dtypes(include=["object","category"]).columns.tolist()
if not cat_cols:
    st.info("No categorical columns remaining.")
else:
    enc_cols = st.multiselect("Select columns to encode:", cat_cols, key="enc_cols")
    enc_method = st.radio("Encoding method:", ["Label Encoding", "One-Hot Encoding"], horizontal=True, key="enc_method")
    if enc_cols and st.button("▶ Encode", key="apply_enc"):
        before = df.copy()
        df = label_encode(df, enc_cols) if enc_method == "Label Encoding" else one_hot_encode(df, enc_cols)
        msg = narrate_wrangling_step(f"{enc_method}", before.shape, df.shape,
                                      f"Encoded: {', '.join(enc_cols)}")
        st.session_state["df_stack"].append(before)
        st.session_state["df"] = df
        st.session_state["wrangling_history"].append(msg)
        log(f"Wrangling: {enc_method} on {enc_cols}")
        st.success(msg)
        st.rerun()

# 6. Scale Numerics
st.markdown("---")
st.markdown("### 6️⃣ Scale Numeric Columns")
num_cols = df.select_dtypes(include="number").columns.tolist()
if not num_cols:
    st.info("No numeric columns available.")
else:
    scale_cols = st.multiselect("Select columns to scale:", num_cols, key="scale_cols")
    scale_method = st.radio("Scaling method:", ["Min-Max (0–1)", "Standard (Z-score)"],
                             horizontal=True, key="scale_method")
    if scale_cols and st.button("▶ Scale", key="apply_scale"):
        before = df.copy()
        df = scale_minmax(df, scale_cols) if "Min-Max" in scale_method else scale_standard(df, scale_cols)
        msg = narrate_wrangling_step(f"{scale_method}", before.shape, df.shape,
                                      f"Scaled: {', '.join(scale_cols)}")
        st.session_state["df_stack"].append(before)
        st.session_state["df"] = df
        st.session_state["wrangling_history"].append(msg)
        log(f"Wrangling: {scale_method} on {scale_cols}")
        st.success(msg)
        st.rerun()

# 8. Datetime Parsing
st.markdown("---")
st.markdown("### 8️⃣ Datetime Parsing")
date_cols = df.select_dtypes(include=["object"]).columns.tolist()
if not date_cols:
    st.info("No string columns to parse as dates.")
else:
    dt_col = st.selectbox("Select column to parse:", date_cols, key="dt_col_sel")
    drop_orig = st.checkbox("Drop original column?", value=True, key="dt_drop_orig")
    if st.button("▶ Extract Date Features", key="apply_dt"):
        before = df.copy()
        df = extract_date_features(df, dt_col, drop_original=drop_orig)
        msg = narrate_wrangling_step(f"Extract Dates from '{dt_col}'", before.shape, df.shape)
        st.session_state["df_stack"].append(before)
        st.session_state["df"] = df
        st.session_state["wrangling_history"].append(msg)
        log(f"Wrangling: Parsed datetime {dt_col}")
        st.success(msg)
        st.rerun()

# 9. Text Cleaning
st.markdown("---")
st.markdown("### 9️⃣ Text Cleaning")
txt_cols = df.select_dtypes(include=["object"]).columns.tolist()
if not txt_cols:
    st.info("No text columns available.")
else:
    clean_col = st.selectbox("Select text column:", txt_cols, key="txt_clean_col")
    c1, c2, c3 = st.columns(3)
    do_lower = c1.checkbox("Lowercase", value=True)
    do_strip = c2.checkbox("Strip space", value=True)
    do_spec  = c3.checkbox("Remove Special", value=False)
    if st.button("▶ Clean Text", key="apply_clean"):
        before = df.copy()
        df = clean_text_col(df, clean_col, lower=do_lower, strip=do_strip, remove_special=do_spec)
        msg = narrate_wrangling_step(f"Clean Text in '{clean_col}'", before.shape, df.shape)
        st.session_state["df_stack"].append(before)
        st.session_state["df"] = df
        st.session_state["wrangling_history"].append(msg)
        log(f"Wrangling: Cleaned text in {clean_col}")
        st.success(msg)
        st.rerun()

# 10. Outlier Removal/Clipping
st.markdown("---")
st.markdown("### 🔟 Outlimit Management")
if not num_cols:
    st.info("No numeric columns.")
else:
    outlier_col = st.selectbox("Select numeric column:", num_cols, key="outlier_mgr_col")
    outlier_mode = st.radio("Action:", ["Clip (Winsorize)", "Drop Rows"], horizontal=True)
    if outlier_mode == "Clip (Winsorize)":
        l_pct = st.slider("Lower percentile:", 0.0, 0.1, 0.05)
        u_pct = st.slider("Upper percentile:", 0.9, 1.0, 0.95)
        if st.button("▶ Clip Outliers", key="apply_clip"):
            before = df.copy()
            df = clip_outliers(df, outlier_col, l_pct, u_pct)
            msg = narrate_wrangling_step(f"Clip outliers in '{outlier_col}'", before.shape, df.shape)
            st.session_state["df_stack"].append(before)
            st.session_state["df"] = df
            st.session_state["wrangling_history"].append(msg)
            log(f"Wrangling: Clipped outliers in {outlier_col}")
            st.success(msg)
            st.rerun()
    else:
        outlier_method = st.selectbox("Method:", ["iqr", "z-score"])
        if st.button("▶ Drop Outliers", key="apply_drop_out"):
            before = df.copy()
            df = drop_outlier_rows(df, outlier_col, method=outlier_method)
            msg = narrate_wrangling_step(f"Drop outliers in '{outlier_col}'", before.shape, df.shape)
            st.session_state["df_stack"].append(before)
            st.session_state["df"] = df
            st.session_state["wrangling_history"].append(msg)
            log(f"Wrangling: Dropped {before.shape[0] - df.shape[0]} outlier rows")
            st.success(msg)
            st.rerun()

# ── Wrangling history ─────────────────────────────────────────────────
if st.session_state["wrangling_history"]:
    st.markdown("---")
    st.markdown("### 📋 Wrangling History")
    for i, step in enumerate(st.session_state["wrangling_history"], 1):
        st.markdown(f"<div class='human-note'><b>Step {i}:</b> {step}</div>", unsafe_allow_html=True)

    if st.button("↩️ Reset to Original Data"):
        orig = st.session_state.get("df_original")
        if orig is not None:
            st.session_state["df"] = orig.copy()
            st.session_state["wrangling_history"] = []
            log("Wrangling: Reset to original data ⚠️", status="⚠️")
            st.rerun()

# ── Current preview ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 👁️ Current Dataset Preview")
st.dataframe(df.head(20), use_container_width=True)
