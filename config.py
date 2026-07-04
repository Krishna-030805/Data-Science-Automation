"""
Global configuration for the DS Automator platform.
"""

# ─── Supported file types ────────────────────────────────────────────
SUPPORTED_TYPES = ["csv", "xlsx", "xls", "json", "parquet"]

# ─── Color palette (Plotly-friendly) ────────────────────────────────
PALETTE = [
    "#6C63FF", "#FF6584", "#43B89C", "#FFD166", "#EF8C40",
    "#A8DADC", "#E63946", "#2A9D8F", "#E9C46A", "#264653",
]

THEME_BG    = "#0F1117"
THEME_CARD  = "#1A1D27"
THEME_ACCENT = "#6C63FF"

# ─── Model registry ─────────────────────────────────────────────────
CLASSIFICATION_MODELS = {
    "Logistic Regression":  "sklearn.linear_model.LogisticRegression",
    "Random Forest":        "sklearn.ensemble.RandomForestClassifier",
    "XGBoost":              "xgboost.XGBClassifier",
    "LightGBM":             "lightgbm.LGBMClassifier",
    "K-Nearest Neighbors":  "sklearn.neighbors.KNeighborsClassifier",
    "Support Vector Machine": "sklearn.svm.SVC",
}

REGRESSION_MODELS = {
    "Linear Regression":    "sklearn.linear_model.LinearRegression",
    "Ridge":                "sklearn.linear_model.Ridge",
    "Lasso":                "sklearn.linear_model.Lasso",
    "Random Forest":        "sklearn.ensemble.RandomForestRegressor",
    "XGBoost":              "xgboost.XGBRegressor",
    "LightGBM":             "lightgbm.LGBMRegressor",
}

CLUSTERING_MODELS = {
    "KMeans":  "sklearn.cluster.KMeans",
    "DBSCAN":  "sklearn.cluster.DBSCAN",
}

# Model suitability reasons (used by AutoNarrate / model opinion panel)
MODEL_REASONS = {
    "Logistic Regression":    "Fast, interpretable baseline for binary/multiclass problems. Works best when classes are linearly separable.",
    "Random Forest":          "Robust ensemble that handles non-linearity and mixed feature types without extensive tuning.",
    "XGBoost":                "Gradient boosting powerhouse — excellent for tabular data, handles missing values natively.",
    "LightGBM":               "Faster than XGBoost on large datasets; great for many features or high-cardinality categoricals.",
    "K-Nearest Neighbors":    "Simple, no-training-required model. Best for small datasets with clear cluster structure.",
    "Support Vector Machine": "Effective in high-dimensional spaces; useful when classes have clear margins.",
    "Linear Regression":      "Interpretable baseline for continuous targets; fast and easy to explain.",
    "Ridge":                  "Linear regression with L2 regularization — prevents overfitting when features are correlated.",
    "Lasso":                  "L1 regularization performs built-in feature selection by zeroing out weak predictors.",
    "KMeans":                 "Partitions data into k groups; works well when clusters are roughly spherical and similar-sized.",
    "DBSCAN":                 "Finds arbitrarily shaped clusters and automatically flags noise/outlier points.",
}

# Model NOT-recommended reasons
MODEL_WARNINGS = {
    "Support Vector Machine": "Slow on large datasets (>10k rows). Consider removing if your data is large.",
    "K-Nearest Neighbors":    "Does not scale well to high-dimensional data. Consider removing if you have many features.",
    "Logistic Regression":    "Assumes linear decision boundary — may underperform on complex, non-linear patterns.",
}

# ─── Insight goal definitions ────────────────────────────────────────
INSIGHT_GOALS = {
    "Descriptive":   "Understand what's in this data — distributions, summaries, value frequencies.",
    "Diagnostic":    "Find out why something happened — correlations, group differences, root causes.",
    "Predictive":    "Build a model to predict a target variable — classification or regression.",
    "Prescriptive":  "Get recommendations — segmentation, clustering, actionable thresholds.",
    "Exploratory":   "Open-ended exploration — show me everything, I'll find patterns myself.",
    "Anomaly / QA":  "Find errors, outliers, and data quality issues.",
}

# ─── CV settings ─────────────────────────────────────────────────────
CV_FOLDS = 5
RANDOM_STATE = 42
TEST_SIZE    = 0.2

# ─── Outlier thresholds ──────────────────────────────────────────────
Z_SCORE_THRESHOLD = 3.0
IQR_MULTIPLIER    = 1.5

# ─── Profiling ───────────────────────────────────────────────────────
MAX_ROWS_PROFILING = 50_000   # cap for ydata-profiling to keep it fast
