"""
data_loader.py  —  Multi-file upload, merge, and preview engine.
"""

import pandas as pd
import io
from typing import List, Optional


# ─── Loaders ─────────────────────────────────────────────────────────

def load_file(uploaded_file) -> pd.DataFrame:
    """Read a single Streamlit UploadedFile into a DataFrame."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    elif name.endswith(".json"):
        return pd.read_json(uploaded_file)
    elif name.endswith(".parquet"):
        return pd.read_parquet(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {uploaded_file.name}")


def load_multiple(files) -> List[pd.DataFrame]:
    """Load a list of uploaded files into DataFrames."""
    dfs = []
    errors = []
    for f in files:
        try:
            dfs.append((f.name, load_file(f)))
        except Exception as e:
            errors.append((f.name, str(e)))
    return dfs, errors


# ─── Merge strategies ────────────────────────────────────────────────

def merge_concat(dframes: List[pd.DataFrame], reset_index: bool = True) -> pd.DataFrame:
    """Vertical concatenation (stack rows)."""
    result = pd.concat(dframes, ignore_index=reset_index)
    return result


def merge_join(dframes: List[pd.DataFrame], key_col: str, how: str = "inner") -> pd.DataFrame:
    """Horizontal join on a common key column."""
    result = dframes[0]
    for df in dframes[1:]:
        result = pd.merge(result, df, on=key_col, how=how)
    return result


# ─── Quick stats ─────────────────────────────────────────────────────

def get_overview(df: pd.DataFrame) -> dict:
    """Return a quick dict of dataset overview stats."""
    num_cols   = df.select_dtypes(include="number").columns.tolist()
    cat_cols   = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols  = df.select_dtypes(include=["datetime"]).columns.tolist()

    return {
        "rows":         df.shape[0],
        "columns":      df.shape[1],
        "numeric_cols": len(num_cols),
        "cat_cols":     len(cat_cols),
        "date_cols":    len(date_cols),
        "missing_cells": int(df.isnull().sum().sum()),
        "missing_pct":  round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_mb":    round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3),
        "numeric_col_names": num_cols,
        "cat_col_names":     cat_cols,
        "date_col_names":    date_cols,
    }


def infer_column_roles(df: pd.DataFrame) -> dict:
    """Guess the role of each column: id, target-candidate, feature, datetime, text."""
    roles = {}
    for col in df.columns:
        nuniq = df[col].nunique()
        dtype = df[col].dtype
        col_lower = col.lower()

        if dtype in ["datetime64[ns]", "datetime64"]:
            roles[col] = "📅 datetime"
        elif nuniq == df.shape[0] and dtype == object:
            roles[col] = "🔑 id / key"
        elif any(k in col_lower for k in ["target", "label", "class", "y", "outcome"]):
            roles[col] = "🎯 likely target"
        elif dtype == object and df[col].str.len().mean() > 40:
            roles[col] = "📝 free text"
        elif dtype == object:
            roles[col] = "🏷️ categorical"
        else:
            roles[col] = "🔢 numeric"
    return roles
