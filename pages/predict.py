"""
pages/predict.py — Inference page for new data.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

# log() injected by app.py; safe fallback for direct execution
if "log" not in dir():
    def log(msg, status="✅"): pass  # noqa

st.markdown("# 🔮 Predict on New Data")
st.markdown("Upload a new dataset with the same columns to get predictions from your best trained model.")

# ── Check for model ──
best_model_name = st.session_state.get("best_model")
ml_results = st.session_state.get("ml_results")

if not best_model_name or not ml_results or best_model_name not in ml_results:
    st.warning("⚠️ No model has been trained yet. Go to **🤖 ML Models** first.")
    st.stop()

best_model = ml_results[best_model_name]["model"]
target_col = st.session_state.get("target_col")
ml_task = st.session_state.get("ml_task")

st.info(f"Using trained model: **{best_model_name}** | Target: `{target_col}`")

# ── Upload new data ──
new_file = st.file_uploader("Upload data for prediction (CSV/Excel/Parquet)", type=["csv", "xlsx", "parquet"])

if new_file:
    try:
        if new_file.name.endswith(".csv"):
            new_df = pd.read_csv(new_file)
        elif new_file.name.endswith(".parquet"):
            new_df = pd.read_parquet(new_file)
        else:
            new_df = pd.read_excel(new_file)
            
        st.success(f"✅ Loaded {new_df.shape[0]} rows for prediction.")
        
        # Check columns
        # In a real app we would align columns more strictly
        if target_col in new_df.columns:
            st.info(f"Target column `{target_col}` found in new data. We will predict and compare.")
        else:
            st.warning(f"Target column `{target_col}` missing (as expected for new data).")

        if st.button("🚀 Run Predictions"):
            with st.spinner("Predicting..."):
                # ── Fix #3: Reuse the stored pipeline (preprocessor + model) ────────
                # When ml_engine.py trains a model, it should store a full sklearn
                # Pipeline that includes the fitted encoders. We look for that first.
                stored_pipeline = ml_results[best_model_name].get("pipeline")
                X_feat_names = ml_results[best_model_name].get("feature_names", [])

                X_new = new_df.copy()
                if target_col and target_col in X_new.columns:
                    X_new = X_new.drop(columns=[target_col])

                if stored_pipeline is not None:
                    # Ideal path: use the full pipeline that has fitted encoders
                    try:
                        y_pred = stored_pipeline.predict(X_new)
                        y_prob = stored_pipeline.predict_proba(X_new) if ml_task == "classification" and hasattr(stored_pipeline, "predict_proba") else None
                    except Exception as e:
                        st.error(f"Pipeline prediction error: {e}")
                        st.stop()
                else:
                    # Fallback: manual alignment (warns user about potential mismatch)
                    st.warning(
                        "⚠️ No stored preprocessing pipeline found. "
                        "Predictions may be incorrect if categorical columns have different "
                        "values than the training data. Retrain the model to generate a stored pipeline."
                    )
                    from sklearn.preprocessing import LabelEncoder
                    for col in X_new.select_dtypes(include=["object", "category"]).columns:
                        le = LabelEncoder()
                        X_new[col] = le.fit_transform(X_new[col].astype(str))
                    X_new = X_new.select_dtypes(include="number")

                    missing_cols = [c for c in X_feat_names if c not in X_new.columns]
                    if missing_cols:
                        st.error(f"Missing required columns: {missing_cols}")
                        st.stop()

                    X_infer = X_new[X_feat_names]
                    y_pred = best_model.predict(X_infer)
                    y_prob = best_model.predict_proba(X_infer) if ml_task == "classification" and hasattr(best_model, "predict_proba") else None

                output_df = new_df.copy()
                if ml_task == "classification" and y_prob is not None:
                    output_df["Prediction"] = y_pred
                    if y_prob.shape[1] == 2:
                        output_df["Confidence"] = y_prob.max(axis=1).round(3)
                else:
                    output_df["Prediction"] = y_pred

                st.markdown("### Prediction Results")
                st.dataframe(output_df.head(100), use_container_width=True)

                csv = output_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Predictions CSV",
                    data=csv,
                    file_name="predictions.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                log(f"Predictions generated for {new_df.shape[0]} rows")

    except Exception as e:
        st.error(f"Error processing new data: {e}")
