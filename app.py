from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import shap
import streamlit as st

from src.churn_pipeline import (
    ARTIFACT_DIR,
    DATA_PATH,
    ID_COLUMN,
    load_artifact,
    load_dataset,
    transform_features,
)

TARGET_COLUMN = "churned"
AUTH_USERNAME = "Admin123"
AUTH_PASSWORD = "12345678"
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
    logistic_regression: ModelMetrics
    xgboost: ModelMetrics
    feature_names: list[str]
    selected_features: list[str]
    feature_columns: dict[str, list[str]]


class AppAssets(TypedDict):
    logistic_pipeline: Any
    xgb_pipeline: Any
    metrics: MetricsBundle
    xgb_explainer: Any
    selected_features: list[str]


class NLPAssets(TypedDict):
    sentiment_metrics: dict[str, Any]
    sentiment_test_predictions: pd.DataFrame
    session_summary: dict[str, Any]
    session_summary_text: str

st.set_page_config(
    page_title="Customer Churn Early Warning System",
    page_icon="📉",
    layout="wide",
)


@st.cache_resource
def load_assets() -> AppAssets:
    logistic_pipeline = load_artifact(ARTIFACT_DIR / "logistic_pipeline.joblib")
    xgb_pipeline = load_artifact(ARTIFACT_DIR / "xgb_pipeline.joblib")
    metrics = json.loads((ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))
    return {
        "logistic_pipeline": logistic_pipeline,
        "xgb_pipeline": xgb_pipeline,
        "metrics": metrics,
        "xgb_explainer": shap.TreeExplainer(xgb_pipeline.named_steps["model"]),
        "selected_features": metrics.get("selected_features", []),
    }


@st.cache_data
def load_source_data() -> pd.DataFrame:
    return load_dataset(DATA_PATH)


@st.cache_data
def load_nlp_assets() -> NLPAssets:
    sentiment_metrics_path = NLP_ARTIFACT_DIR / "sentiment_metrics.json"
    sentiment_predictions_path = NLP_ARTIFACT_DIR / "sentiment_test_predictions.csv"
    session_summary_path = NLP_ARTIFACT_DIR / "session_summary.json"
    session_summary_text_path = NLP_ARTIFACT_DIR / "session_summary.txt"

    sentiment_metrics = json.loads(sentiment_metrics_path.read_text(encoding="utf-8")) if sentiment_metrics_path.exists() else {}
    sentiment_predictions = pd.read_csv(sentiment_predictions_path) if sentiment_predictions_path.exists() else pd.DataFrame()
    session_summary = json.loads(session_summary_path.read_text(encoding="utf-8")) if session_summary_path.exists() else {}
    session_summary_text = session_summary_text_path.read_text(encoding="utf-8") if session_summary_text_path.exists() else ""

    return {
        "sentiment_metrics": sentiment_metrics,
        "sentiment_test_predictions": sentiment_predictions,
        "session_summary": session_summary,
        "session_summary_text": session_summary_text,
    }


def add_branding() -> None:
    st.markdown(
        """
        <style>
            .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
            .hero {
                background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #06b6d4 100%);
                color: white;
                border-radius: 18px;
                padding: 1.4rem 1.6rem;
                margin-bottom: 1.25rem;
                box-shadow: 0 10px 30px rgba(15, 23, 42, 0.25);
            }
            .hero h1 { margin: 0; font-size: 2rem; }
            .hero p { margin: 0.35rem 0 0; opacity: 0.92; }
            .kpi-card {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 1rem 1rem 0.85rem;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
            }
            .dashboard-note,
            .dashboard-note p,
            .dashboard-note li,
            .dashboard-note span {
                color: var(--text-color);
                opacity: 1;
            }
            .dashboard-note {
                background: var(--secondary-background-color);
                border: 1px solid rgba(148, 163, 184, 0.28);
                border-left: 4px solid #2563eb;
                border-radius: 14px;
                padding: 0.85rem 1rem;
                margin: 0.9rem 0 1rem;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
            }
            .dashboard-note strong,
            .dashboard-note b {
                color: var(--text-color);
            }
            .stCaption,
            .stMarkdown p,
            .stMarkdown li {
                color: var(--text-color);
                opacity: 1;
            }
            .stAlert {
                color: var(--text-color);
            }
            .stSidebar .stCaption,
            .stSidebar p,
            .stSidebar li,
            .stSidebar label,
            .stSidebar span {
                color: var(--text-color);
                opacity: 1;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_auth_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "auth_error" not in st.session_state:
        st.session_state.auth_error = ""


def authenticate_user(username: str, password: str) -> bool:
    return username == AUTH_USERNAME and password == AUTH_PASSWORD


def render_login_page() -> None:
    st.markdown(
        """
        <style>
            .login-card {
                background: var(--secondary-background-color);
                border: 1px solid rgba(148, 163, 184, 0.28);
                border-radius: 18px;
                padding: 0;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
            }
            .login-title {
                font-size: 1.6rem;
                font-weight: 700;
                color: var(--text-color);
                margin: 0;
            }
            .login-subtitle {
                color: var(--text-color);
                opacity: 0.82;
                margin: 0.4rem 0 0.85rem;
            }
            .login-caption {
                color: var(--text-color);
                opacity: 0.75;
                margin-top: 0.85rem;
            }
            .login-caption strong,
            .login-caption b {
                color: var(--text-color);
                opacity: 1;
            }
            .stTextInput label,
            .stTextInput p,
            .stTextInput span {
                color: var(--text-color) !important;
                opacity: 1 !important;
            }
            .stTextInput input,
            .stTextInput textarea {
                color: var(--text-color) !important;
            }
            .stButton button {
                border-radius: 12px;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.5, 1])
    with center:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Login to Dashboard</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-subtitle">Masukkan username dan password yang valid untuk membuka dashboard analisis churn.</div>',
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.auth_error = ""
                st.rerun()
            else:
                st.session_state.auth_error = "Username atau password salah."

        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)

        st.markdown(
            f'<div class="login-caption">Credential demo: username {AUTH_USERNAME} dan password {AUTH_PASSWORD}.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


def render_logout_button() -> None:
    st.sidebar.markdown("### Session")
    st.sidebar.success(f"Logged in as {AUTH_USERNAME}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.auth_error = ""
        st.rerun()


def filter_data(frame: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filter Data")

    plan_types = sorted(frame["plan_type"].unique().tolist())
    contract_types = sorted(frame["contract_type"].unique().tolist())
    churn_filters = ["Semua", "Churn", "Tidak Churn"]

    selected_plans = st.sidebar.multiselect("Plan Type", plan_types, default=plan_types)
    selected_contracts = st.sidebar.multiselect("Contract Type", contract_types, default=contract_types)
    selected_churn_status = st.sidebar.radio("Actual churn status", churn_filters, index=0)

    with st.sidebar.expander("Advanced filters", expanded=False):
        tenure_min, tenure_max = int(frame["tenure_months"].min()), int(frame["tenure_months"].max())
        revenue_min, revenue_max = float(frame["monthly_revenue"].min()), float(frame["monthly_revenue"].max())
        login_min, login_max = int(frame["last_login_days_ago"].min()), int(frame["last_login_days_ago"].max())
        nps_min, nps_max = int(frame["nps_score"].min()), int(frame["nps_score"].max())
        feature_min, feature_max = float(frame["feature_adoption_pct"].min()), float(frame["feature_adoption_pct"].max())
        tickets_min, tickets_max = int(frame["support_tickets_last_90d"].min()), int(frame["support_tickets_last_90d"].max())
        payment_min, payment_max = int(frame["payment_delay_count"].min()), int(frame["payment_delay_count"].max())

        tenure_range = st.slider("Tenure (months)", tenure_min, tenure_max, (tenure_min, tenure_max))
        revenue_range = st.slider(
            "Monthly Revenue",
            min_value=float(revenue_min),
            max_value=float(revenue_max),
            value=(float(revenue_min), float(revenue_max)),
        )
        login_range = st.slider("Days Since Last Login", login_min, login_max, (login_min, login_max))
        nps_range = st.slider("NPS Score", nps_min, nps_max, (nps_min, nps_max))
        feature_range = st.slider(
            "Feature Adoption %",
            min_value=float(feature_min),
            max_value=float(feature_max),
            value=(float(feature_min), float(feature_max)),
        )
        tickets_range = st.slider("Support tickets / 90 days", tickets_min, tickets_max, (tickets_min, tickets_max))
        payment_range = st.slider("Payment delay count", payment_min, payment_max, (payment_min, payment_max))

    filtered = frame[
        frame["plan_type"].isin(selected_plans)
        & frame["contract_type"].isin(selected_contracts)
        & frame["tenure_months"].between(*tenure_range)
        & frame["monthly_revenue"].between(*revenue_range)
        & frame["last_login_days_ago"].between(*login_range)
        & frame["nps_score"].between(*nps_range)
        & frame["feature_adoption_pct"].between(*feature_range)
        & frame["support_tickets_last_90d"].between(*tickets_range)
        & frame["payment_delay_count"].between(*payment_range)
    ].copy()

    if selected_churn_status == "Churn":
        filtered = filtered[filtered[TARGET_COLUMN] == 1]
    elif selected_churn_status == "Tidak Churn":
        filtered = filtered[filtered[TARGET_COLUMN] == 0]

    return filtered


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
        ("Customers in view", len(scored)),
        ("High-risk customers", high_risk),
        ("Average churn probability", f"{avg_prob:.2%}"),
        ("Highest churn probability", f"{max_prob:.2%}"),
    ]
    for col, (label, value) in zip(cols, metrics, strict=False):
        with col:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.metric(label, value)
            st.markdown('</div>', unsafe_allow_html=True)
    st.caption(f"Median churn probability in the current view: {median_prob:.2%}")


def plot_risk_distribution(scored: pd.DataFrame, threshold: float) -> None:
    fig = px.histogram(
        scored,
        x="churn_probability",
        nbins=24,
        color_discrete_sequence=["#2563eb"],
        title="Distribution of churn probability",
    )
    fig.add_vline(x=threshold, line_dash="dash", line_color="#ef4444", annotation_text="Threshold")
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True)


def plot_top_risks(scored: pd.DataFrame) -> None:
    top_risk = scored.head(15).copy()
    top_risk["customer_short"] = top_risk[ID_COLUMN]
    fig = px.bar(
        top_risk.sort_values("churn_probability", ascending=True),
        x="churn_probability",
        y="customer_short",
        orientation="h",
        color="churn_probability",
        color_continuous_scale="Reds",
        title="Top customers by churn probability",
    )
    fig.update_layout(height=450, margin=dict(l=10, r=10, t=55, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)


def show_model_comparison(metrics: MetricsBundle) -> None:
    comparison = pd.DataFrame(
        [
            {"model": "Logistic Regression", **metrics["logistic_regression"]},
            {"model": "XGBoost", **metrics["xgboost"]},
        ]
    )
    display = comparison[["model", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]].copy()
    display.columns = ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC AUC", "PR AUC"]
    st.subheader("Model comparison")
    st.dataframe(display.style.format({col: "{:.3f}" for col in display.columns[1:]}), use_container_width=True)


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

    if "payment_delay" in driver or row["payment_delay_count"] >= medians.get("payment_delay_count", row["payment_delay_count"]):
        return "Prioritaskan follow-up penagihan dan tawarkan opsi pembayaran yang lebih fleksibel."
    if "support_tickets" in driver or row["support_tickets_last_90d"] >= medians.get("support_tickets_last_90d", row["support_tickets_last_90d"]):
        return "Lakukan eskalasi support dan periksa akar masalah yang berulang."
    if "last_login" in driver or row["last_login_days_ago"] >= medians.get("last_login_days_ago", row["last_login_days_ago"]):
        return "Jalankan re-engagement untuk pelanggan yang mulai jarang login."
    if "feature_adoption" in driver or row["feature_adoption_pct"] <= medians.get("feature_adoption_pct", row["feature_adoption_pct"]):
        return "Berikan onboarding lanjutan dan edukasi fitur untuk meningkatkan adopsi produk."
    if "nps" in driver or row["nps_score"] <= medians.get("nps_score", row["nps_score"]):
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

    transformed = transform_features(xgb_pipeline, feature_frame)
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

    return global_df, export_df


def build_explanation_summary(scored: pd.DataFrame, assets: AppAssets, model_name: str, threshold: float) -> str:
    metrics_key = {
        "XGBoost": "xgboost",
        "Logistic Regression": "logistic_regression",
    }.get(model_name, "xgboost")
    model_metrics = assets["metrics"][metrics_key]

    actual_churn = int((scored[TARGET_COLUMN] == 1).sum())
    predicted_churn = int((scored["predicted_churn_label"] == "Churn").sum())
    high_risk = int((scored["risk_flag"] == "High Risk").sum())
    match_rate = float((scored["match_flag"] == "Cocok").mean()) if len(scored) else 0.0

    return f"""### Ringkasan Risiko
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
    st.plotly_chart(fig, use_container_width=True)

    selected_customer = st.selectbox(
        "Customer for local explanation",
        options=scored[ID_COLUMN].tolist(),
        index=0,
    )
    row = scored.loc[scored[ID_COLUMN] == selected_customer].head(1).copy().reset_index(drop=True)
    row_features = row.drop(columns=[ID_COLUMN, TARGET_COLUMN, "churn_probability", "risk_flag", "risk_rank", "actual_churn_label", "predicted_churn_label", "match_flag"], errors="ignore")
    if selected_features:
        row_features = row_features[[column for column in selected_features if column in row_features.columns]].copy()
    row_transformed = transform_features(xgb_pipeline, row_features)
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
    bar_colors = np.where(local_top["shap_value"] >= 0, "#dc2626", "#2563eb")
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
    st.plotly_chart(local_fig, use_container_width=True)

    probability = float(row["churn_probability"].iloc[0])
    st.info(
        f"Predicted churn probability for {selected_customer}: {probability:.2%}. "
        f"Positive SHAP values push the customer toward churn; negative values reduce risk."
    )


def recommendation_text(scored: pd.DataFrame) -> str:
    if scored.empty:
        return "Tidak ada data yang dapat dianalisis setelah filter diterapkan."

    return "\n".join(f"- {item}" for item in derive_actions(scored))


def render_nlp_section(nlp_assets: NLPAssets) -> None:
    st.subheader("NLP: Sentiment Analysis dan Session Summary")
    st.markdown(
        '<div class="dashboard-note">Bagian NLP memakai komentar sebagai input. Kolom sentiment pada CSV tidak dipakai sebagai fitur; label training dibentuk otomatis dari isi komentar.</div>',
        unsafe_allow_html=True,
    )

    sentiment_metrics = nlp_assets["sentiment_metrics"]
    sentiment_predictions = nlp_assets["sentiment_test_predictions"]
    session_summary = nlp_assets["session_summary"]
    session_summary_text = nlp_assets["session_summary_text"]

    left_col, right_col = st.columns([1.05, 0.95])
    with left_col:
        st.markdown("##### Sentiment Model Performance")
        if sentiment_metrics:
            nb_values = sentiment_metrics.get("naive_bayes", {})
            sentiment_display = pd.DataFrame(
                [
                    {
                        "Model": "Naive Bayes",
                        "Accuracy": nb_values.get("accuracy", 0.0),
                        "Precision (macro)": nb_values.get("precision_macro", 0.0),
                        "Recall (macro)": nb_values.get("recall_macro", 0.0),
                        "F1 (macro)": nb_values.get("f1_macro", 0.0),
                    }
                ]
            )
            st.dataframe(
                sentiment_display.style.format(
                    {
                        "Accuracy": "{:.3f}",
                        "Precision (macro)": "{:.3f}",
                        "Recall (macro)": "{:.3f}",
                        "F1 (macro)": "{:.3f}",
                    }
                ),
                use_container_width=True,
                height=220,
            )
            label_strategy = sentiment_metrics.get("label_strategy", {})
            if label_strategy:
                st.caption(
                    "Training NLP memakai komentar saja dengan weak supervision: "
                    f"source={label_strategy.get('source', '-')}, "
                    f"method={label_strategy.get('label_method', '-')}, "
                    f"dataset={label_strategy.get('dataset', '-')}."
                )
        else:
            st.info("Artifact sentiment belum ditemukan.")

        if not sentiment_predictions.empty:
            with st.expander("Preview sentiment test predictions", expanded=False):
                st.dataframe(sentiment_predictions.head(12), use_container_width=True, height=240)
                st.download_button(
                    label="Download sentiment test predictions",
                    data=sentiment_predictions.to_csv(index=False).encode("utf-8"),
                    file_name="sentiment_test_predictions.csv",
                    mime="text/csv",
                )

    with right_col:
        st.markdown("##### Session Summary")
        if session_summary:
            metric_cols = st.columns(2)
            with metric_cols[0]:
                st.metric("Total comments", session_summary.get("total_comments", 0))
            with metric_cols[1]:
                unique_commenters = session_summary.get("unique_commenters")
                st.metric("Unique commenters", unique_commenters if unique_commenters is not None else "-")

            if session_summary_text:
                st.text_area("Extractive session summary", value=session_summary_text, height=220)

            top_keywords = session_summary.get("top_keywords", [])
            if top_keywords:
                st.markdown("**Top keywords**")
                st.dataframe(pd.DataFrame(top_keywords), use_container_width=True, height=200)

            representative_comments = session_summary.get("representative_comments", [])
            if representative_comments:
                with st.expander("Representative comments", expanded=False):
                    st.dataframe(pd.DataFrame(representative_comments), use_container_width=True, height=240)

            st.download_button(
                label="Download session summary JSON",
                data=json.dumps(session_summary, indent=2, ensure_ascii=False).encode("utf-8"),
                file_name="session_summary.json",
                mime="application/json",
            )
        else:
            st.info("Artifact session summary belum ditemukan.")


def main() -> None:
    init_auth_state()
    add_branding()

    if not st.session_state.authenticated:
        render_login_page()
        return

    render_logout_button()

    assets = load_assets()
    nlp_assets = load_nlp_assets()
    data = load_source_data()
    selected_features = assets["selected_features"]

    st.markdown(
        """
        <div class="hero">
            <h1>Customer Churn Early Warning Dashboard</h1>
            <p>Prediksi risiko churn, bandingkan Logistic Regression dan XGBoost, lalu jelaskan alasan model dengan SHAP.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.header("Scoring Settings")
    selected_model_name = st.sidebar.radio("Scoring model", ["XGBoost", "Logistic Regression"], index=0)
    threshold = st.sidebar.slider("Risk threshold", min_value=0.10, max_value=0.90, value=0.50, step=0.05)
    st.sidebar.caption("Label churn historis dipakai hanya sebagai ground truth. Model memprediksi tanpa melihat kolom churned. Training memakai split stratified 80/20 dan SMOTE di data training.")
    if selected_features:
        st.sidebar.success(f"Auto-selected features: {len(selected_features)}")
        st.sidebar.caption(", ".join(selected_features))

    filtered = filter_data(data)
    if filtered.empty:
        st.warning("Tidak ada data yang cocok dengan filter saat ini.")
        return

    pipeline_key = {
        "XGBoost": "xgb_pipeline",
        "Logistic Regression": "logistic_pipeline",
    }[selected_model_name]
    pipeline = assets[pipeline_key]
    scored = score_frame(pipeline, filtered, threshold, selected_features)
    global_shap_df, explanation_export = build_shap_summary(
        scored,
        assets["xgb_pipeline"],
        assets["xgb_explainer"],
        selected_features,
    )

    st.markdown(
        '<div class="dashboard-note">Sistem klasifikasi: 80% data dipakai untuk training dan 20% untuk testing. SMOTE diterapkan pada data training. Kolom churned adalah label aktual, bukan input model.</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Penjelasan Risiko")
    st.markdown(build_explanation_summary(scored, assets, selected_model_name, threshold))

    if not global_shap_df.empty:
        st.caption("Faktor global yang paling sering mendorong churn pada view ini")
        st.dataframe(
            global_shap_df.style.format({"mean_abs_shap": "{:.4f}"}),
            use_container_width=True,
            height=260,
        )

    st.download_button(
        label="Download explanation CSV",
        data=explanation_export.to_csv(index=False).encode("utf-8"),
        file_name="churn_explanation_summary.csv",
        mime="text/csv",
    )

    if selected_features:
        st.subheader("Fitur yang dipilih otomatis")
        st.write(
            "Model ini tidak memakai pilihan manual admin. Fitur berikut dipilih otomatis dari hasil training dan akan dipakai konsisten oleh pipeline."
        )
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
    st.dataframe(
        scored[display_columns].style.format(
            {
                "monthly_revenue": "{:.2f}",
                "churn_probability": "{:.2%}",
            }
        ),
        use_container_width=True,
        height=380,
    )

    st.download_button(
        label="Download scored data",
        data=scored.to_csv(index=False).encode("utf-8"),
        file_name="churn_scored_customers.csv",
        mime="text/csv",
    )

    show_model_comparison(assets["metrics"])

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

    if selected_model_name == "XGBoost":
        explain_with_shap(scored, assets["xgb_pipeline"], assets["xgb_explainer"], selected_features)
    else:
        st.info("Panel SHAP tetap menggunakan model XGBoost karena pendekatan XAI pada proyek ini berfokus pada tree-based model utama.")
        explain_with_shap(scored, assets["xgb_pipeline"], assets["xgb_explainer"], selected_features)

    st.subheader("Retained action suggestion")
    st.success(recommendation_text(scored))

    render_nlp_section(nlp_assets)


if __name__ == "__main__":
    main()