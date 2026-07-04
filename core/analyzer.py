"""
analyzer.py  —  Statistical analysis: univariate, bivariate, and hypothesis tests.
"""

import pandas as pd
import numpy as np
from scipy import stats


# ─── Univariate ───────────────────────────────────────────────────────

def univariate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Extended descriptive stats per column."""
    num = df.select_dtypes(include="number")
    records = []
    for col in num.columns:
        s = num[col].dropna()
        records.append({
            "Column":   col,
            "Count":    len(s),
            "Mean":     round(s.mean(), 4),
            "Std":      round(s.std(), 4),
            "Min":      round(s.min(), 4),
            "Q1":       round(s.quantile(0.25), 4),
            "Median":   round(s.median(), 4),
            "Q3":       round(s.quantile(0.75), 4),
            "Max":      round(s.max(), 4),
            "Skewness": round(s.skew(), 4),
            "Kurtosis": round(s.kurtosis(), 4),
            "IQR":      round(s.quantile(0.75) - s.quantile(0.25), 4),
        })
    return pd.DataFrame(records)


def value_counts_table(df: pd.DataFrame, col: str, top_n: int = 20) -> pd.DataFrame:
    """Value frequency table for a categorical column."""
    vc = df[col].value_counts().head(top_n).reset_index()
    vc.columns = ["Value", "Count"]
    vc["Percentage"] = (vc["Count"] / len(df) * 100).round(2)
    return vc


# ─── Normality test ───────────────────────────────────────────────────

def test_normality(df: pd.DataFrame, col: str) -> dict:
    """Shapiro-Wilk normality test (sample up to 5000 for speed)."""
    s = df[col].dropna().sample(min(5000, len(df[col].dropna())), random_state=42)
    stat, p = stats.shapiro(s)
    return {
        "test": "Shapiro-Wilk",
        "statistic": round(float(stat), 6),
        "p_value": round(float(p), 6),
        "normal": p > 0.05,
        "interpretation": (
            " Data appears **normally distributed** (fail to reject H₀)."
            if p > 0.05 else
            " Data is **NOT normally distributed** (reject H₀). "
            "Consider log-transform or non-parametric tests."
        )
    }


# ─── Bivariate correlation test ───────────────────────────────────────

def pearson_test(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Pearson correlation with p-value."""
    s_a = df[col_a].dropna()
    s_b = df[col_b].dropna()
    common = df[[col_a, col_b]].dropna()
    r, p = stats.pearsonr(common[col_a], common[col_b])
    return {
        "test": "Pearson Correlation",
        "Feature A": col_a,
        "Feature B": col_b,
        "statistic": round(float(r), 4),
        "p_value": round(float(p), 6),
        "interpretation": (
            f"r = {r:.4f} → "
            + ("strong" if abs(r) > 0.7 else "moderate" if abs(r) > 0.4 else "weak")
            + " "
            + ("positive" if r > 0 else "negative")
            + " linear relationship. "
            + ("Statistically significant." if p < 0.05 else "Not statistically significant.")
        )
    }


def spearman_test(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Spearman rank correlation."""
    common = df[[col_a, col_b]].dropna()
    r, p = stats.spearmanr(common[col_a], common[col_b])
    return {
        "test": "Spearman Rank Correlation",
        "Feature A": col_a,
        "Feature B": col_b,
        "statistic": round(float(r), 4),
        "p_value": round(float(p), 6),
        "interpretation": (
            f"ρ = {r:.4f} → monotonic relationship strength. "
            + ("Statistically significant." if p < 0.05 else "Not statistically significant.")
        )
    }


# ─── Group comparison ─────────────────────────────────────────────────

def t_test(df: pd.DataFrame, numeric_col: str, group_col: str) -> dict:
    """Independent samples t-test between first two groups of `group_col`."""
    groups = df[group_col].dropna().unique()[:2]
    g1 = df[df[group_col] == groups[0]][numeric_col].dropna()
    g2 = df[df[group_col] == groups[1]][numeric_col].dropna()
    stat, p = stats.ttest_ind(g1, g2)
    return {
        "test": f"T-Test ({group_col}: '{groups[0]}' vs '{groups[1]}')",
        "statistic": round(float(stat), 4),
        "p_value": round(float(p), 6),
        "mean_g1": round(float(g1.mean()), 4),
        "mean_g2": round(float(g2.mean()), 4),
        "interpretation": (
            f"Mean({groups[0]}) = {g1.mean():.4f}, Mean({groups[1]}) = {g2.mean():.4f}. "
            + ("Difference is statistically significant." if p < 0.05
               else "No significant difference detected.")
        )
    }


def anova_test(df: pd.DataFrame, numeric_col: str, group_col: str) -> dict:
    """One-way ANOVA across all groups of `group_col`."""
    groups = [df[df[group_col] == g][numeric_col].dropna().values
              for g in df[group_col].dropna().unique()]
    stat, p = stats.f_oneway(*groups)
    return {
        "test": f"One-Way ANOVA ({numeric_col} by {group_col})",
        "statistic": round(float(stat), 4),
        "p_value": round(float(p), 6),
        "n_groups": len(groups),
        "interpretation": (
            f"Tested across {len(groups)} groups. "
            + ("At least one group mean is significantly different." if p < 0.05
               else "No significant difference in means across groups.")
        )
    }


def chi_square_test(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Chi-squared test of independence between two categorical columns."""
    contingency = pd.crosstab(df[col_a], df[col_b])
    chi2, p, dof, expected = stats.chi2_contingency(contingency)
    return {
        "test": f"Chi-Squared ({col_a} vs {col_b})",
        "statistic": round(float(chi2), 4),
        "p_value": round(float(p), 6),
        "degrees_of_freedom": dof,
        "interpretation": (
            (" Significant association exists between the two variables." if p < 0.05
             else " No significant association detected between the two variables.")
        )
    }
