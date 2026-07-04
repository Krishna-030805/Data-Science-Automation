"""
ml_engine.py  —  Auto-ML: task detection, multi-model training, evaluation, feature importance.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import cross_val_score, train_test_split, GridSearchCV, KFold, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    mean_squared_error, r2_score,
    silhouette_score, confusion_matrix, classification_report,
    make_scorer
)
from sklearn.inspection import permutation_importance
import pickle
import io
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
import xgboost as xgb
import lightgbm as lgb
from config import RANDOM_STATE, TEST_SIZE, CV_FOLDS


# ─── Task auto-detection ─────────────────────────────────────────────

def detect_task(df: pd.DataFrame, target_col: str) -> str:
    """Detect whether this is a classification or regression task."""
    s = df[target_col].dropna()
    if pd.api.types.is_numeric_dtype(s) and s.nunique() > 10:
        return "regression"
    return "classification"


# ─── Model registry factory ──────────────────────────────────────────

def get_classification_models(selected: list) -> dict:
    models = {
        "Logistic Regression":      LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "Random Forest":            RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE),
        "XGBoost":                  xgb.XGBClassifier(eval_metric="logloss", random_state=RANDOM_STATE, verbosity=0),
        "LightGBM":                 lgb.LGBMClassifier(random_state=RANDOM_STATE, verbose=-1),
        "K-Nearest Neighbors":      KNeighborsClassifier(),
        "Support Vector Machine":   SVC(probability=True, random_state=RANDOM_STATE),
    }
    return {k: v for k, v in models.items() if k in selected}


def get_regression_models(selected: list) -> dict:
    models = {
        "Linear Regression":  LinearRegression(),
        "Ridge":              Ridge(random_state=RANDOM_STATE),
        "Lasso":              Lasso(random_state=RANDOM_STATE),
        "Random Forest":      RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE),
        "XGBoost":            xgb.XGBRegressor(random_state=RANDOM_STATE, verbosity=0),
        "LightGBM":           lgb.LGBMRegressor(random_state=RANDOM_STATE, verbose=-1),
    }
    return {k: v for k, v in models.items() if k in selected}


# ─── Data prep ───────────────────────────────────────────────────────

def prepare_data(df: pd.DataFrame, target_col: str):
    """
    Drop non-numeric / non-encodable columns, encode categoricals,
    return X, y ready for sklearn.
    """
    df = df.copy().dropna(subset=[target_col])
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Encode categoricals in X
    for col in X.select_dtypes(include=["object", "category"]).columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))

    # Drop datetime columns
    X = X.select_dtypes(include="number")

    # Encode y if classification
    if not pd.api.types.is_numeric_dtype(y):
        le = LabelEncoder()
        y = le.fit_transform(y.astype(str))

    return X, y


# ─── Training & evaluation ───────────────────────────────────────────

def train_classification(df: pd.DataFrame, target_col: str, selected_models: list,
                          preferred_metric: str = "F1 (weighted)") -> dict:
    X, y = prepare_data(df, target_col)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=TEST_SIZE,
                                               random_state=RANDOM_STATE, stratify=y)
    models = get_classification_models(selected_models)
    results = {}

    for name, model in models.items():
        try:
            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)
            y_prob = model.predict_proba(X_te) if hasattr(model, "predict_proba") else None

            n_classes = len(np.unique(y))
            auc = None
            if y_prob is not None:
                try:
                    auc = roc_auc_score(y_te, y_prob if n_classes > 2 else y_prob[:, 1],
                                        multi_class="ovr", average="weighted")
                except Exception:
                    pass

            results[name] = {
                "Accuracy":    round(accuracy_score(y_te, y_pred), 4),
                "F1 (weighted)": round(f1_score(y_te, y_pred, average="weighted"), 4),
                "ROC-AUC":     round(auc, 4) if auc else "N/A",
                "model":       model,
                "X_test":      X_te,
                "y_test":      y_te,
                "y_pred":      y_pred,
                "feature_names": list(X.columns),
                "error":       None,
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


def train_regression(df: pd.DataFrame, target_col: str, selected_models: list,
                     preferred_metric: str = "R²") -> dict:
    X, y = prepare_data(df, target_col)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=TEST_SIZE,
                                               random_state=RANDOM_STATE)
    models = get_regression_models(selected_models)
    results = {}

    for name, model in models.items():
        try:
            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)
            rmse = np.sqrt(mean_squared_error(y_te, y_pred))
            results[name] = {
                "R²":   round(r2_score(y_te, y_pred), 4),
                "RMSE": round(rmse, 4),
                "MAE":  round(float(np.mean(np.abs(y_te - y_pred))), 4),
                "model": model,
                "X_test": X_te,
                "y_test": y_te,
                "y_pred": y_pred,
                "feature_names": list(X.columns),
                "error": None,
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


def run_clustering(df: pd.DataFrame, k: int = 3) -> dict:
    """KMeans clustering with silhouette score and PCA coords for visualization."""
    num_df = df.select_dtypes(include="number").dropna()

    # KMeans
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    labels = km.fit_predict(num_df)
    sil = silhouette_score(num_df, labels) if len(set(labels)) > 1 else 0

    # PCA for 2D visualization
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(num_df)
    viz_df = pd.DataFrame(coords, columns=["PC1", "PC2"])
    viz_df["Cluster"] = labels.astype(str)

    # Elbow values
    inertia = []
    k_range = range(2, min(10, len(num_df)))
    for ki in k_range:
        km_i = KMeans(n_clusters=ki, random_state=RANDOM_STATE, n_init=10)
        km_i.fit(num_df)
        inertia.append(km_i.inertia_)

    return {
        "labels":          labels,
        "silhouette":      round(float(sil), 4),
        "k":               k,
        "viz_df":          viz_df,
        "elbow_k":         list(k_range),
        "elbow_inertia":   inertia,
        "cluster_centers": pd.DataFrame(km.cluster_centers_, columns=num_df.columns),
    }


# ─── Feature importance ──────────────────────────────────────────────

def get_feature_importance(result: dict, model_name: str) -> pd.DataFrame:
    """Extract feature importances from a trained model result."""
    model = result.get("model")
    feat_names = result.get("feature_names", [])
    if model is None or not feat_names:
        return pd.DataFrame()

    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
    elif hasattr(model, "coef_"):
        imp = np.abs(model.coef_).flatten()[:len(feat_names)]
    else:
        # Fallback to permutation importance if native isn't available
        return get_permutation_importance(model, result["X_test"], result["y_test"])

    df_imp = pd.DataFrame({"Feature": feat_names, "Importance": imp})
    return df_imp.sort_values("Importance", ascending=False).reset_index(drop=True)


def get_permutation_importance(model, X_val, y_val) -> pd.DataFrame:
    """Compute permutation importance (model agnostic)."""
    r = permutation_importance(model, X_val, y_val, n_repeats=5, random_state=RANDOM_STATE)
    df_imp = pd.DataFrame({"Feature": list(X_val.columns), "Importance": r.importances_mean})
    return df_imp.sort_values("Importance", ascending=False).reset_index(drop=True)


# ─── Best model picker ───────────────────────────────────────────────

def pick_best_model(results: dict, task: str, metric: str = None) -> str:
    """Return the name of the best-performing model."""
    valid = {k: v for k, v in results.items() if not v.get("error")}
    if not valid:
        return "None"

    if task == "classification":
        key = metric if metric in ["Accuracy", "F1 (weighted)", "ROC-AUC"] else "F1 (weighted)"
    elif task == "regression":
        key = metric if metric in ["R²", "RMSE", "MAE"] else "R²"
    else:
        return max(valid, key=lambda k: valid[k].get("silhouette", 0))

    reverse = (key != "RMSE" and key != "MAE")
    filtered = {k: v for k, v in valid.items() if isinstance(v.get(key), float)}
    if not filtered:
        return list(valid.keys())[0]
    return max(filtered, key=lambda k: filtered[k][key] if reverse else -filtered[k][key])
# ─── Hyperparameter Tuning ───────────────────────────────────────────

def tune_best_model(model, X, y, task: str):
    """Run a light GridSearchCV on the best model."""
    name = type(model).__name__
    
    param_grids = {
        "RandomForestClassifier": {"n_estimators": [50, 100, 200], "max_depth": [None, 10, 20]},
        "RandomForestRegressor":  {"n_estimators": [50, 100, 200], "max_depth": [None, 10, 20]},
        "XGBClassifier":          {"n_estimators": [50, 100], "learning_rate": [0.01, 0.1]},
        "XGBRegressor":           {"n_estimators": [50, 100], "learning_rate": [0.01, 0.1]},
        "LGBMClassifier":         {"n_estimators": [50, 100], "num_leaves": [31, 50]},
        "LGBMRegressor":          {"n_estimators": [50, 100], "num_leaves": [31, 50]},
        "SVC":                    {"C": [0.1, 1, 10], "kernel": ["rbf", "linear"]},
        "LogisticRegression":     {"C": [0.1, 1, 10]},
        "Ridge":                  {"alpha": [0.1, 1.0, 10.0]},
        "Lasso":                  {"alpha": [0.1, 1.0, 10.0]},
    }
    
    grid = param_grids.get(name)
    if not grid:
        return model, {} # No grid defined
        
    scoring = "f1_weighted" if task == "classification" else "r2"
    cv = StratifiedKFold(n_splits=3) if task == "classification" else KFold(n_splits=3)
    
    gs = GridSearchCV(model, grid, cv=cv, scoring=scoring, n_jobs=-1)
    gs.fit(X, y)
    
    return gs.best_estimator_, gs.best_params_


def get_cv_scores(model, X, y, task: str):
    """Get per-fold CV scores for distribution plotting."""
    scoring = "f1_weighted" if task == "classification" else "r2"
    cv = StratifiedKFold(n_splits=CV_FOLDS) if task == "classification" else KFold(n_splits=CV_FOLDS)
    scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
    return scores.tolist()


# ─── Serialization ────────────────────────────────────────────────────

def serialize_model(model):
    """Return model as bytes for download."""
    buffer = io.BytesIO()
    pickle.dump(model, buffer)
    return buffer.getvalue()
