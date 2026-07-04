"""
visualizer.py  —  All interactive charts with Plotly.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import PALETTE




import plotly.io as pio
import plotly.graph_objects as go

saas_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, sans-serif", color="#A1A1AA"),
        title=dict(font=dict(color="#EDEDED", size=18, family="Inter, sans-serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
        colorway=["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"],
        margin=dict(t=50, b=40, l=40, r=40)
    )
)
pio.templates["saas"] = saas_template
pio.templates.default = "saas"

# ─── Distribution ────────────────────────────────────────────────────

def histogram(df: pd.DataFrame, col: str, color: str = PALETTE[0]) -> go.Figure:
    fig = px.histogram(
        df, x=col, nbins=40, marginal="box",
        color_discrete_sequence=[color],
        title=f"Distribution of {col}",
        template="saas",
    )
    fig.update_layout(bargap=0.05)
    return fig


def box_plot(df: pd.DataFrame, col: str, group_col: str = None) -> go.Figure:
    kwargs = dict(y=col, template="saas",
                  color_discrete_sequence=PALETTE,
                  title=f"Box Plot — {col}")
    if group_col:
        kwargs["x"] = group_col
        kwargs["color"] = group_col
    return px.box(df, **kwargs)


def violin_plot(df: pd.DataFrame, col: str, group_col: str = None) -> go.Figure:
    kwargs = dict(y=col, template="saas",
                  color_discrete_sequence=PALETTE,
                  title=f"Violin Plot — {col}", box=True)
    if group_col:
        kwargs["x"] = group_col
        kwargs["color"] = group_col
    return px.violin(df, **kwargs)


# ─── Categorical ─────────────────────────────────────────────────────

def bar_chart(df: pd.DataFrame, col: str, top_n: int = 15) -> go.Figure:
    vc = df[col].value_counts().head(top_n).reset_index()
    vc.columns = ["Value", "Count"]
    fig = px.bar(vc, x="Value", y="Count",
                 color="Count",
                 color_continuous_scale="Viridis",
                 title=f"Top {top_n} Values — {col}",
                 template="saas")
    return fig


def pie_chart(df: pd.DataFrame, col: str, top_n: int = 8) -> go.Figure:
    vc = df[col].value_counts().head(top_n)
    fig = px.pie(values=vc.values, names=vc.index,
                 title=f"Proportion — {col}",
                 color_discrete_sequence=PALETTE,
                 template="saas")
    return fig


# ─── Correlation ─────────────────────────────────────────────────────

def correlation_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    fig = px.imshow(
        corr_matrix,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        text_auto=".2f",
        title="Correlation Heatmap",
        template="saas",
        aspect="auto",
    )
    fig.update_layout(height=600)
    return fig


def scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, color_col: str = None) -> go.Figure:
    kwargs = dict(x=x_col, y=y_col, template="saas",
                  title=f"{x_col} vs {y_col}",
                  opacity=0.7, color_discrete_sequence=PALETTE)
    if color_col:
        kwargs["color"] = color_col
    return px.scatter(df, **kwargs, trendline="ols")


def pair_plot(df: pd.DataFrame, cols: list, color_col: str = None) -> go.Figure:
    sub_df = df[cols + ([color_col] if color_col else [])].dropna()
    kwargs = dict(dimensions=cols, template="saas",
                  title="Pair Plot (Scatter Matrix)",
                  color_discrete_sequence=PALETTE)
    if color_col:
        kwargs["color"] = color_col
    return px.scatter_matrix(sub_df, **kwargs)


# ─── Time series ─────────────────────────────────────────────────────

def time_series(df: pd.DataFrame, date_col: str, value_col: str) -> go.Figure:
    plot_df = df[[date_col, value_col]].dropna().sort_values(date_col)
    fig = px.line(plot_df, x=date_col, y=value_col,
                  title=f"{value_col} over Time",
                  template="saas",
                  color_discrete_sequence=PALETTE)
    fig.update_traces(line_width=2)
    return fig


# ─── ML charts ───────────────────────────────────────────────────────

def confusion_matrix_chart(y_true, y_pred, labels=None) -> go.Figure:
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig = px.imshow(
        cm, text_auto=True,
        color_continuous_scale="Blues",
        title="Confusion Matrix",
        template="saas",
        labels=dict(x="Predicted", y="Actual"),
    )
    return fig


def feature_importance_chart(imp_df: pd.DataFrame, model_name: str) -> go.Figure:
    top = imp_df.head(20)
    fig = px.bar(
        top.sort_values("Importance"),
        x="Importance", y="Feature",
        orientation="h",
        color="Importance",
        color_continuous_scale="Viridis",
        title=f"Feature Importances — {model_name}",
        template="saas",
    )
    return fig


def residual_plot(y_true, y_pred) -> go.Figure:
    residuals = np.array(y_true) - np.array(y_pred)
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Residuals vs Predicted", "Residual Distribution"))
    fig.add_trace(go.Scatter(x=list(y_pred), y=list(residuals),
                              mode="markers", marker=dict(color=PALETTE[0], opacity=0.6),
                              name="Residuals"), row=1, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=1)
    fig.add_trace(go.Histogram(x=list(residuals), nbinsx=40,
                                marker_color=PALETTE[1], name="Distribution"), row=1, col=2)
    fig.update_layout(template="saas", title="Residual Analysis", showlegend=False)
    return fig


def elbow_chart(k_range: list, inertia: list) -> go.Figure:
    fig = px.line(x=k_range, y=inertia, markers=True,
                  title="Elbow Method — Optimal K",
                  labels={"x": "Number of Clusters (k)", "y": "Inertia"},
                  template="saas",
                  color_discrete_sequence=PALETTE)
    return fig


def cluster_scatter(viz_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(viz_df, x="PC1", y="PC2", color="Cluster",
                     title="Cluster Visualization (PCA 2D)",
                     template="saas",
                     color_discrete_sequence=PALETTE)
    fig.update_traces(marker_size=7, marker_opacity=0.8)
    return fig


def metrics_bar(metrics_df: pd.DataFrame, metric_col: str) -> go.Figure:
    """Bar chart comparing models on a given metric."""
    fig = px.bar(
        metrics_df.sort_values(metric_col, ascending=metric_col in ["RMSE", "MAE"]),
        x="Model", y=metric_col,
        color=metric_col,
        color_continuous_scale="Viridis",
        title=f"Model Comparison — {metric_col}",
        template="saas",
    )
    return fig


def sunburst_chart(df: pd.DataFrame, path: list, values: str = None) -> go.Figure:
    """Hierarchical sunburst chart."""
    fig = px.sunburst(
        df, path=path, values=values,
        color_discrete_sequence=PALETTE,
        template="saas",
        title=f"Sunburst Hierarchy: {' → '.join(path)}"
    )
    return fig


def animated_bubble_chart(df: pd.DataFrame, x: str, y: str, size: str, color: str, hover_name: str) -> go.Figure:
    """Bubble chart (static or animated if time col provided - here static version)."""
    fig = px.scatter(
        df, x=x, y=y, size=size, color=color,
        hover_name=hover_name,
        color_discrete_sequence=PALETTE,
        template="saas",
        title=f"Bubble Analysis: {x} vs {y}",
        log_x=False, size_max=60
    )
    return fig


def cv_score_distribution(scores: list, model_name: str) -> go.Figure:
    """Box plot showing the distribution of CV scores."""
    fig = px.box(
        y=scores,
        template="saas",
        title=f"Cross-Validation Score Distribution — {model_name}",
        color_discrete_sequence=[PALETTE[2]], # Use a distinct color (greenish)
        labels={"y": "Score"}
    )
    fig.update_layout(yaxis_range=[max(0, min(scores) - 0.1), min(1.0, max(scores) + 0.1)])
    return fig
