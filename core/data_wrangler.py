"""
data_wrangler.py  —  Interactive data cleaning, encoding, scaling, feature engineering.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler


# ─── Missing value handling ───────────────────────────────────────────

def fill_missing(df: pd.DataFrame, col: str, strategy: str, custom_value=None) -> pd.DataFrame:
    df = df.copy()
    if strategy == "mean":
        df[col] = df[col].fillna(df[col].mean())
    elif strategy == "median":
        df[col] = df[col].fillna(df[col].median())
    elif strategy == "mode":
        df[col] = df[col].fillna(df[col].mode()[0])
    elif strategy == "forward fill":
        df[col] = df[col].ffill()
    elif strategy == "backward fill":
        df[col] = df[col].bfill()
    elif strategy == "custom":
        df[col] = df[col].fillna(custom_value)
    elif strategy == "drop rows":
        df = df.dropna(subset=[col])
    return df


def fill_all_missing(df: pd.DataFrame, strategy: str = "median") -> pd.DataFrame:
    """Fill all missing values in one pass."""
    df = df.copy()
    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df = fill_missing(df, col, strategy)
        else:
            df = fill_missing(df, col, "mode")
    return df


# ─── Duplicate handling ───────────────────────────────────────────────

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)


# ─── Column operations ────────────────────────────────────────────────

def drop_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    return df.drop(columns=cols, errors="ignore")


def rename_column(df: pd.DataFrame, old: str, new: str) -> pd.DataFrame:
    return df.rename(columns={old: new})


# ─── Encoding ─────────────────────────────────────────────────────────

def label_encode(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
    return df


def one_hot_encode(df: pd.DataFrame, cols: list, drop_first: bool = False) -> pd.DataFrame:
    return pd.get_dummies(df, columns=cols, drop_first=drop_first)


# ─── Scaling ──────────────────────────────────────────────────────────

def scale_minmax(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df = df.copy()
    scaler = MinMaxScaler()
    df[cols] = scaler.fit_transform(df[cols])
    return df


def scale_standard(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df = df.copy()
    scaler = StandardScaler()
    df[cols] = scaler.fit_transform(df[cols])
    return df


# ─── Feature engineering ──────────────────────────────────────────────

def create_column_from_expr(df: pd.DataFrame, new_col: str, expr: str) -> pd.DataFrame:
    """
    Create a new column using a pandas eval expression.
    Example: expr = "col_a * col_b" or "col_a + col_b / 2"
    """
    df = df.copy()
    df[new_col] = df.eval(expr)
    return df


def extract_date_features(df: pd.DataFrame, col: str, drop_original: bool = False) -> pd.DataFrame:
    """Parse a column as datetime and extract year, month, day, weekday."""
    df = df.copy()
    dt = pd.to_datetime(df[col], errors="coerce")
    df[f"{col}_year"]    = dt.dt.year
    df[f"{col}_month"]   = dt.dt.month
    df[f"{col}_day"]     = dt.dt.day
    df[f"{col}_weekday"] = dt.dt.day_name()
    if drop_original:
        df = df.drop(columns=[col])
    return df


def clean_text_col(df: pd.DataFrame, col: str, lower: bool = True, strip: bool = True, remove_special: bool = False) -> pd.DataFrame:
    """Clean a text/object column."""
    df = df.copy()
    s = df[col].astype(str)
    if strip:
        s = s.str.strip()
    if lower:
        s = s.str.lower()
    if remove_special:
        s = s.str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
    df[col] = s
    return df


def clip_outliers(df: pd.DataFrame, col: str, lower_pct: float = 0.05, upper_pct: float = 0.95) -> pd.DataFrame:
    """Clip (Winsorize) extreme values in a numeric column."""
    df = df.copy()
    lower_val = df[col].quantile(lower_pct)
    upper_val = df[col].quantile(upper_pct)
    df[col] = df[col].clip(lower=lower_val, upper=upper_val)
    return df


def drop_outlier_rows(df: pd.DataFrame, col: str, method: str = "iqr") -> pd.DataFrame:
    """Drop rows containing outliers in a specific column."""
    df = df.copy()
    if method == "iqr":
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
    else: # z-score
        mean = df[col].mean()
        std = df[col].std()
        lower = mean - 3 * std
        upper = mean + 3 * std
        
    return df[(df[col] >= lower) & (df[col] <= upper)]


def drop_high_null_columns(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Drop columns where more than `threshold` fraction of values are null."""
    limit = int(threshold * len(df))
    return df.dropna(thresh=limit, axis=1)


# ─── Diff / undo support ──────────────────────────────────────────────

def compute_diff(df_before: pd.DataFrame, df_after: pd.DataFrame) -> dict:
    """Return a summary of what changed between two DataFrames."""
    return {
        "rows_before": df_before.shape[0],
        "rows_after":  df_after.shape[0],
        "cols_before": df_before.shape[1],
        "cols_after":  df_after.shape[1],
        "rows_delta":  df_before.shape[0] - df_after.shape[0],
        "cols_delta":  df_before.shape[1] - df_after.shape[1],
        "new_cols":    [c for c in df_after.columns if c not in df_before.columns],
        "dropped_cols":[c for c in df_before.columns if c not in df_after.columns],
    }


def clip_outliers(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[col]):
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df[col] = df[col].clip(lower=lower, upper=upper)
    return df


def extract_date_features(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.copy()
    df[col] = pd.to_datetime(df[col], errors='coerce')
    df[f"{col}_year"] = df[col].dt.year
    df[f"{col}_month"] = df[col].dt.month
    df[f"{col}_day"] = df[col].dt.day
    return df


def clean_text_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.copy()
    if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
        df[col] = df[col].astype(str).str.lower().str.strip()
    return df
