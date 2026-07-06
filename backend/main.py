import os
import sys
import io
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add core path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from core.data_loader import load_file, merge_concat, merge_join, get_overview, infer_column_roles
from core.narrator import narrate_dataset, narrate_columns, narrate_outliers, narrate_model_choice, narrate_results, narrate_insights
from core.data_miner import profile_columns, detect_outliers_iqr, detect_outliers_zscore, quality_score, get_outlier_rows
from core.ml_engine import detect_task, train_classification, train_regression, run_clustering, get_feature_importance, pick_best_model, tune_best_model, get_cv_scores
from core.insight_generator import build_full_insight_list, generate_hypothesis_verdict
from core.llm_engine import profiler_agent, setup_gemini

# Initialize Gemini if key is in env
if os.environ.get("GEMINI_API_KEY"):
    try:
        setup_gemini()
    except Exception as e:
        print(f"Failed to pre-initialize Gemini: {e}")

app = FastAPI(title="DataSense AI API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory application state
STATE = {
    "df": None,
    "df_original": None,
    "file_names": [],
    "overview": {},
    "profiling_df": None,
    "ml_results": {},
    "ml_task": None,
    "best_model": None,
    "flags": [],
    "all_insights": []
}

class TrainRequest(BaseModel):
    target_col: str
    selected_model: Optional[str] = None

class OutlierRequest(BaseModel):
    method: str  # "IQR" or "Z-Score"

class FlagRequest(BaseModel):
    page: str
    type: str
    description: str

@app.get("/")
def read_root():
    return {"message": "DataSense AI Backend is running."}

@app.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    merge_strategy: str = Form("Stack (Union)"),
    key_col: Optional[str] = Form(None),
    how: Optional[str] = Form("inner")
):
    try:
        dfs_named = []
        errors = []
        for file in files:
            contents = await file.read()
            # Wrap bytes in BytesIO
            file_like = io.BytesIO(contents)
            file_like.name = file.filename
            try:
                df = load_file(file_like)
                dfs_named.append((file.filename, df))
            except Exception as e:
                errors.append((file.filename, str(e)))

        if errors:
            raise HTTPException(status_code=400, detail={"message": "Error loading files", "errors": errors})
        
        if not dfs_named:
            raise HTTPException(status_code=400, detail="No valid files loaded.")

        file_names = [n for n, _ in dfs_named]
        dfs = [d for _, d in dfs_named]

        # Merge strategy
        if len(dfs) > 1:
            if merge_strategy == "Join on Key" and key_col:
                df = merge_join(dfs, key_col, how)
            else:
                df = merge_concat(dfs)
        else:
            df = dfs[0]

        # Reset global state
        STATE["df"] = df
        STATE["df_original"] = df.copy()
        STATE["file_names"] = file_names
        overview = get_overview(df)
        STATE["overview"] = overview
        STATE["flags"] = []
        STATE["all_insights"] = []
        
        roles = infer_column_roles(df)
        narrative = narrate_dataset(overview)

        return {
            "file_names": file_names,
            "overview": overview,
            "roles": roles,
            "narrative": narrative
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview")
def get_preview(rows: int = 100):
    if STATE["df"] is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded.")
    df = STATE["df"]
    # Convert dataframe to JSON-compatible list of dicts, handles NaN/Inf
    preview_data = df.head(rows).fillna("").to_dict(orient="records")
    columns = list(df.columns)
    return {
        "columns": columns,
        "preview": preview_data
    }

@app.post("/profile")
def run_profile():
    if STATE["df"] is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded.")
    
    df = STATE["df"]
    qs = quality_score(df)
    profiling_df = profile_columns(df)
    STATE["profiling_df"] = profiling_df
    
    col_info = profiling_df.set_index("Column").to_dict(orient="index")
    narration = narrate_columns({c: {"null_pct": v["Null %"], "nunique": v["Unique"]}
                                  for c, v in col_info.items()})

    # Generate AI summary if API key is set
    ai_summary = None
    if os.environ.get("GEMINI_API_KEY"):
        try:
            ai_summary = profiler_agent(df)
            STATE["all_insights"].append(ai_summary)
        except Exception as e:
            ai_summary = f"AI summary generation failed: {e}"

    return {
        "quality_score": qs,
        "profiling": profiling_df.fillna("").to_dict(orient="records"),
        "narration": narration,
        "ai_summary": ai_summary
    }

@app.post("/outliers")
def run_outliers(req: OutlierRequest):
    if STATE["df"] is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded.")
    df = STATE["df"]
    
    if req.method == "IQR":
        outlier_summary = detect_outliers_iqr(df)
    else:
        outlier_summary = detect_outliers_zscore(df)
        
    narration_out = narrate_outliers(outlier_summary)
    
    # We will format the outlier rows for each column so the client can query them
    outlier_details = {}
    for col in outlier_summary.keys():
        out_rows = get_outlier_rows(df, col)
        outlier_details[col] = out_rows.fillna("").to_dict(orient="records")
        
    return {
        "summary": outlier_summary,
        "narration": narration_out,
        "details": outlier_details
    }

@app.get("/correlation")
def get_correlation():
    if STATE["df"] is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded.")
    
    df = STATE["df"]
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if len(num_cols) < 2:
        return {"error": "Need at least 2 numeric columns for correlation."}
        
    cols = num_cols[:18]
    corr = df[cols].corr().fillna(0)
    
    # Format correlation matrix
    corr_dict = corr.to_dict(orient="index")
    # Clean matrix keys
    corr_matrix = {str(k): {str(ik): float(iv) for ik, iv in v.items()} for k, v in corr_dict.items()}

    # Format edges/nodes for Physics Universe
    edges = []
    for i, ca in enumerate(cols):
        for j, cb in enumerate(cols):
            if j <= i: continue
            c = float(corr.loc[ca, cb])
            if abs(c) > 0.15:
                edges.append({"source": i, "target": j, "strength": round(c, 3)})

    return {
        "columns": cols,
        "matrix": corr_matrix,
        "physics": {
            "nodes": [{"label": c} for c in cols],
            "edges": edges
        }
    }

@app.post("/train")
def run_train(req: TrainRequest):
    if STATE["df"] is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded.")
    df = STATE["df"]
    
    ml_task = detect_task(df, req.target_col)
    STATE["ml_task"] = ml_task
    
    results = {}
    best = None
    best_model_obj = None
    
    # Import prepare_data locally
    from core.ml_engine import prepare_data
    try:
        X_full, y_full = prepare_data(df, req.target_col)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to prepare data: {e}")
        
    if ml_task == "classification":
        results = train_classification(df, req.target_col)
        best, best_model_obj = pick_best_model(results, ml_task)
    elif ml_task == "regression":
        results = train_regression(df, req.target_col)
        best, best_model_obj = pick_best_model(results, ml_task)
    elif ml_task == "clustering":
        results = run_clustering(df)
        best = "KMeans"
        
    STATE["ml_results"] = results
    STATE["best_model"] = best
    
    # Remove non-serializable objects from results for JSON response
    serialized_results = {}
    for model_name, metrics in results.items():
        serialized_results[model_name] = {k: v for k, v in metrics.items() if k not in ["model", "viz_df"]}
        
    # Get feature importance if not clustering
    importance = []
    if ml_task != "clustering" and best_model_obj:
        try:
            imp_df = get_feature_importance(best_model_obj, X_full.columns, ml_task)
            importance = imp_df.to_dict(orient="records")
        except Exception as e:
            print(f"Feature importance failed: {e}")
            
    opinion = narrate_model_choice(ml_task, serialized_results, best)
    
    return {
        "ml_task": ml_task,
        "results": serialized_results,
        "best_model": best,
        "opinion": opinion,
        "feature_importance": importance
    }

@app.post("/flags")
def add_flag(req: FlagRequest):
    STATE["flags"].append({
        "page": req.page,
        "type": req.type,
        "description": req.description
    })
    return {"message": "Flag added successfully.", "total_flags": len(STATE["flags"])}

@app.get("/insights")
def get_insights():
    if STATE["df"] is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded.")
        
    # Generate default insights if list is empty
    if not STATE["all_insights"]:
        corr_matrix = STATE["df"].select_dtypes(include="number").corr().fillna(0) if STATE["df"] is not None else None
        outlier_sum = detect_outliers_iqr(STATE["df"])
        
        # Build insight list
        STATE["all_insights"] = build_full_insight_list(
            STATE["overview"],
            STATE["profiling_df"],
            corr_matrix,
            outlier_sum,
            STATE["ml_results"],
            STATE["ml_task"] or "",
            STATE["best_model"] or "None",
            []
        )
        
    summary = narrate_insights(STATE["all_insights"])
    
    return {
        "insights": STATE["all_insights"],
        "narrative": summary,
        "flags": STATE["flags"]
    }
