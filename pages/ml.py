"""pages/ml.py — ML Models page with model opinion panel."""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from core.ml_engine import (detect_task, train_classification, train_regression,
                        run_clustering, get_feature_importance, pick_best_model,
                        tune_best_model, get_cv_scores, serialize_model)
from core.narrator import narrate_model_choice, narrate_results
from core.visualizer import (confusion_matrix_chart, feature_importance_chart,
                         residual_plot, elbow_chart, cluster_scatter, metrics_bar,
                         cv_score_distribution)
from config import CLASSIFICATION_MODELS, REGRESSION_MODELS, CLUSTERING_MODELS, MODEL_REASONS, MODEL_WARNINGS
from core.ui_components import saas_kpi_card

df = st.session_state.get("df")
if df is None:
    st.warning("⚠️ Please upload data first."); st.stop()

st.markdown("# 🤖 ML Models")
st.markdown("Auto-select, explain, and train models — with full human override capability.")

# ── Task detection ────────────────────────────────────────────────────
ml_task    = st.session_state.get("ml_task")
target_col = st.session_state.get("target_col")

# Allow override here
st.markdown("### ⚙️ Task Configuration")
col1, col2 = st.columns(2)
with col1:
    task_override = st.selectbox(
        "ML Task:",
        ["Auto-detect", "Classification", "Regression", "Clustering"],
        index=0,
        key="task_override"
    )
with col2:
    num_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols = df.columns.tolist()
    if task_override != "Clustering":
        target_override = st.selectbox(
            "Target column:",
            ["— from Goals page —"] + all_cols,
            key="target_override"
        )
        if target_override != "— from Goals page —":
            target_col = target_override
            st.session_state["target_col"] = target_col

# Resolve task
if task_override == "Auto-detect" and target_col:
    ml_task = detect_task(df, target_col)
elif task_override == "Classification":
    ml_task = "classification"
elif task_override == "Regression":
    ml_task = "regression"
elif task_override == "Clustering":
    ml_task = "clustering"

st.session_state["ml_task"] = ml_task

if ml_task and ml_task != "clustering":
    st.info(f"🎯 Task: **{ml_task.upper()}** | Target: `{target_col}`")
elif ml_task == "clustering":
    st.info("🎯 Task: **CLUSTERING** (unsupervised)")
else:
    st.warning("Set your target column or select a task above.")

# ── Model Opinion Panel ───────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗳️ Model Opinion Panel")
st.markdown("""
<div class='narrate-box'>
Below are the models selected for your task — with <b>reasons why</b> each was chosen.
You can <b>remove</b> models you don't want, <b>add</b> others, and choose your preferred evaluation metric.
The system will train all selected models and compare them side by side.
</div>
""", unsafe_allow_html=True)

if ml_task == "classification":
    default_models = list(CLASSIFICATION_MODELS.keys())
elif ml_task == "regression":
    default_models = list(REGRESSION_MODELS.keys())
elif ml_task == "clustering":
    default_models = ["KMeans"]
else:
    default_models = []

# Show reason for each model
if ml_task in ["classification", "regression"]:
    for m in default_models:
        reason = MODEL_REASONS.get(m, "")
        warning = MODEL_WARNINGS.get(m, "")
        warn_html = f"<br><span style='color:#FFD166'>⚠️ {warning}</span>" if warning else ""
        st.markdown(
            f"<div class='ds-card'>"
            f"<b>{m}</b>: {reason}{warn_html}"
            f"</div>",
            unsafe_allow_html=True
        )

# User model selection
if ml_task == "classification":
    selected_models = st.multiselect(
        "✅ Models to train (uncheck to remove):", default_models, default=default_models, key="sel_models")
    metric_choice = st.selectbox("Preferred evaluation metric:", ["F1 (weighted)", "Accuracy", "ROC-AUC"],
                                  key="metric_choice")
elif ml_task == "regression":
    selected_models = st.multiselect(
        "✅ Models to train:", default_models, default=default_models, key="sel_models_reg")
    metric_choice = st.selectbox("Preferred evaluation metric:", ["R²", "RMSE", "MAE"],
                                  key="metric_choice_reg")
elif ml_task == "clustering":
    k = st.slider("Number of clusters (k):", 2, 10, 3, key="cluster_k")
    selected_models = ["KMeans"]
    metric_choice = "Silhouette"
else:
    selected_models = []
    metric_choice = None

# ── Narrate model choice ──────────────────────────────────────────────
if selected_models and ml_task in ["classification", "regression"]:
    narration = narrate_model_choice(ml_task, selected_models, df.shape, target_col)
    st.markdown(f"<div class='narrate-box'>{narration}</div>", unsafe_allow_html=True)

# ── Train ─────────────────────────────────────────────────────────────
st.markdown("---")
if st.button("🚀 Train Models", type="primary", key="train_btn", use_container_width=True):
    if not selected_models:
        st.error("Please select at least one model.")
        st.stop()

    with st.spinner("Training models... this may take a moment ⏳"):
        if ml_task == "classification" and target_col:
            results = train_classification(df, target_col, selected_models, metric_choice)
            best = pick_best_model(results, ml_task, metric_choice)
        elif ml_task == "regression" and target_col:
            results = train_regression(df, target_col, selected_models, metric_choice)
            best = pick_best_model(results, ml_task, metric_choice)
        elif ml_task == "clustering":
            results = {"KMeans": run_clustering(df, k)}
            best = "KMeans"
        else:
            st.error("Cannot train: task or target not set.")
            st.stop()

    st.session_state["ml_results"] = results
    st.session_state["best_model"] = best
    log(f"ML training complete — best model: {best}")
    st.success(f"✅ Training complete! Best model: **{best}**")
    st.rerun()

# ── Results ───────────────────────────────────────────────────────────
results = st.session_state.get("ml_results")
best    = st.session_state.get("best_model")

if results:
    if ml_task == "clustering" and "KMeans" in results:
        cr = results["KMeans"]
        c1, c2 = st.columns(2)
        with c1: saas_kpi_card("Silhouette Score", cr["silhouette"])
        with c2: saas_kpi_card("Clusters (k)", cr["k"])
        st.plotly_chart(elbow_chart(cr["elbow_k"], cr["elbow_inertia"]), use_container_width=True)
        st.plotly_chart(cluster_scatter(cr["viz_df"]), use_container_width=True)
        st.markdown("**Cluster Centers:**")
        st.dataframe(cr["cluster_centers"], use_container_width=True)
    else:
        # Metrics table
        metric_keys = ["Accuracy", "F1 (weighted)", "ROC-AUC"] if ml_task == "classification" else ["R²", "RMSE", "MAE"]
        rows = []
        for name, res in results.items():
            if res.get("error"):
                rows.append({"Model": name, **{k: "Error" for k in metric_keys}, "Error": res["error"]})
            else:
                row = {"Model": name}
                for k in metric_keys:
                    row[k] = res.get(k, "N/A")
                row["🏆 Best"] = "⭐" if name == best else ""
                rows.append(row)
        metrics_df = pd.DataFrame(rows)
        st.dataframe(metrics_df, use_container_width=True)

        # Metrics chart
        primary_metric = metric_keys[0]
        numeric_metrics = metrics_df[metrics_df[primary_metric] != "Error"].copy()
        numeric_metrics[primary_metric] = pd.to_numeric(numeric_metrics[primary_metric], errors="coerce")
        if not numeric_metrics.empty:
            st.plotly_chart(metrics_bar(numeric_metrics, primary_metric), use_container_width=True)

        # AutoNarrate results
        narration = narrate_results(metrics_df, ml_task, best)
        st.markdown(f"<div class='narrate-box'>{narration}</div>", unsafe_allow_html=True)

        # Best model deep dive
        if best and best in results and not results[best].get("error"):
            st.markdown(f"### 🔬 Deep Dive — `{best}`")
            best_res = results[best]
            best_model_obj = best_res["model"]

            # ── 1. Hyperparameter Tuning ──
            with st.expander("⚙️ Tune Model Performance"):
                st.markdown("Run a light search for optimal parameters to squeeze out more accuracy.")
                if st.button("🚀 Run Tuning"):
                    with st.spinner("Tuning..."):
                        from core.ml_engine import prepare_data
                        X_full, y_full = prepare_data(df, target_col)
                        tuned_model, best_params = tune_best_model(best_model_obj, X_full, y_full, ml_task)
                        
                        st.session_state["ml_results"][best]["model"] = tuned_model
                        st.session_state["ml_results"][best]["params_tuned"] = best_params
                        st.success(f"Tuning complete! Best Params: {best_params}")
                        st.rerun()
                
                if best_res.get("params_tuned"):
                    st.json(best_res["params_tuned"])

            # ── 2. Cross-Validation Score Distribution ──
            if st.button("📊 Run Cross-Validation Analysis"):
                with st.spinner("Running CV..."):
                    from core.ml_engine import prepare_data
                    X_full, y_full = prepare_data(df, target_col)
                    cv_scores = get_cv_scores(best_model_obj, X_full, y_full, ml_task)
                    st.plotly_chart(cv_score_distribution(cv_scores, best), use_container_width=True)

            # ── 3. Feature Importance ──
            imp_df = get_feature_importance(best_res, best)
            if not imp_df.empty:
                st.session_state["feature_imp_df"] = imp_df
                st.plotly_chart(feature_importance_chart(imp_df, best), use_container_width=True)

            # ── 4. Task Specific Charts ──
            if ml_task == "classification":
                st.plotly_chart(
                    confusion_matrix_chart(best_res["y_test"], best_res["y_pred"]),
                    use_container_width=True
                )
            elif ml_task == "regression":
                st.plotly_chart(
                    residual_plot(best_res["y_test"], best_res["y_pred"]),
                    use_container_width=True
                )
                
            # ── 5. Download Model ──
            st.markdown("---")
            model_bytes = serialize_model(best_model_obj)
            st.download_button(
                label=f"📥 Download {best} (.pkl)",
                data=model_bytes,
                file_name=f"{best.lower().replace(' ', '_')}_model.pkl",
                mime="application/octet-stream",
                use_container_width=True
            )

# ── User opinion ──────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📝 Your Observations on ML Results"):
    note = st.text_area("What do you think about these results?",
                         placeholder="e.g., 'The model performance seems too good — might be data leakage from column X'",
                         key="ml_note")
    tag = st.selectbox("Tag:", ["suspected error", "interesting pattern",
                                 "need more context", "confirmed valid"], key="ml_tag")
    if st.button("💾 Save Note", key="save_ml_note"):
        st.session_state["user_notes"].append({"page": "ML Models", "note": note, "tag": tag})
        log("User note added on ML Models page")
        st.success("Note saved!")
