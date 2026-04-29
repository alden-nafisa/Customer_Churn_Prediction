from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, TypedDict

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
    PLAN_TYPES,
    get_plan_slug,
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


def init_auth_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "auth_error" not in st.session_state:
        st.session_state.auth_error = ""


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
                background: radial-gradient(circle at top, #f7fbff 0%, #eef4ff 42%, #e3eef8 100%);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Customer Churn Early Warning System",
    page_icon="📉",
    layout="wide",
)


@st.cache_resource
def load_assets(plan_type: str) -> AppAssets:
    plan_slug = get_plan_slug(plan_type)
    plan_dir = ARTIFACT_DIR / "plan_models" / plan_slug
    metrics_path = ARTIFACT_DIR / "plan_model_metrics.json"
    summary = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {"plans": {}}
    metrics = summary.get("plans", {}).get(plan_type, {})

    xgb_pipeline = load_artifact(plan_dir / "xgb_pipeline.joblib")
    catboost_pipeline = load_artifact(plan_dir / "catboost_pipeline.joblib")
    return {
        "xgb_pipeline": xgb_pipeline,
        "catboost_pipeline": catboost_pipeline,
        "metrics": metrics,
        "xgb_explainer": shap.TreeExplainer(xgb_pipeline.named_steps["model"]),
        "catboost_explainer": shap.TreeExplainer(catboost_pipeline.named_steps["model"]),
        "selected_features": metrics.get("selected_features", []),
        "plan_type": plan_type,
    }


def render_login_page() -> None:
    st.markdown(
        """
        <style>
            :root {
                --brand-blue: #2f6ea8;
                --brand-blue-dark: #245582;
                --brand-blue-mid: #3d82bf;
                --brand-blue-light: #72aee0;
                --brand-blue-pale: #e8f2fb;
            }
            .stApp {
                background: radial-gradient(circle at top, #f7fbff 0%, var(--brand-blue-pale) 42%, #e3eef8 100%);
            }
            header[data-testid="stHeader"],
            [data-testid="stToolbar"],
            #MainMenu {
                visibility: hidden !important;
                display: none !important;
            }
            .login-page {
                padding-top: 2.2rem;
                padding-bottom: 3rem;
            }
            .login-shell {
                width: min(1180px, calc(100vw - 5rem));
                max-width: 1180px;
                margin: 0 auto;
                background: white;
                border-radius: 28px;
                overflow: hidden;
                box-shadow: 0 26px 60px rgba(15, 23, 42, 0.18), 0 2px 0 rgba(255, 255, 255, 0.55) inset;
                border: 1px solid rgba(15, 23, 42, 0.06);
            }
            div[data-testid="column"] {
                padding: 0 !important;
            }
            .login-left {
                position: relative;
                min-height: 560px;
                padding: 2rem;
                background:
                    radial-gradient(circle at 20% 20%, rgba(255,255,255,0.25) 0 10px, transparent 11px),
                    radial-gradient(circle at 80% 12%, rgba(255,255,255,0.18) 0 14px, transparent 15px),
                    radial-gradient(circle at 15% 78%, rgba(255,255,255,0.15) 0 18px, transparent 19px),
                    linear-gradient(135deg, var(--brand-blue-dark) 0%, var(--brand-blue) 35%, var(--brand-blue-mid) 68%, var(--brand-blue-light) 100%);
                color: white;
                isolation: isolate;
                overflow: hidden;
            }
            .login-left::before,
            .login-left::after {
                content: "";
                position: absolute;
                inset: auto;
                border-radius: 999px;
                pointer-events: none;
            }
            .login-left::before {
                width: 340px;
                height: 340px;
                top: -110px;
                right: -110px;
                background: radial-gradient(circle, rgba(255,255,255,0.26) 0%, rgba(255,255,255,0.04) 55%, transparent 70%);
                animation: floatGlow 10s ease-in-out infinite;
            }
            .login-left::after {
                width: 260px;
                height: 260px;
                left: -90px;
                bottom: -100px;
                background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.05) 60%, transparent 72%);
                animation: floatGlow 12s ease-in-out infinite reverse;
            }
            .blue-grid {
                position: absolute;
                inset: 0;
                background-image:
                    linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px);
                background-size: 42px 42px;
                opacity: 0.45;
                mask-image: linear-gradient(180deg, rgba(0,0,0,0.85), rgba(0,0,0,0.3));
                animation: gridDrift 18s linear infinite, gridPulse 6s ease-in-out infinite;
            }
            .wave {
                position: absolute;
                left: -22%;
                width: 144%;
                height: 220px;
                border-radius: 46% 54% 45% 55% / 58% 42% 58% 42%;
                filter: blur(6px);
                opacity: 0.9;
                mix-blend-mode: screen;
                z-index: 1;
                will-change: transform, opacity, background-position;
            }
            .wave.one {
                top: 10%;
                background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.24), rgba(255,255,255,0.02));
                background-size: 200% 100%;
                animation: waveOne 9s ease-in-out infinite;
            }
            .wave.two {
                top: 26%;
                background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.16), rgba(255,255,255,0.02));
                background-size: 220% 100%;
                animation: waveTwo 11s ease-in-out infinite;
            }
            .wave.three {
                bottom: 9%;
                background: linear-gradient(90deg, rgba(29, 78, 216, 0.28), rgba(255,255,255,0.16), rgba(56, 189, 248, 0.26));
                background-size: 240% 100%;
                animation: waveThree 13s ease-in-out infinite;
            }
            .orbit {
                position: absolute;
                border-radius: 50%;
                border: 1px solid rgba(255,255,255,0.28);
                box-shadow: 0 0 24px rgba(255,255,255,0.2) inset;
                animation: orbitPulse 8s ease-in-out infinite;
                z-index: 1;
            }
            .orbit.one { width: 82px; height: 82px; left: 24px; top: 78px; }
            .orbit.two { width: 120px; height: 120px; right: 40px; top: 34px; animation-delay: -2s; }
            .orbit.three { width: 68px; height: 68px; left: 54%; top: 54%; animation-delay: -4s; }
            .login-brand {
                position: relative;
                z-index: 2;
                display: flex;
                align-items: center;
                gap: 0.6rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                font-size: 0.8rem;
                text-transform: uppercase;
                opacity: 0.96;
            }
            .brand-mark {
                width: 34px;
                height: 34px;
                border-radius: 999px;
                border: 2px solid rgba(255,255,255,0.9);
                display: grid;
                place-items: center;
                font-size: 0.9rem;
                box-shadow: 0 0 0 10px rgba(255,255,255,0.08);
            }
            .login-copy {
                position: relative;
                z-index: 2;
                margin-top: 7rem;
                max-width: 420px;
            }
            .login-copy .eyebrow {
                font-size: 1rem;
                opacity: 0.9;
                margin-bottom: 0.5rem;
            }
            .login-copy h1 {
                font-size: clamp(2.5rem, 4vw, 4.4rem);
                line-height: 0.94;
                margin: 0;
                letter-spacing: -0.04em;
                text-transform: uppercase;
            }
            .login-copy .divider {
                width: 56px;
                height: 4px;
                border-radius: 999px;
                background: rgba(255,255,255,0.95);
                margin: 1rem 0 1.1rem;
            }
            .login-copy p {
                margin: 0;
                max-width: 330px;
                line-height: 1.55;
                opacity: 0.9;
                font-size: 0.95rem;
            }
            .login-right {
                min-height: 560px;
            }
            .login-title {
                font-size: 1.7rem;
                font-weight: 800;
                color: #2563eb;
                margin: 0;
                letter-spacing: -0.03em;
            }
            .login-subtitle {
                color: #6b7280;
                margin: 0.45rem 0 1.1rem;
                line-height: 1.55;
                font-size: 0.95rem;
            }
            .login-chip-row {
                display: flex;
                gap: 0.75rem;
                align-items: center;
                margin: 1.2rem 0 1.45rem;
                color: #6b7280;
                font-size: 0.88rem;
            }
            .login-chip {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 20px;
                height: 20px;
                border-radius: 999px;
                background: #e5e7eb;
                color: #6b7280;
                font-weight: 700;
            }
            .login-caption {
                color: #6b7280;
                margin-top: 0.85rem;
                font-size: 0.9rem;
            }
            .login-caption strong,
            .login-caption b {
                color: #0f172a;
            }
            .stForm {
                background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
                border-radius: 28px;
                padding: 3rem 3rem 2.6rem;
                box-shadow: 0 26px 60px rgba(15, 23, 42, 0.12), 0 1px 0 rgba(255, 255, 255, 0.8) inset;
                border: 1px solid rgba(15, 23, 42, 0.06);
                margin-top: 0;
            }
            .stTextInput label,
            .stTextInput p,
            .stTextInput span {
                color: #6b7280 !important;
                opacity: 1 !important;
            }
            .stTextInput input,
            .stTextInput textarea {
                color: #0f172a !important;
                background: white !important;
                border: 1px solid #d1d5db !important;
                border-left: 4px solid #2563eb !important;
                border-radius: 10px !important;
                box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04) !important;
            }
            div[data-testid="stTextInput"] [data-baseweb="base-input"],
            div[data-testid="stTextInput"] [data-baseweb="base-input"] > div,
            div[data-testid="stTextInput"] [data-baseweb="input"] {
                background: white !important;
                box-shadow: none !important;
                border-color: #d1d5db !important;
            }
            div[data-testid="stTextInput"] [data-baseweb="input"] input,
            div[data-testid="stTextInput"] [data-baseweb="base-input"] input {
                background: white !important;
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
                opacity: 1 !important;
            }
            div[data-testid="stTextInput"] [data-baseweb="base-input"] button,
            div[data-testid="stTextInput"] [data-baseweb="base-input"] button:hover,
            div[data-testid="stTextInput"] [data-baseweb="base-input"] button:active,
            div[data-testid="stTextInput"] [data-baseweb="base-input"] button:focus,
            div[data-testid="stTextInput"] button,
            div[data-testid="stTextInput"] button:hover,
            div[data-testid="stTextInput"] button:active,
            div[data-testid="stTextInput"] button:focus {
                background: #f3f4f6 !important;
                color: #6b7280 !important;
                fill: #6b7280 !important;
                stroke: #6b7280 !important;
                border-color: #d1d5db !important;
                box-shadow: none !important;
            }
            div[data-testid="stTextInput"] button svg,
            div[data-testid="stTextInput"] button svg * {
                fill: #6b7280 !important;
                stroke: #6b7280 !important;
            }
            div[data-testid="stForm"] button,
            div[data-testid="stForm"] button:hover,
            div[data-testid="stForm"] button:active,
            div[data-testid="stForm"] button:focus,
            div[data-testid="stForm"] button[kind="primary"],
            div[data-testid="stForm"] button[kind="primary"]:hover,
            div[data-testid="stForm"] button[kind="primary"]:active,
            div[data-testid="stForm"] button[kind="primary"]:focus {
                border-radius: 999px;
                font-weight: 700;
                background: #1f7aec !important;
                color: #ffffff !important;
                border: 1px solid #1f7aec !important;
                box-shadow: 0 14px 24px rgba(31, 122, 236, 0.22) !important;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            div[data-testid="stForm"] button:hover,
            div[data-testid="stForm"] button[kind="primary"]:hover {
                transform: translateY(-1px);
                box-shadow: 0 18px 28px rgba(31, 122, 236, 0.28) !important;
            }
            @keyframes floatGlow {
                0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
                50% { transform: translate3d(0, 18px, 0) scale(1.03); }
            }
            @keyframes waveOne {
                0%, 100% { transform: translate(-2%, 0px) scaleX(1.01) scaleY(1.00) rotate(-4deg); background-position: 0% 50%; opacity: 0.82; }
                50% { transform: translate(4%, 10px) scaleX(1.05) scaleY(1.08) rotate(-2deg); background-position: 100% 50%; opacity: 0.98; }
            }
            @keyframes waveTwo {
                0%, 100% { transform: translate(0, 0px) scaleX(1.02) scaleY(1.00) rotate(7deg); background-position: 100% 50%; opacity: 0.72; }
                50% { transform: translate(-5%, -12px) scaleX(1.08) scaleY(1.1) rotate(10deg); background-position: 0% 50%; opacity: 0.92; }
            }
            @keyframes waveThree {
                0%, 100% { transform: translate(0, 0px) scaleX(1.01) scaleY(1.00) rotate(-2deg); background-position: 0% 50%; opacity: 0.7; }
                50% { transform: translate(6%, -8px) scaleX(1.08) scaleY(1.12) rotate(2deg); background-position: 100% 50%; opacity: 0.95; }
            }
            @keyframes orbitPulse {
                0%, 100% { transform: scale(1); opacity: 0.45; }
                50% { transform: scale(1.08); opacity: 0.8; }
            }
            @keyframes gridDrift {
                0% { background-position: 0 0; }
                100% { background-position: 84px 42px; }
            }
            @keyframes gridPulse {
                0%, 100% { opacity: 0.34; }
                50% { opacity: 0.56; }
            }
            @media (max-width: 900px) {
                .login-shell {
                    width: min(100vw - 1.5rem, 1180px);
                }
                .login-left {
                    min-height: 360px;
                }
                .login-copy {
                    margin-top: 6rem;
                }
                .login-right {
                    padding: 2rem 1.5rem 2.2rem;
                    min-height: auto;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-page">', unsafe_allow_html=True)
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    left_col, right_col = st.columns([1.0, 1.0])

    with left_col:
        st.markdown(
            """
            <div class="login-left">
                <div class="blue-grid"></div>
                <div class="wave one"></div>
                <div class="wave two"></div>
                <div class="wave three"></div>
                <div class="orbit one"></div>
                <div class="orbit two"></div>
                <div class="orbit three"></div>
                <div class="login-brand"><div class="brand-mark">◎</div><span>Company Name</span></div>
                <div class="login-copy">
                    <div class="eyebrow">Nice to see you again</div>
                    <h1>WELCOME BACK</h1>
                    <div class="divider"></div>
                    <p>Masuk untuk membuka dashboard churn dengan tampilan yang lebih tenang, modern, dan fokus pada analisis.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        with st.form("login_form", clear_on_submit=False):
            st.markdown('<div class="login-title">Login Account</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">Masukkan username dan password yang valid untuk membuka dashboard analisis churn.</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-chip-row"><span class="login-chip">✓</span><span>Keep me signed in</span><span style="margin-left:auto; color:#6b7280; font-weight:600;">Already a member?</span></div>', unsafe_allow_html=True)
            username = st.text_input("Email ID", placeholder="Admin123")
            password = st.text_input("Password", type="password", placeholder="12345678")
            submitted = st.form_submit_button("SUBSCRIBE", use_container_width=True)

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
            f'<div class="login-caption">Credential demo: username <strong>{AUTH_USERNAME}</strong> dan password <strong>{AUTH_PASSWORD}</strong>.</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return


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
        color_continuous_scale="Greys",
        title="Top customers by churn probability",
    )
    fig.update_layout(height=450, margin=dict(l=10, r=10, t=55, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)


def show_model_comparison(metrics: MetricsBundle, plan_type: str) -> None:
    comparison = pd.DataFrame([
        {"model": "XGBoost", **metrics["xgboost"]},
        {"model": "CatBoost", **metrics["catboost"]},
    ])
    display = comparison[["model", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]].copy()
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
    st.plotly_chart(fig, use_container_width=True)

    selected_customer = render_customer_navigator(scored[ID_COLUMN].tolist())
    st.caption(f"Selected customer: {selected_customer}")
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
    st.plotly_chart(local_fig, use_container_width=True)

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
        "value": config["default_value"],
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
    st.plotly_chart(shap_fig, use_container_width=True)

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

    transformed = transform_features(pipeline, feature_frame)
    explanation = explainer(transformed)
    feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    row_values = explanation.values[0]

    local_df = pd.DataFrame({"feature": feature_names, "shap_value": row_values})
    return local_df.sort_values("shap_value", key=lambda s: np.abs(s), ascending=False).head(10).sort_values("shap_value")


def render_predict_page(data: pd.DataFrame, active_plan_type: str, selected_model_name: str, threshold: float) -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Customer Churn Quick Prediction</h1>
            <p>Prediksi cepat dengan model terpisah per plan type agar routing risiko lebih jelas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    assets = load_assets(active_plan_type)
    selected_features = assets["selected_features"]
    defaults = build_feature_defaults(data, selected_features)
    categorical_options = {
        column: sorted(data[column].dropna().astype(str).unique().tolist())
        for column in selected_features
        if column in data.columns and not pd.api.types.is_numeric_dtype(data[column])
    }

    st.markdown(
        f'<div class="dashboard-note">Model aktif saat ini: <strong>{active_plan_type}</strong>. Pilih mode yang sesuai: input manual atau customer existing.</div>',
        unsafe_allow_html=True,
    )
    mode = st.radio("Predict mode", ["Predict Input", "Existing Customer"], horizontal=True, index=0)

    if mode == "Predict Input":
        with st.form("customer_prediction_form"):
            left_col, right_col = st.columns([1, 1])
            form_values: dict[str, Any] = {}

            with left_col:
                st.markdown("##### Profil")
                plan_type_for_input = st.selectbox("Plan Type", PLAN_TYPES, index=PLAN_TYPES.index(active_plan_type))
                if "tenure_months" in selected_features:
                    config = get_numeric_field_config(data, "tenure_months", defaults)
                    form_values["tenure_months"] = st.number_input("Tenure (months)", **build_number_input_kwargs(config))

                if "contract_type" in selected_features:
                    contract_options = categorical_options.get("contract_type", [str(defaults.get("contract_type", ""))])
                    default_contract = defaults.get("contract_type", contract_options[0])
                    default_index = contract_options.index(default_contract) if default_contract in contract_options else 0
                    form_values["contract_type"] = st.selectbox("Contract Type", contract_options, index=default_index)

                if "monthly_usage_hrs" in selected_features:
                    config = get_numeric_field_config(data, "monthly_usage_hrs", defaults)
                    form_values["monthly_usage_hrs"] = st.number_input("Monthly Usage Hours", **build_number_input_kwargs(config))

            with right_col:
                st.markdown("##### Aktivitas")
                if "last_login_days_ago" in selected_features:
                    config = get_numeric_field_config(data, "last_login_days_ago", defaults)
                    form_values["last_login_days_ago"] = st.number_input("Days Since Last Login", **build_number_input_kwargs(config))

                if "nps_score" in selected_features:
                    config = get_numeric_field_config(data, "nps_score", defaults)
                    form_values["nps_score"] = st.number_input("NPS Score", **build_number_input_kwargs(config))

                if "feature_adoption_pct" in selected_features:
                    config = get_numeric_field_config(data, "feature_adoption_pct", defaults)
                    form_values["feature_adoption_pct"] = st.number_input("Feature Adoption %", **build_number_input_kwargs(config))

                if "support_tickets_last_90d" in selected_features:
                    config = get_numeric_field_config(data, "support_tickets_last_90d", defaults)
                    form_values["support_tickets_last_90d"] = st.number_input("Support Tickets / 90 days", **build_number_input_kwargs(config))

                if "payment_delay_count" in selected_features:
                    config = get_numeric_field_config(data, "payment_delay_count", defaults)
                    form_values["payment_delay_count"] = st.number_input("Payment Delay Count", **build_number_input_kwargs(config))

            st.caption("Nilai di luar rentang training tetap bisa diproses, tetapi hasilnya bisa kurang stabil.")
            submitted = st.form_submit_button("Hitung Risiko", use_container_width=True)

        if not submitted:
            st.info("Isi form lalu klik Hitung Risiko.")
            return

        input_frame = build_manual_input_row(data, selected_features, form_values)
        input_frame.insert(0, ID_COLUMN, "SIMULASI-001")
        input_assets = load_assets(plan_type_for_input)
        render_single_prediction_result(
            input_frame,
            data,
            input_assets,
            input_assets["selected_features"],
            selected_model_name,
            threshold,
            plan_type_for_input,
        )
        st.markdown(
            '<div class="dashboard-note">Mode ini untuk simulasi cepat. Advanced Analysis dipakai untuk eksplorasi data per plan.</div>',
            unsafe_allow_html=True,
        )
        return

    customer_ids = data[ID_COLUMN].astype(str).tolist()
    selected_customer_id = st.selectbox(
        "Existing customer",
        options=customer_ids,
        index=0,
        help="Pilih customer yang sudah ada untuk dicek risikonya.",
    )

    customer_row = data.loc[data[ID_COLUMN].astype(str) == str(selected_customer_id)].head(1).copy()
    if customer_row.empty:
        st.warning("Customer ID tidak ditemukan di dataset saat ini.")
        return

    st.markdown("##### Customer Summary")
    left_col, right_col = st.columns([1.05, 0.95])
    with left_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Sentiment Model Performance</div>', unsafe_allow_html=True)
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
                    f"dataset={label_strategy.get('dataset', '-')}.")
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
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Session Summary</div>', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

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
    )

    show_model_comparison(assets["metrics"], active_plan_type)

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


def main() -> None:
    init_auth_state()
    add_branding()

    if not st.session_state.authenticated:
        render_login_page()
        return

    render_logout_button()

    nlp_assets = load_nlp_assets()
    data = load_source_data()
    page_name = st.sidebar.radio("Dashboard page", ["Predict", "Advanced Analysis"], index=0)
    active_plan_type = st.sidebar.selectbox("Active plan model", PLAN_TYPES, index=0)
    selected_model_name = st.sidebar.radio("Scoring model", ["XGBoost", "CatBoost"], index=0)
    threshold = st.sidebar.slider("Risk threshold", min_value=0.10, max_value=0.90, value=0.50, step=0.05)

    active_assets = load_assets(active_plan_type)
    selected_features = active_assets["selected_features"]
    st.sidebar.caption("Label churn historis dipakai hanya sebagai ground truth. Model memprediksi tanpa melihat kolom churned. Setiap plan punya model sendiri dan dashboard akan mengikuti plan aktif.")
    st.sidebar.success(f"Active plan model: {active_plan_type}")
    if selected_features:
        st.sidebar.caption(f"Auto-selected features: {len(selected_features)}")
        st.sidebar.caption(", ".join(selected_features))
    if page_name == "Predict":
        render_predict_page(data, active_plan_type, selected_model_name, threshold)
    else:
        render_advanced_analysis_page(data, nlp_assets, active_plan_type, selected_model_name, threshold)


if __name__ == "__main__":
    main()