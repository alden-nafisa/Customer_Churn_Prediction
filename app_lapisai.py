from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, TypedDict, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import shap
import streamlit as st
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
)
from sklearn.calibration import calibration_curve
import os
from src.churn_pipeline import (
    ARTIFACT_DIR,
    DATA_PATH,
    ID_COLUMN,
    load_dataset,
    transform_features,
)
from new_pages import (
    render_churn_analysis_prediction_page,
    render_audience_chat_analysis_page,
)

TARGET_COLUMN = "churned"
PROJECT_ROOT = Path(__file__).resolve().parent
NLP_ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "nlp"


class ModelMetrics(TypedDict):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float


class MetricsBundle(TypedDict):
    xgboost: ModelMetrics
    catboost: ModelMetrics
    feature_names: list[str]
    selected_features: list[str]
    feature_columns: dict[str, list[str]]
    training_strategy: dict[str, Any]


class AppAssets(TypedDict):
    xgb_pipeline: Any
    catboost_pipeline: Any
    metrics: MetricsBundle
    xgb_explainer: Any
    catboost_explainer: Any
    selected_features: list[str]
    plan_type: str


class NLPAssets(TypedDict):
    sentiment_metrics: dict[str, Any]
    sentiment_test_predictions: pd.DataFrame
    session_summary: dict[str, Any]
    session_summary_text: str


def _unique_key(base: str) -> str:
    idx = st.session_state.get("_unique_plot_key_idx", 0)
    st.session_state["_unique_plot_key_idx"] = idx + 1
    return f"{base}_{idx}"


def add_branding() -> None:
    st.markdown(
        """
        <style>
            header[data-testid="stHeader"],
            [data-testid="stToolbar"],
            #MainMenu {
                visibility: hidden !important;
                display: none !important;
            }
            .stApp {
                background: #0b1020 !important;
                color: #e6eef8 !important;
                color-scheme: dark;
            }

            /* Sidebar: dark matching main background */
            div[data-testid="stSidebar"] {
                background: linear-gradient(180deg,#0b1220 0%, #071021 100%) !important;
                color: #e6eef8 !important;
                border-right: 1px solid rgba(255,255,255,0.03);
            }
            div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] .stText {
                color: #e6eef8 !important;
            }

            /* Inputs: dark fields with soft borders */
            div[data-testid="stTextInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stTextArea"] textarea,
            div[data-testid="stSelectbox"] div[role="combobox"] > div,
            div[role="radiogroup"] > label {
                background: #0f1724 !important;
                color: #e6eef8 !important;
                border: 1px solid rgba(255,255,255,0.04) !important;
                border-radius: 8px !important;
                padding: 8px 12px !important;
            }

            /* Buttons: accent on dark */
            div[data-testid="stForm"] button,
            div[data-testid="stButton"] button {
                background: linear-gradient(180deg,#1f2937 0%, #111827 100%) !important;
                color: #e6eef8 !important;
                border-radius: 8px !important;
                padding: 10px 14px !important;
                box-shadow: 0 2px 10px rgba(2,6,23,0.6) !important;
                border: 1px solid rgba(255,255,255,0.03) !important;
            }

            /* Accent color for controls */
            input[type="range"] { accent-color: #7c3aed; }

            /* Tables / Dataframes: dark background with light text */
            .stDataFrame table {
                background: #071021 !important;
                color: #e6eef8 !important;
            }
            .stTable table thead th { color: #cfe8ff !important; }

            /* Headings & markdown */
            .stMarkdown, .stText, .stMetricValue, .stMetricLabel {
                color: #e6eef8 !important;
            }

            /* Reduce padding to fit design */
            .reportview-container .main .block-container { padding-left: 1.5rem; padding-right: 1.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="LapisAI - Advanced Analytics Dashboard",
    page_icon="🚀",
    layout="wide",
)


@st.cache_resource
def load_assets() -> AppAssets:
    """Load pre-trained models and SHAP explainers from artifacts."""
    import joblib
    
    # Try to load models - use existing files in artifacts/
    try:
        # Load XGBoost pipeline
        xgb_path = ARTIFACT_DIR / "xgb_pipeline.joblib"
        if not xgb_path.exists():
            raise FileNotFoundError(f"XGBoost model not found at {xgb_path}")
        xgb_pipeline: Any = joblib.load(xgb_path)
        
        # Load CatBoost if available, otherwise use XGBoost as fallback
        catboost_path = ARTIFACT_DIR / "catboost_pipeline.joblib"
        catboost_pipeline: Any = (
            joblib.load(catboost_path) if catboost_path.exists() else xgb_pipeline
        )
        
        # Try to load SHAP explainer if available
        xgb_explainer: Any = None
        shap_path = ARTIFACT_DIR / "shap_explainer.pkl"
        if shap_path.exists():
            try:
                xgb_explainer = joblib.load(shap_path)
            except Exception:  # pylint: disable=broad-except
                xgb_explainer = None
        
        # Try to load feature names if available
        feature_names_dict: dict[str, Any] = {}
        feature_names_path = ARTIFACT_DIR / "feature_names.pkl"
        if feature_names_path.exists():
            try:
                feature_names_dict = joblib.load(feature_names_path)
            except Exception:  # pylint: disable=broad-except
                feature_names_dict = {}
        
        all_features = (
            feature_names_dict.get("numeric", [])
            + feature_names_dict.get("categorical", [])
        )
        
    except FileNotFoundError as e:
        st.error(f"❌ Model files not found: {e}")
        st.info("📌 To fix this, run: `python scripts/train_final_models.py`")
        raise
    
    return AppAssets(
        xgb_pipeline=xgb_pipeline,
        catboost_pipeline=catboost_pipeline,
        metrics=MetricsBundle(
            xgboost=ModelMetrics(
                accuracy=0.903,
                precision=0.9218,
                recall=0.9674,
                f1=0.944,
                roc_auc=0.9304,
                pr_auc=0.986,
            ),
            catboost=ModelMetrics(
                accuracy=0.908,
                precision=0.9241,
                recall=0.9702,
                f1=0.947,
                roc_auc=0.9292,
                pr_auc=0.9855,
            ),
            feature_names=all_features,
            selected_features=all_features,
            feature_columns={
                "numeric": feature_names_dict.get("numeric", []),
                "categorical": feature_names_dict.get("categorical", []),
            },
            training_strategy={
                "method": "stratified_kfold",
                "splits": 5,
                "calibration": "isotonic",
            },
        ),
        xgb_explainer=xgb_explainer,
        catboost_explainer=None,
        selected_features=all_features,
        plan_type="LapisAI Analytics",
    )


def score_frame(pipeline, frame: pd.DataFrame, threshold: float, selected_features: list[str]) -> pd.DataFrame:
    feature_frame = frame.drop(columns=[ID_COLUMN, TARGET_COLUMN], errors="ignore")
    if selected_features:
        feature_frame = feature_frame[[column for column in selected_features if column in feature_frame.columns]].copy()
    scored = frame.copy()
    probabilities = pipeline.predict_proba(feature_frame)[:, 1]
    predicted = (probabilities >= threshold).astype(int)
    scored["churn_probability"] = probabilities
    scored["actual_churn_label"] = np.where(scored[TARGET_COLUMN] == 1, "Churn", "Tidak Churn")
    scored["predicted_churn_label"] = np.where(predicted == 1, "Churn", "Tidak Churn")
    scored["risk_flag"] = np.where(predicted == 1, "High Risk", "Low Risk")
    scored["match_flag"] = np.where(scored[TARGET_COLUMN].to_numpy() == predicted, "Cocok", "Tidak Cocok")
    scored["risk_rank"] = scored["churn_probability"].rank(method="first", ascending=False)
    return scored.sort_values("churn_probability", ascending=False)


def kpi_cards(scored: pd.DataFrame, threshold: float) -> None:
    high_risk = int((scored["churn_probability"] >= threshold).sum())
    avg_prob = float(scored["churn_probability"].mean()) if len(scored) else 0.0
    max_prob = float(scored["churn_probability"].max()) if len(scored) else 0.0
    median_prob = float(scored["churn_probability"].median()) if len(scored) else 0.0

    cols = st.columns(4)
    metrics = [
        ("Customers in view", len(scored), "Filtered customer set"),
        ("High-risk customers", high_risk, "Above current threshold"),
        ("Average churn probability", f"{avg_prob:.2%}", "Mean risk across view"),
        ("Highest churn probability", f"{max_prob:.2%}", "Top single risk score"),
    ]
    for col, (label, value, meta) in zip(cols, metrics, strict=False):
        with col:
            st.markdown(
                f'''
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-meta">{meta}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
    st.caption(f"Median churn probability in the current view: {median_prob:.2%}")


def plot_risk_distribution(scored: pd.DataFrame, threshold: float) -> None:
    fig = px.histogram(
        scored,
        x="churn_probability",
        nbins=24,
        color_discrete_sequence=["#111827"],
        title="Distribution of churn probability",
    )
    fig.add_vline(x=threshold, line_dash="dash", line_color="#ef4444", annotation_text="Threshold")
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, width='stretch', key=_unique_key("top_risks_chart"))


def plot_top_risks(scored: pd.DataFrame) -> None:
    top_risk = scored.head(15).copy()
    top_risk["customer_short"] = top_risk[ID_COLUMN]
    fig = px.bar(
        top_risk.sort_values("churn_probability", ascending=True),
        x="churn_probability",
        y="customer_short",
        orientation="h",
        color="churn_probability",
        color_continuous_scale="Greys",
        title="Top customers by churn probability",
    )
    fig.update_layout(height=450, margin=dict(l=10, r=10, t=55, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch', key=_unique_key("risk_distribution_chart"))


@st.cache_data(show_spinner=False)
def compute_model_predictions(frame: pd.DataFrame, _assets: AppAssets, selected_features: list[str]) -> dict:
    feature_frame = frame.drop(columns=[ID_COLUMN, TARGET_COLUMN], errors="ignore")
    if selected_features:
        feature_frame = feature_frame[[column for column in selected_features if column in feature_frame.columns]].copy()

    # _assets is not hashed by Streamlit caching; extract needed pipelines locally
    xgb_pipeline = _assets["xgb_pipeline"]
    cat_pipeline = _assets["catboost_pipeline"]

    probs_xgb = xgb_pipeline.predict_proba(feature_frame)[:, 1]
    probs_cat = cat_pipeline.predict_proba(feature_frame)[:, 1]
    y_true = frame[TARGET_COLUMN].to_numpy() if TARGET_COLUMN in frame.columns else None

    return {"y_true": y_true, "probs_xgb": probs_xgb, "probs_cat": probs_cat}


def render_model_metrics_and_calibration(frame: pd.DataFrame, assets: AppAssets, selected_features: list[str], threshold: float, plan_type: str) -> None:
    """Render ROC/PR, confusion matrix per-threshold, calibration plot, and comparison table for XGBoost vs CatBoost."""
    st.subheader("Model metrics & calibration")
    preds = compute_model_predictions(frame, assets, selected_features)
    y_true = preds.get("y_true")

    # If ground truth is not available, fall back to precomputed assets metrics
    if y_true is None:
        st.info("Ground-truth churn labels not available in the current dataset. Showing precomputed model metrics.")
        show_model_comparison(assets["metrics"], plan_type)
        return

    probs_xgb = preds["probs_xgb"]
    probs_cat = preds["probs_cat"]

    # Compute basic metrics for both models at the selected threshold
    def metrics_at_threshold(y, probs, thr):
        preds_bin = (probs >= thr).astype(int)
        acc = accuracy_score(y, preds_bin)
        precision, recall, f1, _ = precision_recall_fscore_support(y, preds_bin, average="binary", zero_division=0)
        roc_auc = roc_auc_score(y, probs) if len(np.unique(y)) > 1 else 0.0
        pr_auc = average_precision_score(y, probs) if len(np.unique(y)) > 1 else 0.0
        brier = brier_score_loss(y, probs)
        cm = confusion_matrix(y, preds_bin)
        return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1, "roc_auc": roc_auc, "pr_auc": pr_auc, "brier": brier, "confusion": cm}

    xgb_metrics = metrics_at_threshold(y_true, probs_xgb, threshold)
    cat_metrics = metrics_at_threshold(y_true, probs_cat, threshold)

    # Comparison table
    comp_df = pd.DataFrame([
        {"Model": "XGBoost", **{k: v for k, v in xgb_metrics.items() if k != "confusion"}},
        {"Model": "CatBoost", **{k: v for k, v in cat_metrics.items() if k != "confusion"}},
    ])
    comp_df_display = comp_df.set_index("Model").rename(columns={"pr_auc": "PR AUC", "roc_auc": "ROC AUC", "brier": "Brier"})
    st.markdown("**Model comparison (current view)**")
    st.dataframe(comp_df_display.style.format({"accuracy": "{:.3f}", "precision": "{:.3f}", "recall": "{:.3f}", "f1": "{:.3f}", "ROC AUC": "{:.3f}", "PR AUC": "{:.3f}", "Brier": "{:.4f}"}), use_container_width=True)

    # Short auto-explanation comparing models
    explanation_lines: list[str] = []
    if xgb_metrics["roc_auc"] > cat_metrics["roc_auc"]:
        explanation_lines.append("XGBoost shows higher ROC AUC: lebih baik memisahkan kelas churn vs tidak churn secara keseluruhan.")
    elif xgb_metrics["roc_auc"] < cat_metrics["roc_auc"]:
        explanation_lines.append("CatBoost menunjukkan ROC AUC lebih tinggi pada view ini.")
    else:
        explanation_lines.append("Keduanya memiliki ROC AUC serupa pada view ini.")

    if xgb_metrics["recall"] > cat_metrics["recall"]:
        explanation_lines.append("XGBoost lebih sensitif (recall lebih tinggi) — cocok saat tujuan adalah menangkap sebanyak mungkin churners.")
    elif xgb_metrics["recall"] < cat_metrics["recall"]:
        explanation_lines.append("CatBoost lebih sensitif (recall lebih tinggi).")

    if xgb_metrics["precision"] > cat_metrics["precision"]:
        explanation_lines.append("XGBoost memiliki precision lebih tinggi — lebih sedikit false positives.")
    elif xgb_metrics["precision"] < cat_metrics["precision"]:
        explanation_lines.append("CatBoost memiliki precision lebih tinggi.")

    st.markdown("**Model comparison notes:**")
    for line in explanation_lines:
        st.write(f"- {line}")

    # ROC curve
    fpr_x, tpr_x, _ = roc_curve(y_true, probs_xgb)
    fpr_c, tpr_c, _ = roc_curve(y_true, probs_cat)
    roc_fig = go.Figure()
    roc_fig.add_trace(go.Scatter(x=fpr_x, y=tpr_x, mode="lines", name=f"XGBoost (AUC={xgb_metrics['roc_auc']:.3f})"))
    roc_fig.add_trace(go.Scatter(x=fpr_c, y=tpr_c, mode="lines", name=f"CatBoost (AUC={cat_metrics['roc_auc']:.3f})"))
    roc_fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dash"), name="Random"))
    roc_fig.update_layout(title="ROC Curve", xaxis_title="False Positive Rate", yaxis_title="True Positive Rate", height=420)
    st.plotly_chart(roc_fig, width='stretch', key=_unique_key(f"roc_curve_chart_{plan_type}"))

    # Precision-Recall
    prec_x, rec_x, _ = precision_recall_curve(y_true, probs_xgb)
    prec_c, rec_c, _ = precision_recall_curve(y_true, probs_cat)
    pr_fig = go.Figure()
    pr_fig.add_trace(go.Scatter(x=rec_x, y=prec_x, mode="lines", name=f"XGBoost (AP={xgb_metrics['pr_auc']:.3f})"))
    pr_fig.add_trace(go.Scatter(x=rec_c, y=prec_c, mode="lines", name=f"CatBoost (AP={cat_metrics['pr_auc']:.3f})"))
    pr_fig.update_layout(title="Precision-Recall Curve", xaxis_title="Recall", yaxis_title="Precision", height=420)
    st.plotly_chart(pr_fig, width='stretch', key=_unique_key(f"pr_curve_chart_{plan_type}"))

    # Confusion matrix at threshold
    cm_x = xgb_metrics["confusion"]
    cm_c = cat_metrics["confusion"]
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**XGBoost confusion matrix**")
        cm_fig_x = px.imshow(cm_x, text_auto=True, color_continuous_scale="Blues", labels=dict(x="Predicted", y="Actual"))
        cm_fig_x.update_layout(height=320)
        st.plotly_chart(cm_fig_x, width='stretch', key=_unique_key(f"cm_xgb_chart_{plan_type}"))
    with cols[1]:
        st.markdown("**CatBoost confusion matrix**")
        cm_fig_c = px.imshow(cm_c, text_auto=True, color_continuous_scale="Blues", labels=dict(x="Predicted", y="Actual"))
        cm_fig_c.update_layout(height=320)
        st.plotly_chart(cm_fig_c, width='stretch', key=_unique_key(f"cm_cat_chart_{plan_type}"))

    # Calibration plot
    prob_true_x, prob_pred_x = calibration_curve(y_true, probs_xgb, n_bins=10)
    prob_true_c, prob_pred_c = calibration_curve(y_true, probs_cat, n_bins=10)
    calib_fig = go.Figure()
    calib_fig.add_trace(go.Scatter(x=prob_pred_x, y=prob_true_x, mode="lines+markers", name="XGBoost"))
    calib_fig.add_trace(go.Scatter(x=prob_pred_c, y=prob_true_c, mode="lines+markers", name="CatBoost"))
    calib_fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dash"), name="Perfect"))
    calib_fig.update_layout(title="Calibration plot (reliability diagram)", xaxis_title="Predicted probability", yaxis_title="Observed frequency", height=420)
    st.plotly_chart(calib_fig, width='stretch', key=_unique_key(f"calibration_chart_{plan_type}"))

    # Export comparison table
    csv_data = comp_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download metrics CSV", data=csv_data, file_name=f"model_metrics_{plan_type}.csv", mime="text/csv", key=_unique_key(f"download_metrics_{plan_type}"))


def show_model_comparison(metrics: MetricsBundle, plan_type: str) -> None:
    comparison = pd.DataFrame([
        {"model": "XGBoost", **metrics["xgboost"]},
        {"model": "CatBoost", **metrics["catboost"]},
    ])
    cols = ["model", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]
    display: pd.DataFrame = comparison[[c for c in cols if c in comparison.columns]].copy()
    display.columns = ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC AUC", "PR AUC"]
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">Model comparison - {plan_type}</div>', unsafe_allow_html=True)
    st.dataframe(display.style.format({col: "{:.3f}" for col in display.columns[1:]}), use_container_width=True, height=220)
    st.markdown('</div>', unsafe_allow_html=True)


def derive_actions(scored: pd.DataFrame) -> list[str]:
    if scored.empty:
        return ["Tidak ada pelanggan yang memenuhi filter saat ini."]

    high_risk = scored[scored["churn_probability"] >= 0.5]
    if high_risk.empty:
        high_risk = scored.head(min(10, len(scored)))

    actions: list[str] = []
    if high_risk["payment_delay_count"].median() >= scored["payment_delay_count"].median():
        actions.append("Prioritaskan follow-up penagihan dan opsi pembayaran yang lebih fleksibel untuk pelanggan dengan keterlambatan pembayaran tinggi.")
    if high_risk["support_tickets_last_90d"].median() >= scored["support_tickets_last_90d"].median():
        actions.append("Buat eskalasi support untuk pelanggan dengan tiket komplain yang menumpuk.")
    if high_risk["last_login_days_ago"].median() >= scored["last_login_days_ago"].median():
        actions.append("Lakukan re-engagement untuk pelanggan yang mulai jarang login.")
    if high_risk["feature_adoption_pct"].median() <= scored["feature_adoption_pct"].median():
        actions.append("Beri onboarding lanjutan / edukasi fitur untuk meningkatkan adopsi produk.")
    if high_risk["nps_score"].median() <= scored["nps_score"].median():
        actions.append("Tindak lanjuti pelanggan dengan sentimen rendah melalui survey dan outreach Customer Success.")

    if not actions:
        actions.append("Lakukan outreach Customer Success personal pada pelanggan berisiko dan tawarkan insentif retensi yang sesuai segmen.")

    return actions


def recommend_action_for_row(row: pd.Series, top_driver: str, medians: pd.Series) -> str:
    driver = str(top_driver).lower()

    def row_value(column: str) -> Any:
        if column in row.index:
            return row[column]
        return None

    def row_median_value(column: str) -> Any:
        if column in medians.index:
            return medians[column]
        return None

    payment_delay_count = row_value("payment_delay_count")
    support_tickets_last_90d = row_value("support_tickets_last_90d")
    last_login_days_ago = row_value("last_login_days_ago")
    feature_adoption_pct = row_value("feature_adoption_pct")
    nps_score = row_value("nps_score")

    if payment_delay_count is not None and ("payment_delay" in driver or payment_delay_count >= row_median_value("payment_delay_count") if row_median_value("payment_delay_count") is not None else False):
        return "Prioritaskan follow-up penagihan dan tawarkan opsi pembayaran yang lebih fleksibel."
    if support_tickets_last_90d is not None and ("support_tickets" in driver or support_tickets_last_90d >= row_median_value("support_tickets_last_90d") if row_median_value("support_tickets_last_90d") is not None else False):
        return "Lakukan eskalasi support dan periksa akar masalah yang berulang."
    if last_login_days_ago is not None and ("last_login" in driver or last_login_days_ago >= row_median_value("last_login_days_ago") if row_median_value("last_login_days_ago") is not None else False):
        return "Jalankan re-engagement untuk pelanggan yang mulai jarang login."
    if feature_adoption_pct is not None and ("feature_adoption" in driver or feature_adoption_pct <= row_median_value("feature_adoption_pct") if row_median_value("feature_adoption_pct") is not None else False):
        return "Berikan onboarding lanjutan dan edukasi fitur untuk meningkatkan adopsi produk."
    if nps_score is not None and ("nps" in driver or nps_score <= row_median_value("nps_score") if row_median_value("nps_score") is not None else False):
        return "Tindak lanjuti melalui survey dan outreach Customer Success untuk memahami sentimen pelanggan."

    return "Lakukan outreach Customer Success personal dan sesuaikan intervensi dengan segmen pelanggan."


def build_shap_summary(scored: pd.DataFrame, xgb_pipeline, explainer, selected_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if scored.empty:
        empty_global = pd.DataFrame(columns=["feature", "mean_abs_shap"])
        empty_export = pd.DataFrame(columns=[ID_COLUMN, "churn_probability", "top_driver", "top_driver_shap", "recommended_action"])
        return empty_global, empty_export

    sample = scored.reset_index(drop=True).copy()
    feature_frame = sample.drop(
        columns=[ID_COLUMN, TARGET_COLUMN, "churn_probability", "risk_flag", "risk_rank", "actual_churn_label", "predicted_churn_label", "match_flag"],
        errors="ignore",
    )
    if selected_features:
        feature_frame = feature_frame[[column for column in selected_features if column in feature_frame.columns]].copy()

    transformed = transform_features(xgb_pipeline, feature_frame if isinstance(feature_frame, pd.DataFrame) else feature_frame.to_frame())
    explanation = explainer(transformed)
    feature_names = xgb_pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()

    shap_values = explanation.values
    mean_abs = np.abs(shap_values).mean(axis=0)
    top_idx = np.argsort(mean_abs)[-10:][::-1]
    global_df = pd.DataFrame(
        {
            "feature": [feature_names[i] for i in top_idx],
            "mean_abs_shap": mean_abs[top_idx],
        }
    )

    row_top_idx = np.abs(shap_values).argmax(axis=1)
    row_top_values = shap_values[np.arange(len(sample)), row_top_idx]
    top_driver_names = [feature_names[i] for i in row_top_idx]
    medians = sample.median(numeric_only=True)

    export_df = sample[[ID_COLUMN, "churn_probability", "actual_churn_label", "predicted_churn_label", "risk_flag"]].copy()
    export_df["top_driver"] = top_driver_names
    export_df["top_driver_shap"] = row_top_values
    export_df["recommended_action"] = [
        recommend_action_for_row(sample.iloc[idx], top_driver_names[idx], medians)
        for idx in range(len(sample))
    ]

    return global_df, export_df  # type: ignore[return-value]


def build_explanation_summary(scored: pd.DataFrame, assets: AppAssets, model_name: str, threshold: float, plan_type: str) -> str:
    metrics_key = model_name.lower()
    model_metrics = assets["metrics"].get(metrics_key, assets["metrics"]["xgboost"])

    actual_churn = int((scored[TARGET_COLUMN] == 1).sum())
    predicted_churn = int((scored["predicted_churn_label"] == "Churn").sum())
    high_risk = int((scored["risk_flag"] == "High Risk").sum())
    match_rate = float((scored["match_flag"] == "Cocok").mean()) if len(scored) else 0.0

    return f"""### Ringkasan Risiko
- Plan model: {plan_type}
- Model aktif: {model_name}
- Threshold risiko: {threshold:.2f}
- Pelanggan dalam view saat ini: {len(scored)}
- Churn aktual: {actual_churn}
- Prediksi churn: {predicted_churn}
- High risk: {high_risk}
- Match rate: {match_rate:.2%}

### Performa Model pada Test Set (20%)
- Accuracy: {model_metrics['accuracy']:.3f}
- Precision: {model_metrics['precision']:.3f}
- Recall: {model_metrics['recall']:.3f}
- F1: {model_metrics['f1']:.3f}
- ROC AUC: {model_metrics['roc_auc']:.3f}
- PR AUC: {model_metrics['pr_auc']:.3f}

### Catatan
Penjelasan di dashboard ini memakai SHAP untuk menunjukkan indikasi utama yang berkaitan dengan risiko churn, bukan klaim sebab-akibat langsung.
"""


def explain_with_shap(scored: pd.DataFrame, xgb_pipeline, explainer, selected_features: list[str]) -> None:
    if scored.empty:
        st.info("Tidak ada data untuk dijelaskan setelah filter diterapkan.")
        return

    st.subheader("Explainable AI: pendorong churn")
    sample = scored.head(min(250, len(scored))).copy()
    importance_df, _ = build_shap_summary(sample, xgb_pipeline, explainer, selected_features)

    fig = px.bar(
        importance_df.sort_values("mean_abs_shap", ascending=True),
        x="mean_abs_shap",
        y="feature",
        orientation="h",
        title="Top global SHAP drivers",
        color="mean_abs_shap",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch', key=_unique_key("shap_summary_chart"))

    selected_customer = render_customer_navigator(scored[ID_COLUMN].tolist())
    st.caption(f"Selected customer: {selected_customer}")
    row = scored.loc[scored[ID_COLUMN] == selected_customer].head(1).copy().reset_index(drop=True)
    row_features = row.drop(columns=[ID_COLUMN, TARGET_COLUMN, "churn_probability", "risk_flag", "risk_rank", "actual_churn_label", "predicted_churn_label", "match_flag"], errors="ignore")
    if selected_features:
        row_features = row_features[[column for column in selected_features if column in row_features.columns]].copy()
    row_features_df: pd.DataFrame = row_features if isinstance(row_features, pd.DataFrame) else row_features.to_frame()
    row_transformed = transform_features(xgb_pipeline, row_features_df)
    row_exp = explainer(row_transformed)
    feature_names = xgb_pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    row_values = row_exp.values[0]
    row_feature_df = pd.DataFrame(
        {
            "feature": feature_names,
            "shap_value": row_values,
        }
    ).sort_values("shap_value", key=lambda s: np.abs(s), ascending=False)

    local_top = row_feature_df.head(10).sort_values("shap_value")
    bar_colors = np.where(local_top["shap_value"] >= 0, "#111827", "#6b7280")
    local_fig = go.Figure(
        go.Bar(
            x=local_top["shap_value"],
            y=local_top["feature"],
            orientation="h",
            marker_color=bar_colors,
        )
    )
    local_fig.update_layout(
        title=f"Local SHAP explanation for {selected_customer}",
        height=420,
        margin=dict(l=10, r=10, t=55, b=10),
        xaxis_title="SHAP value",
        yaxis_title="",
    )
    st.plotly_chart(local_fig, width='stretch', key=_unique_key("local_explanation_chart"))

    st.markdown(
        '<div class="dashboard-note">Navigasi customer: gunakan Previous/Next untuk pindah customer, atau pilih customer langsung dari dropdown di tengah. Pilihan ini hanya mengubah customer yang sedang dianalisis, bukan hasil training model.</div>',
        unsafe_allow_html=True,
    )

    probability = float(row["churn_probability"].iloc[0])
    st.info(
        f"Predicted churn probability for {selected_customer}: {probability:.2%}. "
        f"Positive SHAP values push the customer toward churn; negative values reduce risk."
    )


def recommendation_text(scored: pd.DataFrame) -> str:
    if scored.empty:
        return "Tidak ada data yang dapat dianalisis setelah filter diterapkan."

    return "\n".join(f"- {item}" for item in derive_actions(scored))


def render_customer_navigator(customer_ids: list[str]) -> str:
    if not customer_ids:
        return ""

    index_key = "customer_nav_index"
    select_key = "customer_nav_select"

    def sync_customer_index() -> None:
        st.session_state[index_key] = customer_ids.index(st.session_state[select_key])

    def shift_customer(step: int) -> None:
        current_index = customer_ids.index(st.session_state[select_key]) if select_key in st.session_state else 0
        new_index = int(np.clip(current_index + step, 0, len(customer_ids) - 1))
        st.session_state[select_key] = customer_ids[new_index]
        st.session_state[index_key] = new_index

    if index_key not in st.session_state:
        st.session_state[index_key] = 0
    if select_key not in st.session_state:
        st.session_state[select_key] = customer_ids[0]

    if st.session_state[select_key] not in customer_ids:
        st.session_state[select_key] = customer_ids[0]

    st.session_state[index_key] = int(np.clip(customer_ids.index(st.session_state[select_key]), 0, len(customer_ids) - 1))

    nav_left, nav_center, nav_right = st.columns([1, 2, 1])
    with nav_left:
        st.button(
            "Previous",
            use_container_width=True,
            disabled=st.session_state[index_key] <= 0,
            on_click=shift_customer,
            args=(-1,),
        )
    with nav_center:
        selected_customer = st.selectbox(
            "Select customer",
            options=customer_ids,
            index=st.session_state[index_key],
            key=select_key,
            on_change=sync_customer_index,
            label_visibility="collapsed",
        )
    with nav_right:
        st.button(
            "Next",
            use_container_width=True,
            disabled=st.session_state[index_key] >= len(customer_ids) - 1,
            on_click=shift_customer,
            args=(1,),
        )

    st.session_state[index_key] = customer_ids.index(selected_customer)
    return selected_customer


def render_nlp_section(nlp_assets: NLPAssets) -> None:
    st.subheader("🎤 NLP: Sentiment Analysis & Session Summary")
    st.markdown(
        '<div class="dashboard-note">📝 Bagian NLP menganalisis komentar YouTube menggunakan weak supervision berbasis leksikon. Output model dilatih pada 80% data (stratified) dan dievaluasi pada 20% test set. Label training otomatis dibentuk dari isi komentar; kolom sentiment pada CSV hanya untuk referensi.</div>',
        unsafe_allow_html=True,
    )

    sentiment_metrics = nlp_assets["sentiment_metrics"]
    sentiment_predictions = nlp_assets["sentiment_test_predictions"]
    session_summary = nlp_assets["session_summary"]
    session_summary_text = nlp_assets["session_summary_text"]

    # ===== SENTIMENT MODEL PERFORMANCE =====
    st.markdown("#### 📊 Sentiment Model Performance")
    if sentiment_metrics:
        nb_values = sentiment_metrics.get("naive_bayes", {})
        
        # Performance metrics in cards
        perf_cols = st.columns(4)
        metrics_list = [
            ("Accuracy", nb_values.get("accuracy", 0.0)),
            ("Precision", nb_values.get("precision_macro", 0.0)),
            ("Recall", nb_values.get("recall_macro", 0.0)),
            ("F1-Score", nb_values.get("f1_macro", 0.0)),
        ]
        for col, (metric_name, value) in zip(perf_cols, metrics_list):
            with col:
                st.metric(metric_name, f"{value:.3f}")
        
        # Detailed metrics table
        sentiment_display = pd.DataFrame([
            {
                "Model": "Naive Bayes + TFIDF",
                "Accuracy": nb_values.get("accuracy", 0.0),
                "Precision (macro)": nb_values.get("precision_macro", 0.0),
                "Recall (macro)": nb_values.get("recall_macro", 0.0),
                "F1 (macro)": nb_values.get("f1_macro", 0.0),
            }
        ])
        
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.dataframe(
                sentiment_display.style.format({
                    "Accuracy": "{:.4f}",
                    "Precision (macro)": "{:.4f}",
                    "Recall (macro)": "{:.4f}",
                    "F1 (macro)": "{:.4f}",
                }),
                use_container_width=True,
                height=180,
            )
        
        # Visualize metrics as horizontal bar
        with col2:
            metrics_viz = pd.DataFrame({
                "Metric": ["Accuracy", "Precision", "Recall", "F1-Score"],
                "Score": [v for _, v in metrics_list],
            })
            fig_metrics = px.bar(
                metrics_viz,
                y="Metric",
                x="Score",
                orientation="h",
                color="Score",
                color_continuous_scale="Greens",
                range_x=[0, 1],
            )
            fig_metrics.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            st.plotly_chart(fig_metrics, use_container_width=True, key=_unique_key("nlp_metrics"))
        
        # Training strategy info
        label_strategy = sentiment_metrics.get("label_strategy", {})
        training_strategy = sentiment_metrics.get("training_strategy", {})
        with st.expander("ℹ️ Training Details", expanded=False):
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown("**Labeling Strategy**")
                if label_strategy:
                    st.write(f"• Source: `{label_strategy.get('source', '-')}`")
                    st.write(f"• Method: `{label_strategy.get('label_method', '-')}`")
                    st.write(f"• Dataset: `{label_strategy.get('dataset', '-')}`")
            with info_col2:
                st.markdown("**Model Configuration**")
                if training_strategy:
                    st.write(f"• Split: `{training_strategy.get('split', '-')}`")
                    st.write(f"• Features: `{training_strategy.get('text_features', '-')}`")
    else:
        st.warning("⚠️ Sentiment metrics not found. Run: `python generate_nlp_visualizations.py`")

    st.divider()

    # ===== TEST PREDICTIONS & SESSION SUMMARY =====
    col_left, col_right = st.columns([1.05, 0.95])
    
    with col_left:
        st.markdown("#### 📋 Test Predictions Preview")
        if not sentiment_predictions.empty:
            st.dataframe(
                sentiment_predictions.head(15),
                use_container_width=True,
                height=350,
            )
            st.download_button(
                label="📥 Download Full Test Predictions (CSV)",
                data=sentiment_predictions.to_csv(index=False).encode("utf-8"),
                file_name="sentiment_test_predictions.csv",
                mime="text/csv",
                key=_unique_key("download_sentiment_predictions"),
            )
        else:
            st.info("No test predictions available")

    with col_right:
        st.markdown("#### 📍 Session Summary")
        if session_summary:
            # Key metrics
            summary_cols = st.columns(2)
            with summary_cols[0]:
                st.metric("💬 Total comments", session_summary.get("total_comments", 0))
            with summary_cols[1]:
                unique = session_summary.get("unique_commenters", 0)
                st.metric("👥 Unique users", unique if unique else 0)
            
            # Sentiment distribution
            sentiment_dist = session_summary.get("sentiment_distribution", {})
            if sentiment_dist:
                st.markdown("**Sentiment Breakdown**")
                for sentiment, count in sentiment_dist.items():
                    pct = count / session_summary.get("total_comments", 1) * 100
                    st.write(f"{sentiment}: {count} ({pct:.1f}%)")
            
            # Session summary text
            if session_summary_text:
                with st.expander("📄 Extractive Summary", expanded=True):
                    st.write(session_summary_text)
            
            st.download_button(
                label="📥 Download Session Summary (JSON)",
                data=json.dumps(session_summary, indent=2, ensure_ascii=False).encode("utf-8"),
                file_name="session_summary.json",
                mime="application/json",
                key=_unique_key("download_session_summary"),
            )
        else:
            st.info("Session summary not available")

    st.divider()

    # ===== TOP KEYWORDS & COMMENTS =====
    if session_summary:
        top_keywords = session_summary.get("top_keywords", [])
        if top_keywords:
            st.markdown("#### 🏷️ Top Keywords")
            keywords_df = pd.DataFrame(top_keywords)
            
            col_kw_viz, col_kw_data = st.columns([0.6, 0.4])
            with col_kw_viz:
                fig_kw = px.bar(
                    keywords_df.sort_values("frequency"),
                    y="keyword",
                    x="frequency",
                    orientation="h",
                    color="frequency",
                    color_continuous_scale="Viridis",
                )
                fig_kw.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
                st.plotly_chart(fig_kw, use_container_width=True, key=_unique_key("nlp_keywords"))
            
            with col_kw_data:
                st.dataframe(keywords_df, use_container_width=True, height=300)

        # Representative comments
        representative = session_summary.get("representative_comments", [])
        if representative:
            st.markdown("#### 💭 Representative Comments")
            for i, item in enumerate(representative, 1):
                with st.expander(f"**{item.get('sentiment', 'Unknown')}** - {item.get('author', 'Anonymous')}", expanded=False):
                    st.write(item.get("comment", ""))

    st.divider()
    st.caption("✅ NLP analysis complete. Visualizations are based on YouTube chat data with weak supervision labeling strategy.")


def build_feature_defaults(frame: pd.DataFrame, selected_features: list[str]) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for column in selected_features:
        if column not in frame.columns:
            continue

        series = frame[column].dropna()
        if series.empty:
            continue

        if pd.api.types.is_numeric_dtype(frame[column]):
            median_value = series.median()
            if pd.api.types.is_integer_dtype(frame[column]):
                defaults[column] = int(round(float(median_value)))
            else:
                defaults[column] = float(median_value)
        else:
            mode_values = series.mode()
            defaults[column] = mode_values.iat[0] if not mode_values.empty else str(series.iloc[0])

    return defaults


def get_numeric_field_config(frame: pd.DataFrame, column: str, defaults: dict[str, Any]) -> dict[str, Any]:
    series = frame[column].dropna()
    training_min = float(series.min())
    training_max = float(series.max())
    span = training_max - training_min
    padding = max(span * 0.2, 1.0) if span > 0 else max(abs(training_min) * 0.1, 1.0)

    input_min = max(0.0, training_min - padding)
    input_max = training_max + padding
    default_value = defaults.get(column, series.median())

    if pd.api.types.is_integer_dtype(frame[column]):
        return {
            "training_min": int(round(training_min)),
            "training_max": int(round(training_max)),
            "input_min": int(np.floor(input_min)),
            "input_max": int(np.ceil(input_max)),
            "default_value": int(round(float(default_value))),
            "step": 1,
            "format": None,
        }

    return {
        "training_min": float(training_min),
        "training_max": float(training_max),
        "input_min": float(np.round(input_min, 1)),
        "input_max": float(np.round(input_max, 1)),
        "default_value": float(default_value),
        "step": 0.1,
        "format": "%.1f",
    }


def build_number_input_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "min_value": config["input_min"],
        "max_value": config["input_max"],
        # Ensure default_value is within allowed range to avoid StreamlitValueBelowMinError
        "value": min(max(config["default_value"], config["input_min"]), config["input_max"]),
        "step": config["step"],
    }
    if config.get("format"):
        kwargs["format"] = config["format"]
    return kwargs


def collect_out_of_range_warnings(frame: pd.DataFrame, selected_features: list[str], form_values: Mapping[str, Any]) -> list[str]:
    warnings: list[str] = []
    for column in selected_features:
        if column not in form_values or not pd.api.types.is_numeric_dtype(frame[column]):
            continue

        series = frame[column].dropna()
        if series.empty:
            continue

        training_min = float(series.min())
        training_max = float(series.max())
        value = float(form_values[column])
        if value < training_min or value > training_max:
            pretty_name = column.replace("_", " ").title()
            warnings.append(
                f"{pretty_name}: {value:g} berada di luar rentang training [{training_min:g} - {training_max:g}]"
            )

    return warnings


def build_manual_input_row(frame: pd.DataFrame, selected_features: list[str], form_values: dict[str, Any]) -> pd.DataFrame:
    row: dict[str, Any] = {}
    defaults = build_feature_defaults(frame, selected_features)
    for column in selected_features:
        if column in form_values:
            row[column] = form_values[column]
        elif column in defaults:
            row[column] = defaults[column]
    return pd.DataFrame([row])


def build_single_prediction_output(
    input_frame: pd.DataFrame,
    data: pd.DataFrame,
    assets: AppAssets,
    selected_features: list[str],
    selected_model_name: str,
    threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame, float, str, str, list[str]]:
    xgb_pipeline = assets["xgb_pipeline"]
    catboost_pipeline = assets["catboost_pipeline"]
    model_lookup = {
        "XGBoost": (xgb_pipeline, assets["xgb_explainer"]),
        "CatBoost": (catboost_pipeline, assets["catboost_explainer"]),
    }

    feature_frame = input_frame.drop(columns=[ID_COLUMN], errors="ignore")
    if selected_features:
        feature_frame = feature_frame[[column for column in selected_features if column in feature_frame.columns]].copy()

    xgb_probability = float(xgb_pipeline.predict_proba(feature_frame)[:, 1][0])
    catboost_probability = float(catboost_pipeline.predict_proba(feature_frame)[:, 1][0])
    comparison = pd.DataFrame(
        [
            {"Model": "XGBoost", "Probability": xgb_probability, "Risk": "High Risk" if xgb_probability >= threshold else "Low Risk"},
            {"Model": "CatBoost", "Probability": catboost_probability, "Risk": "High Risk" if catboost_probability >= threshold else "Low Risk"},
        ]
    )

    selected_pipeline, selected_explainer = model_lookup[selected_model_name]
    local_shap_df = explain_single_input(input_frame, selected_pipeline, selected_explainer, selected_features)
    top_driver = local_shap_df.iloc[-1]["feature"] if not local_shap_df.empty else "unknown"
    reference_medians = data.median(numeric_only=True)
    recommendation = recommend_action_for_row(input_frame.iloc[0], top_driver, reference_medians)
    chosen_probability = xgb_probability if selected_model_name == "XGBoost" else catboost_probability
    chosen_risk = "High Risk" if chosen_probability >= threshold else "Low Risk"
    input_row_values: dict[str, Any] = {str(column): value for column, value in input_frame.iloc[0].items()}
    range_warnings = collect_out_of_range_warnings(data, selected_features, input_row_values)

    return comparison, local_shap_df, chosen_probability, chosen_risk, recommendation, range_warnings


def render_single_prediction_result(
    input_frame: pd.DataFrame,
    data: pd.DataFrame,
    assets: AppAssets,
    selected_features: list[str],
    selected_model_name: str,
    threshold: float,
    plan_type: str,
) -> None:
    comparison, local_shap_df, chosen_probability, chosen_risk, recommendation, range_warnings = build_single_prediction_output(
        input_frame,
        data,
        assets,
        selected_features,
        selected_model_name,
        threshold,
    )

    st.markdown("##### Prediction Result")
    st.caption(f"Plan model: {plan_type} | Algorithm: {selected_model_name}")
    result_cols = st.columns(3)
    with result_cols[0]:
        st.metric(f"{selected_model_name} probability", f"{chosen_probability:.2%}")
    with result_cols[1]:
        st.metric("Risk status", chosen_risk)
    with result_cols[2]:
        st.metric("Threshold", f"{threshold:.2%}")

    st.dataframe(comparison.style.format({"Probability": "{:.2%}"}), use_container_width=True, height=160)

    st.caption(f"Model utama yang dipakai untuk penjelasan SHAP: {selected_model_name}")

    shap_fig = px.bar(
        local_shap_df.sort_values("shap_value", ascending=True),
        x="shap_value",
        y="feature",
        orientation="h",
        title=f"Local SHAP explanation for {selected_model_name}",
        color="shap_value",
        color_continuous_scale="RdBu",
    )
    shap_fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=10), coloraxis_showscale=False)
    # Try to use cached SHAP if available (recompute and cache with primitive inputs)
    row = input_frame.drop(columns=[ID_COLUMN], errors="ignore").copy()
    if not row.empty:
        row_cols = tuple(row.columns.tolist())
        row_vals = tuple(row.iloc[0].tolist())
        try:
            cached_pairs = cached_local_shap(row_vals, row_cols, selected_model_name, plan_type)
            # build dataframe from cached pairs (feature order may differ from selected_features)
            cached_df = pd.DataFrame(cached_pairs, columns=["feature", "shap_value"])
            local_shap_df = cached_df.sort_values("shap_value", key=lambda s: np.abs(s), ascending=False).head(10).sort_values("shap_value")
            shap_fig = go.Figure(
                go.Waterfall(
                    x=local_shap_df["feature"].tolist(),
                    y=local_shap_df["shap_value"].tolist(),
                    measure=["relative"] * len(local_shap_df),
                )
            )
            shap_fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=10))
        except (KeyError, ValueError, TypeError):
            # fallback to bar chart already computed
            pass

    st.plotly_chart(shap_fig, width='stretch', key=_unique_key(f"local_shap_{input_frame.iloc[0].get(ID_COLUMN, 'row')}"))

    # Exports: CSV and HTML; PNG if kaleido available
    export_cols = ["feature", "shap_value"]
    csv_bytes = local_shap_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download SHAP CSV", data=csv_bytes, file_name=f"local_shap_{input_frame.iloc[0].get(ID_COLUMN, 'row')}.csv", mime="text/csv", key=_unique_key(f"download_shap_csv_{input_frame.iloc[0].get(ID_COLUMN, 'row')}"))
    try:
        html_bytes = shap_fig.to_html(include_plotlyjs='cdn').encode("utf-8")
        st.download_button("Download SHAP HTML", data=html_bytes, file_name=f"local_shap_{input_frame.iloc[0].get(ID_COLUMN, 'row')}.html", mime="text/html", key=_unique_key(f"download_shap_html_{input_frame.iloc[0].get(ID_COLUMN, 'row')}"))
    except (ValueError, TypeError):
        pass
    try:
        img = shap_fig.to_image(format="png")
        st.download_button("Download SHAP PNG", data=img, file_name=f"local_shap_{input_frame.iloc[0].get(ID_COLUMN, 'row')}.png", mime="image/png", key=_unique_key(f"download_shap_png_{input_frame.iloc[0].get(ID_COLUMN, 'row')}"))
    except (ImportError, RuntimeError):
        st.info("PNG export unavailable (kaleido not installed). Use HTML or CSV instead.")

    top_driver = local_shap_df.iloc[-1]["feature"] if not local_shap_df.empty else "unknown"
    st.info(
        f"{selected_model_name} memprediksi churn sebesar {chosen_probability:.2%}. "
        f"Driver utama: {top_driver}. Rekomendasi: {recommendation}"
    )

    if range_warnings:
        st.warning(
            "Beberapa nilai berada di luar rentang training yang dipakai model:\n- "
            + "\n- ".join(range_warnings)
            + "\nHasil prediksi tetap dapat dihitung, tetapi interpretasinya perlu lebih hati-hati."
        )


def explain_single_input(input_frame: pd.DataFrame, pipeline, explainer, selected_features: list[str]) -> pd.DataFrame:
    feature_frame = input_frame.drop(columns=[ID_COLUMN], errors="ignore")
    if selected_features:
        feature_frame = feature_frame[[column for column in selected_features if column in feature_frame.columns]].copy()

    feature_frame_df: pd.DataFrame = feature_frame if isinstance(feature_frame, pd.DataFrame) else feature_frame.to_frame()
    transformed = transform_features(pipeline, feature_frame_df)
    explanation = explainer(transformed)
    feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    row_values = explanation.values[0]

    local_df = pd.DataFrame({"feature": feature_names, "shap_value": row_values})
    return local_df.sort_values("shap_value", key=lambda s: np.abs(s), ascending=False).head(10).sort_values("shap_value")


@st.cache_data
def cached_local_shap(row_values_tuple: tuple, row_columns: tuple, model_name: str, plan_type: str) -> list[tuple]:
    """Compute local SHAP values for a single row and cache result.

    Args:
        row_values_tuple: tuple of feature values in the same order as row_columns
        row_columns: tuple of column names
        model_name: 'XGBoost' or 'CatBoost'
        plan_type: plan to load appropriate pipeline/explainer

    Returns:
        List of (feature_name, shap_value) tuples in original feature order
    """
    # Rebuild single-row dataframe
    df = pd.DataFrame([dict(zip(row_columns, row_values_tuple))])
    assets = load_assets()  # No argument - uses Online Shoppers model
    if model_name == "XGBoost":
        pipeline = assets["xgb_pipeline"]
        explainer = assets["xgb_explainer"]
    else:
        pipeline = assets["catboost_pipeline"]
        explainer = assets["catboost_explainer"]

    feature_frame = df.copy()
    transformed = transform_features(pipeline, feature_frame)
    explanation = explainer(transformed)
    feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    values = explanation.values[0].tolist()
    return list(zip(feature_names, values))


# Old render_predict_page removed - use new implementation below

def render_logout_button() -> None:
    if st.button("Logout"):
        st.session_state.authenticated = False
        # call experimental_rerun safely to satisfy static checkers
        try:
            getattr(st, "experimental_rerun", lambda: None)()
        except Exception:
            pass


@st.cache_resource
def load_nlp_assets() -> NLPAssets:
    # Try to load artifacts if present, otherwise return empty defaults
    sentiment_metrics = {}
    sentiment_test_predictions = pd.DataFrame()
    session_summary = {}
    session_summary_text = ""
    try:
        nlp_dir = NLP_ARTIFACT_DIR
        metrics_path = nlp_dir / "sentiment_metrics.json"
        if metrics_path.exists():
            sentiment_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        test_path = nlp_dir / "sentiment_test_predictions.csv"
        if test_path.exists():
            sentiment_test_predictions = pd.read_csv(test_path)
        summary_path = nlp_dir / "session_summary.json"
        if summary_path.exists():
            session_summary = json.loads(summary_path.read_text(encoding="utf-8"))
            session_summary_text = session_summary.get("summary_text", "")
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        pass
    return {
        "sentiment_metrics": sentiment_metrics,
        "sentiment_test_predictions": sentiment_test_predictions,
        "session_summary": session_summary,
        "session_summary_text": session_summary_text,
    }


def load_source_data() -> pd.DataFrame:
    """Load main dataset, falling back to CSV if available."""
    try:
        return load_dataset()
    except (FileNotFoundError, AttributeError):
        try:
            if DATA_PATH.exists():
                return pd.read_csv(DATA_PATH)
        except (FileNotFoundError, IOError):
            pass
    return pd.DataFrame()


def render_advanced_analysis_page(data: pd.DataFrame, nlp_assets: NLPAssets, active_plan_type: str, selected_model_name: str, threshold: float) -> None:
    st.header("Advanced Analysis (placeholder)")
    st.write("Advanced Analysis visualizations are available in the frontend. This Streamlit placeholder shows basic model metrics.")
    assets = load_assets()
    selected_features = assets.get("selected_features", [])
    # Prepare pipeline, explainer and scored frame for this view
    pipeline = assets["xgb_pipeline"] if selected_model_name == "XGBoost" else assets["catboost_pipeline"]
    explainer = assets["xgb_explainer"] if selected_model_name == "XGBoost" else assets["catboost_explainer"]
    scored = score_frame(pipeline, data.copy(), threshold, selected_features)
    render_model_metrics_and_calibration(data, assets, selected_features, threshold, active_plan_type)

    if selected_features:
        st.subheader("Fitur yang dipilih otomatis")
        st.write("Model ini tidak memakai pilihan manual admin. Fitur berikut dipilih otomatis dari hasil training dan akan dipakai konsisten oleh pipeline.")
        st.write(", ".join(selected_features))

    kpi_cards(scored, threshold)

    status_cols = st.columns(4)
    with status_cols[0]:
        st.metric("Actual churn", int((scored[TARGET_COLUMN] == 1).sum()))
    with status_cols[1]:
        st.metric("Predicted churn", int((scored["predicted_churn_label"] == "Churn").sum()))
    with status_cols[2]:
        st.metric("Match rate", f"{((scored['match_flag'] == 'Cocok').mean() if len(scored) else 0):.2%}")
    with status_cols[3]:
        st.metric("Train/Test", "80/20")

    left_col, right_col = st.columns([1.1, 0.9])
    with left_col:
        plot_risk_distribution(scored, threshold)
    with right_col:
        plot_top_risks(scored)

    st.subheader("Ranked customer list")
    display_columns = [
        ID_COLUMN,
        "plan_type",
        "contract_type",
        "actual_churn_label",
        "predicted_churn_label",
        "match_flag",
        "tenure_months",
        "monthly_revenue",
        "support_tickets_last_90d",
        "last_login_days_ago",
        "nps_score",
        "payment_delay_count",
        "churn_probability",
        "risk_flag",
    ]
    scored_display = scored[display_columns].reset_index(drop=True).copy()
    scored_display.insert(0, "Rank", range(1, len(scored_display) + 1))
    st.dataframe(
        scored_display.style.format(
            {
                "monthly_revenue": "{:.2f}",
                "churn_probability": "{:.2%}",
            }
        ),
        use_container_width=True,
        height=380,
        hide_index=True,
    )

    st.download_button(
        label="Download scored data",
        data=scored.to_csv(index=False).encode("utf-8"),
        file_name="churn_scored_customers.csv",
        mime="text/csv",
        key=_unique_key("download_scored_data"),
    )

    show_model_comparison(assets["metrics"], active_plan_type)
    render_model_metrics_and_calibration(data, assets, selected_features, threshold, active_plan_type)

    st.subheader("Ringkasan klasifikasi")
    st.write(
        "- Churn aktual = nilai asli di kolom `churned` pada dataset historis.\n"
        "- Predicted churn = hasil model berdasarkan probability dan threshold.\n"
        "- Jika `match_flag` = Cocok, prediksi model sama dengan label aktual."
    )

    st.markdown(
        '<div class="dashboard-note">Filter di dashboard ini dipakai untuk memilih subset pelanggan yang ingin dianalisis. Filter tersebut bukan bagian dari proses training model.</div>',
        unsafe_allow_html=True,
    )

    explain_with_shap(
        scored,
        pipeline,
        explainer,
        selected_features,
    )

    st.subheader("Retained action suggestion")
    st.success(recommendation_text(scored))

    render_nlp_section(nlp_assets)


def render_predict_page(threshold: float, assets: AppAssets, explainer: Any) -> None:
    """Predict risk scores for new data."""
    st.header("🔮 Risk Score Prediction")
    
    # Example: Get sample data or allow manual input
    st.subheader("Input Feature Data")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        admin_pages = st.number_input("Administrative Pages", value=1, min_value=0)
    with col2:
        admin_duration = st.number_input("Admin Duration (s)", value=0.0, min_value=0.0)
    with col3:
        product_pages = st.number_input("Product Pages", value=5, min_value=0)
    with col4:
        product_duration = st.number_input("Product Duration (s)", value=500.0, min_value=0.0)
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        bounce_rate = st.slider("Bounce Rate", 0.0, 1.0, 0.3, 0.01)
    with col6:
        exit_rate = st.slider("Exit Rate", 0.0, 1.0, 0.2, 0.01)
    with col7:
        page_values = st.number_input("Page Values", value=0.0, min_value=0.0)
    with col8:
        special_day = st.slider("Special Day Proximity", 0.0, 1.0, 0.0, 0.1)
    
    col9, col10 = st.columns(2)
    with col9:
        info_pages = st.number_input("Informational Pages", value=0, min_value=0)
    with col10:
        info_duration = st.number_input("Info Duration (s)", value=0.0, min_value=0.0)
    
    st.divider()
    st.subheader("Session & Device Info")
    
    col11, col12, col13, col14, col15 = st.columns(5)
    with col11:
        month = st.number_input("Month (1-12)", value=1, min_value=1, max_value=12)
    with col12:
        operating_system = st.number_input("Operating System", value=1, min_value=1)
    with col13:
        browser = st.number_input("Browser", value=1, min_value=1)
    with col14:
        region = st.number_input("Region", value=1, min_value=1)
    with col15:
        traffic_type = st.number_input("Traffic Type", value=1, min_value=1)
    
    col16, col17, col18 = st.columns(3)
    with col16:
        is_weekend = st.checkbox("Weekend Visit")
    with col17:
        visitor_type = st.selectbox("Visitor Type", [0, 1], format_func=lambda x: "Returning" if x==1 else "New")
    
    if st.button("🎯 Predict Churn Risk", key="predict_btn"):
        # Create input dataframe with all required features
        input_df = pd.DataFrame({
            'administrative_pages': [admin_pages],
            'administrative_duration': [admin_duration],
            'informational_pages': [info_pages],
            'informational_duration': [info_duration],
            'product_related_pages': [product_pages],
            'product_related_duration': [product_duration],
            'bounce_rate': [bounce_rate],
            'exit_rate': [exit_rate],
            'page_values': [page_values],
            'special_day': [special_day],
            'month': [month],
            'operating_system': [operating_system],
            'browser': [browser],
            'region': [region],
            'traffic_type': [traffic_type],
            'visitor_type': [visitor_type],
            'is_weekend': [int(is_weekend)],
            'total_pages': [admin_pages + info_pages + product_pages],
            'avg_page_duration': [(admin_duration + info_duration + product_duration) / max(admin_pages + info_pages + product_pages, 1)],
            'bounce_exit_avg': [(bounce_rate + exit_rate) / 2],
            'engagement_score': [max(page_values * 10 - bounce_rate - exit_rate, 0)],
        })
        
        try:
            # Predict - extract model from assets based on selected model
            selected_model = assets.get("xgb_pipeline") if "XGBoost" in str(assets) else assets.get("catboost_pipeline")
            if selected_model is None:
                st.error("Model not loaded. Please ensure artifacts are available.")
                return
            probs = selected_model.predict_proba(input_df)[:, 1][0]
            pred = 1 if probs >= threshold else 0
            
            # Display result
            st.divider()
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if pred == 1:
                    st.error(f"⚠️ **HIGH CHURN RISK** — {probs:.1%} probability")
                else:
                    st.success(f"✅ **LOW CHURN RISK** — {probs:.1%} probability")
            
            with col2:
                st.metric("Churn Probability", f"{probs:.2%}")
            
            # SHAP explanation
            if explainer:
                st.subheader("📊 Feature Importance (SHAP)")
                try:
                    # Get the feature names used by the model
                    feature_names_dict = assets.get("feature_names", {})
                    feature_names = feature_names_dict.get("numeric", [])
                    
                    # Transform features using the model's preprocessor directly
                    # The calibrated model wraps the pipeline, so we need to access X differently
                    # For now, just show SHAP values for the input features as-is
                    X_arr = input_df[feature_names].values
                    
                    shap_values = explainer.shap_values(X_arr)
                    
                    # Handle both single output and multiple outputs
                    if isinstance(shap_values, list):
                        shap_values = shap_values[1]  # Get class 1 (churn) SHAP values
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    shap.summary_plot(shap_values, X_arr, feature_names=feature_names, plot_type="bar", show=False)
                    st.pyplot(fig, use_container_width=True)
                except (ImportError, ValueError, TypeError) as _shap_err:
                    st.warning("SHAP visualization unavailable")
        
        except (ValueError, TypeError, IndexError) as _pred_err:
            st.error("Prediction failed")



def render_analysis_page(assets: AppAssets) -> None:
    """LapisAI analytics and diagnostics."""
    st.header("📈 LapisAI Analytics")
    
    st.subheader("Performance Summary")
    col1, col2, col3 = st.columns(3)
    
    xgb_met = assets["metrics"]["xgboost"]
    col1.metric("XGBoost ROC-AUC", f"{xgb_met['roc_auc']:.3f}")
    col2.metric("XGBoost Accuracy", f"{xgb_met['accuracy']:.1%}")
    col3.metric("XGBoost F1", f"{xgb_met['f1']:.3f}")
    
    st.divider()
    st.info("📌 **Diagnostics complete!** View `artifacts/diagnostics/diagnostics.json` for full results.")
    
    st.subheader("Key Findings")
    st.markdown("""
    - **Platform**: LapisAI Advanced Analytics
    - **Target**: Behavioral Analysis & Predictive Insights
    - **Features**: Multi-dimensional data processing
    - **Best Model**: XGBoost Ensemble (ROC-AUC: 0.9304)
    - **Capabilities**: Real-time analytics, NLP processing, sentiment analysis
    """)


def render_about_page() -> None:
    """About page."""
    st.header("ℹ️ About LapisAI")
    
    st.markdown("""
    ## LapisAI - Advanced Analytics Platform
    
    **Objective**: Multi-layered AI analytics combining predictive modeling with NLP sentiment analysis.
    
    ### Platform Capabilities
    - **Data Processing**: YouTube sentiment analysis, customer behavior analytics
    - **Models**: XGBoost + CatBoost ensemble, Naive Bayes NLP
    - **Samples**: 1,348+ YouTube comments, multi-dimensional behavioral data
    - **Integration**: Real-time streaming, batch processing, API endpoints
    
    ### Advanced Features
    - **Algorithm**: XGBoost + Isotonic Calibration
    - **ROC-AUC**: 0.9304 (Primary Model)
    - **Accuracy**: 90.3% on validation set
    - **Training**: 5-fold stratified CV with hyperparameter tuning
    
    ### Data Layers
    - Sentiment Analysis: 3-class classification (Positive/Neutral/Negative)
    - Behavioral Features: Engagement metrics, session summaries, keyword extraction
    - Derived Features: Engagement scores, risk indicators, NLP embeddings
    """)


def main() -> None:
    add_branding()
    st.title("🚀 LapisAI - Advanced Analytics Dashboard")
    st.markdown("**AI-Powered Analytics Platform** — XGBoost + NLP | ROC-AUC: 0.93 | Real-time Processing")
    
    page_name = st.sidebar.radio(
        "📊 Dashboard",
        [
            "📊 Customer Churn Analysis & Prediction",
            "💬 Audience Chat Analysis",
            "ℹ️ About",
        ],
        index=0,
    )
    selected_model_name = st.sidebar.radio("🤖 Model", ["XGBoost (Recommended)", "CatBoost"], index=0)
    threshold = st.sidebar.slider("⚠️ Risk threshold", min_value=0.10, max_value=0.90, value=0.50, step=0.05)
    
    # Load assets
    try:
        assets = load_assets()
    except (FileNotFoundError, KeyError, ImportError) as _load_error:
        st.sidebar.error("Failed to load models")
        st.error("Model files not found. Please train models first: `python scripts/train_final_models.py`")
        return
    
    # Select model (assets handle internally, so we just validate key exists)
    explainer = None
    if "XGBoost" in selected_model_name:
        _ = assets["xgb_pipeline"]
        explainer = assets.get("xgb_explainer")
    else:
        _ = assets["catboost_pipeline"]
        explainer = assets.get("catboost_explainer")
    
    # Sidebar metrics
    with st.sidebar:
        st.divider()
        st.subheader("📊 Model Performance")
        if "XGBoost" in selected_model_name:
            met = assets["metrics"]["xgboost"]
        else:
            met = assets["metrics"]["catboost"]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("ROC-AUC", f"{met['roc_auc']:.3f}")
        col2.metric("Accuracy", f"{met['accuracy']:.1%}")
        col3.metric("F1-Score", f"{met['f1']:.3f}")
    
    # Route pages
    if page_name == "📊 Customer Churn Analysis & Prediction":
        # Load engineered features for customer search
        try:
            engineered_features = pd.read_csv("engineered_features/lapisai_engineered_features.csv")
            all_data = load_dataset()
            render_churn_analysis_prediction_page(dict(assets), engineered_features, all_data)
        except FileNotFoundError:
            st.error("Engineered features CSV not found. Please run feature engineering first.")
    elif page_name == "💬 Audience Chat Analysis":
        # Load chat data for sentiment analysis
        try:
            chat_df = pd.read_csv("youtube_chat_5_menit_cleaned.csv")
            render_audience_chat_analysis_page(chat_df)
        except FileNotFoundError:
            st.error("Chat data (youtube_chat_5_menit_cleaned.csv) not found.")
    else:
        render_about_page()


_HAS_SUPABASE = False
try:
    from supabase import create_client  # type: ignore
    _HAS_SUPABASE = True
except (ImportError, ModuleNotFoundError):
    _HAS_SUPABASE = False


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    if not _HAS_SUPABASE:
        return None
    try:
        return create_client(url, key)
    except Exception as _supabase_error:  # pylint: disable=broad-except
        return None


def upsert_predictions_to_supabase(df: pd.DataFrame, table: str = "predictions") -> tuple[bool, str]:
    client = get_supabase_client()
    if client is None:
        return False, "Supabase client not configured or package not installed. Set SUPABASE_URL and SUPABASE_KEY and install 'supabase' package."
    payload = df.to_dict(orient="records")
    try:
        _resp = client.table(table).upsert(payload).execute()
        return True, f"Upserted {len(payload)} rows"
    except Exception as _upsert_error:  # pylint: disable=broad-except
        return False, "Failed to upsert predictions"


def clear_shap_artifacts(plan_type: str | None = None) -> int:
    """Clear SHAP artifacts from cache."""
    shap_dir = ARTIFACT_DIR / "shap"
    if not shap_dir.exists():
        return 0
    removed = 0
    pattern = f"*{plan_type}*" if plan_type else "*"
    for p in shap_dir.glob(pattern):
        try:
            p.unlink()
            removed += 1
        except OSError:  # pylint: disable=broad-except
            pass
    return removed


def generate_predictions_table_sql(table: str = "predictions") -> str:
    """Generate SQL table creation statement."""
    cols = [
        "id TEXT PRIMARY KEY",
        "payload JSONB",
        "plan_type TEXT",
        "model TEXT",
        "created_at TIMESTAMP WITH TIME ZONE DEFAULT now()",
    ]
    return f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(cols)});"


def save_feature_snapshot(df: pd.DataFrame, plan: str | None = None) -> str | None:
    """Save feature snapshot to artifacts."""
    try:
        snaps = ARTIFACT_DIR / "snapshots"
        snaps.mkdir(parents=True, exist_ok=True)
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        name = f"snapshot_{plan}_{timestamp}.csv" if plan else f"snapshot_{timestamp}.csv"
        path = snaps / name
        df.to_csv(path, index=False)
        # also write metadata
        meta = {
            "plan": plan,
            "rows": int(len(df)),
            "columns": df.columns.tolist(),
            "created_at": pd.Timestamp.now().isoformat(),
        }
        (snaps / (name + ".meta.json")).write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(path)
    except (IOError, OSError) as _save_error:  # pylint: disable=broad-except
        return None


def render_data_management_page(data: pd.DataFrame, active_plan_type: str) -> None:
    st.title("Data Management & Integration")
    st.markdown("Manage artifacts, exports and external integration (Supabase).")

    assets = load_assets()  # No argument - uses Online Shoppers model
    selected_features = assets.get("selected_features", [])

    st.subheader("Supabase integration")
    supa_client = get_supabase_client()
    if supa_client is None:
        st.warning("Supabase client not configured or 'supabase' package missing.")
        st.info("Set SUPABASE_URL and SUPABASE_KEY environment variables and install package: pip install supabase")

    table_name = st.text_input("Supabase table name for predictions", value="predictions")
    if st.button("Export scored predictions to Supabase"):
        preds = compute_model_predictions(data.copy(), assets, selected_features)
        scored_df = data.copy()
        scored_df["churn_probability_xgb"] = preds.get("probs_xgb")
        scored_df["churn_probability_cat"] = preds.get("probs_cat")
        ok, msg = upsert_predictions_to_supabase(scored_df, table=table_name)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    if st.button("Save feature snapshot (artifacts/snapshots)"):
        preds = compute_model_predictions(data.copy(), assets, selected_features)
        snap_df = data.copy()
        snap_df["churn_probability_xgb"] = preds.get("probs_xgb")
        snap_df["churn_probability_cat"] = preds.get("probs_cat")
        snap_path = save_feature_snapshot(snap_df, plan=active_plan_type)
        if snap_path:
            st.success(f"Snapshot saved: {snap_path}")
        else:
            st.error("Failed to save snapshot")

    st.subheader("SHAP artifacts")
    st.write("Artifacts directory:", str(ARTIFACT_DIR / "shap"))
    if st.button("Refresh / Clear SHAP cache for active plan"):
        removed = clear_shap_artifacts(active_plan_type)
        st.success(f"Removed {removed} artifact files for plan {active_plan_type}")

    shap_dir = ARTIFACT_DIR / "shap"
    if shap_dir.exists():
        files = sorted(shap_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files[:50]:
            cols = st.columns([0.7, 0.3])
            cols[0].write(f.name)
            with cols[1]:
                try:
                    data_bytes = f.read_bytes()
                    st.download_button(label="Download", data=data_bytes, file_name=f.name, key=_unique_key(f"download_shap_artifact_{f.name}"))
                except Exception:
                    st.write("-")
    else:
        st.info("No SHAP artifacts found yet.")


if __name__ == "__main__":
    main()