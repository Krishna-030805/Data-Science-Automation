"""
data_miner.py  —  Profiling, outlier detection, correlations, data quality scoring.
"""

import pandas as pd
import numpy as np
from config import Z_SCORE_THRESHOLD, IQR_MULTIPLIER


# ─── Column profiling ────────────────────────────────────────────────

def profile_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a per-column profiling DataFrame."""
    records = []
    for col in df.columns:
        s = df[col]
        rec = {
            "Column":      col,
            "Dtype":       str(s.dtype),
            "Non-Null":    s.notna().sum(),
            "Null Count":  s.isna().sum(),
            "Null %":      round(s.isna().mean() * 100, 2),
            "Unique":      s.nunique(),
            "Unique %":    round(s.nunique() / len(s) * 100, 2),
        }
        if pd.api.types.is_numeric_dtype(s):
            rec.update({
                "Min":      round(s.min(), 4),
                "Max":      round(s.max(), 4),
                "Mean":     round(s.mean(), 4),
                "Median":   round(s.median(), 4),
                "Std":      round(s.std(), 4),
                "Skewness": round(s.skew(), 4),
                "Kurtosis": round(s.kurtosis(), 4),
            })
        else:
            try:
                s_valid = s.dropna().astype(str)
                s_min = s_valid.min() if not s_valid.empty else None
                s_max = s_valid.max() if not s_valid.empty else None
            except Exception:
                s_min, s_max = None, None
                
            rec.update({
                "Min": s_min,
                "Max": s_max,
                "Mean": None, "Median": None, "Std": None,
                "Skewness": None, "Kurtosis": None,
            })
        records.append(rec)
    return pd.DataFrame(records)


# ─── Outlier detection ───────────────────────────────────────────────

def detect_outliers_iqr(df: pd.DataFrame) -> dict:
    """IQR-based outlier detection for all numeric columns."""
    result = {}
    num_cols = df.select_dtypes(include="number").columns
    for col in num_cols:
        s = df[col].dropna()
        Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = Q3 - Q1
        lower = Q1 - IQR_MULTIPLIER * iqr
        upper = Q3 + IQR_MULTIPLIER * iqr
        mask = (df[col] < lower) | (df[col] > upper)
        count = int(mask.sum())
        if count > 0:
            result[col] = {
                "count": count,
                "pct":   round(count / len(df) * 100, 2),
                "lower": lower,
                "upper": upper,
                "min":   df[col].min(),
                "max":   df[col].max(),
                "method": "IQR",
            }
    return result


def detect_outliers_zscore(df: pd.DataFrame) -> dict:
    """Z-score outlier detection for all numeric columns."""
    result = {}
    num_cols = df.select_dtypes(include="number").columns
    for col in num_cols:
        s = df[col].dropna()
        if s.std() == 0:
            continue
        z = (df[col] - s.mean()) / s.std()
        mask = z.abs() > Z_SCORE_THRESHOLD
        count = int(mask.sum())
        if count > 0:
            result[col] = {
                "count":  count,
                "pct":    round(count / len(df) * 100, 2),
                "method": "Z-score",
            }
    return result


def get_outlier_rows(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return the actual rows flagged as outliers for a column (IQR)."""
    s = df[col].dropna()
    Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = Q3 - Q1
    lower = Q1 - IQR_MULTIPLIER * iqr
    upper = Q3 + IQR_MULTIPLIER * iqr
    return df[(df[col] < lower) | (df[col] > upper)]


# ─── Correlation ─────────────────────────────────────────────────────

def compute_correlation(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Return correlation matrix for numeric columns."""
    return df.select_dtypes(include="number").corr(method=method).round(3)


def top_correlations(corr_matrix: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top-n correlated pairs (excluding self-correlation)."""
    pairs = (
        corr_matrix
        .where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        .stack()
        .reset_index()
    )
    pairs.columns = ["Feature A", "Feature B", "Correlation"]
    pairs["Abs Corr"] = pairs["Correlation"].abs()
    return pairs.sort_values("Abs Corr", ascending=False).head(n).drop(columns="Abs Corr")


# ─── Data quality score ──────────────────────────────────────────────

def quality_score(df: pd.DataFrame) -> dict:
    """
    Compute an overall data quality score (0–100).
    Deductions: missing data, duplicates, low-variance columns.
    """
    score = 100
    details = []

    missing_pct = df.isnull().mean().mean() * 100
    if missing_pct > 0:
        deduct = min(30, missing_pct * 1.5)
        score -= deduct
        details.append(f"−{deduct:.1f} pts: {missing_pct:.1f}% missing values")

    dup_pct = df.duplicated().sum() / len(df) * 100
    if dup_pct > 0:
        deduct = min(20, dup_pct * 2)
        score -= deduct
        details.append(f"−{deduct:.1f} pts: {dup_pct:.1f}% duplicate rows")

    low_var_cols = [c for c in df.select_dtypes("number").columns if df[c].std() == 0]
    if low_var_cols:
        deduct = len(low_var_cols) * 2
        score -= deduct
        details.append(f"−{deduct} pts: {len(low_var_cols)} zero-variance column(s)")

    score = max(0, round(score, 1))
    label = " Excellent" if score >= 85 else " Good" if score >= 65 else " Fair" if score >= 40 else " Poor"
    return {"score": score, "label": label, "details": details}
