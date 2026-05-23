from __future__ import annotations

import ast
import json
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENGINEERED_FEATURES_PATH = PROJECT_ROOT / "engineered_features" / "lapisai_engineered_features.csv"
ENSEMBLE_PREDICTIONS_PATH = PROJECT_ROOT / "model_results" / "ensemble_predictions.csv"
EVALUATION_METRICS_PATH = PROJECT_ROOT / "model_results" / "evaluation_metrics.csv"
PREPROCESSED_DIR = PROJECT_ROOT / "preprocessed_data"
TRAINED_MODELS_DIR = PROJECT_ROOT / "trained_models" / "plan_specific"
CHAT_DATA_PATH = PROJECT_ROOT / "youtube_chat_5_menit_cleaned.csv"
SESSION_SUMMARY_PATH = PROJECT_ROOT / "artifacts" / "nlp" / "session_summary.txt"

FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app = FastAPI(title="Customer Churn API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class PredictRequest(BaseModel):
    customer_id: str
    plan_type: str
    model_choice: Literal["XGBoost Only", "CatBoost Only", "Ensemble (Recommended)"] = "Ensemble (Recommended)"
    overrides: Dict[str, float] = Field(default_factory=dict)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return pd.read_csv(path)


@lru_cache(maxsize=1)
def load_engineered_df() -> pd.DataFrame:
    return _read_csv(ENGINEERED_FEATURES_PATH)


@lru_cache(maxsize=1)
def load_ensemble_df() -> pd.DataFrame:
    return _read_csv(ENSEMBLE_PREDICTIONS_PATH)


@lru_cache(maxsize=1)
def load_eval_df() -> pd.DataFrame:
    return _read_csv(EVALUATION_METRICS_PATH)


@lru_cache(maxsize=1)
def load_chat_df() -> pd.DataFrame:
    return _read_csv(CHAT_DATA_PATH)


@lru_cache(maxsize=1)
def load_preprocessing_info() -> Dict[str, List[str]]:
    info: Dict[str, List[str]] = {}
    for plan in ("starter", "professional", "enterprise"):
        info_path = PREPROCESSED_DIR / f"{plan}_preprocessing_info.json"
        if not info_path.exists():
            continue
        data = json.loads(info_path.read_text(encoding="utf-8"))
        features = ast.literal_eval(data.get("features_selected", "[]"))
        info[plan.capitalize()] = [str(x) for x in features]
    return info


@lru_cache(maxsize=6)
def load_models(plan_type: str) -> Dict[str, Any]:
    models: Dict[str, Any] = {}
    plan = plan_type.strip().lower()
    for name in ("xgboost", "catboost"):
        path = TRAINED_MODELS_DIR / f"{plan}_{name}.pkl"
        if path.exists():
            with path.open("rb") as f:
                models[name] = pickle.load(f)
    return models


def normalize_plan(plan_type: str) -> str:
    plan = plan_type.strip().lower()
    if plan == "starter":
        return "Starter"
    if plan == "professional":
        return "Professional"
    if plan == "enterprise":
        return "Enterprise"
    return plan_type.strip().title()


def selected_features_for_plan(plan_type: str) -> List[str]:
    info = load_preprocessing_info()
    plan = normalize_plan(plan_type)
    if plan in info:
        return info[plan]
    for key, value in info.items():
        if key.lower() == plan.lower():
            return value
    raise HTTPException(status_code=404, detail=f"No training features found for plan: {plan_type}")


def apply_overrides(row: pd.Series, overrides: Dict[str, float]) -> pd.Series:
    mapping = {
        "payment_delay_days": "payment_delay_days_mean",
        "days_since_login": "days_since_last_login",
        "avg_nps_score": "avg_nps_score",
        "feature_adoption_pct": "feature_adoption_pct_mean",
        "annual_value": "annual_value",
        "avg_monthly_usage_hours": "avg_monthly_usage_hours",
        "total_tickets": "total_tickets",
        "payment_health_score": "payment_health_score",
    }
    updated = row.copy()
    for key, value in overrides.items():
        col = mapping.get(key, key)
        if col in updated.index:
            updated[col] = value
    return updated


def risk_label(prob: float) -> str:
    if prob > 0.7:
        return "VERY HIGH"
    if prob > 0.5:
        return "HIGH"
    if prob > 0.3:
        return "MEDIUM"
    return "LOW"


def evaluation_label(actual: int, predicted: int) -> tuple[str, str]:
    if actual == 1 and predicted == 1:
        return "TRUE_POSITIVE", "Model correctly identified this customer as churned."
    if actual == 0 and predicted == 0:
        return "TRUE_NEGATIVE", "Model correctly predicted this customer will be retained."
    if actual == 1 and predicted == 0:
        return "FALSE_NEGATIVE", "Model missed this churn case."
    return "FALSE_POSITIVE", "Model predicted churn but customer actually retained."


def compute_risk_factors(row: pd.Series) -> List[Dict[str, Any]]:
    candidates = []
    names = [
        ("Days Since Login", "days_since_last_login", True),
        ("Payment Delay Days", "payment_delay_days_mean", True),
        ("Critical Ticket Ratio", "critical_ticket_ratio", True),
        ("Unresolved Ratio", "unresolved_ratio", True),
        ("Revenue at Risk", "revenue_at_risk", True),
        ("Avg NPS Score", "avg_nps_score", False),
        ("Feature Adoption %", "feature_adoption_pct_mean", False),
        ("Payment Health Score", "payment_health_score", False),
        ("Monthly Usage Hours", "avg_monthly_usage_hours", False),
    ]
    for label, col, higher_is_riskier in names:
        if col not in row.index or pd.isna(row[col]):
            continue
        value = float(row[col])
        score = value if higher_is_riskier else -value
        candidates.append({"label": label, "value": value, "score": score})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:3]


def get_plan_summary() -> Dict[str, Any]:
    engine = load_engineered_df()
    plans = sorted(engine["plan_type"].dropna().astype(str).str.capitalize().unique().tolist())
    items = []
    for plan in plans:
        plan_df = engine[engine["plan_type"].astype(str).str.capitalize() == plan].copy()
        churned = int(plan_df["churned"].sum())
        total = int(len(plan_df))
        items.append(
            {
                "plan": plan,
                "total_customers": total,
                "churned": churned,
                "retained": total - churned,
                "churn_rate": round((churned / total) if total else 0, 4),
            }
        )
    return {"plans": items}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def api_auth_login(payload: LoginRequest) -> Dict[str, Any]:
    if not payload.username.strip() or not payload.password.strip():
        raise HTTPException(status_code=400, detail="Username and password are required")
    return {
        "token": "mock-jwt-token",
        "user": {
            "username": payload.username,
            "role": "admin",
        },
    }


@app.get("/api/plans")
def api_plans() -> Dict[str, Any]:
    return get_plan_summary()


@app.get("/api/customers")
def api_customers(plan_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    engine = load_engineered_df()
    df = engine.copy()
    if plan_type:
        df = df[df["plan_type"].astype(str).str.capitalize() == normalize_plan(plan_type)]

    rows = []
    for _, row in df.head(limit).iterrows():
        rows.append(
            {
                "customer_id": row.get("customer_id"),
                "plan_type": row.get("plan_type"),
                "contract_type": row.get("contract_type"),
                "status": "Churned" if int(row.get("churned", 0)) else "Not Churned",
            }
        )
    return {"plan_type": normalize_plan(plan_type) if plan_type else None, "customers": rows}


@app.get("/api/dashboard/summary")
def api_dashboard_summary() -> Dict[str, Any]:
    engine = load_engineered_df()
    ensemble = load_ensemble_df()
    sample_images = [
        "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=40&h=40&q=80",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=40&h=40&q=80",
        "https://images.unsplash.com/photo-1481481600673-c6cb160e2f32?auto=format&fit=crop&w=40&h=40&q=80",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=40&h=40&q=80",
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=40&h=40&q=80",
    ]

    summary_stats = [
        {
            "id": "risk",
            "label": "Customers at Risk",
            "value": f"{int((ensemble['ensemble_proba'] > 0.5).sum()):,}",
            "chartData": [10, 25, 15, 30, 45, 35, 20],
            "color": "indigo",
        },
        {
            "id": "revenue",
            "label": "Revenue at Risk",
            "value": f"${float(engine['revenue_at_risk'].sum()):,.0f}",
            "chartData": [20, 15, 30, 25, 40, 30, 20],
            "color": "indigo",
        },
        {
            "id": "nps",
            "label": "Average NPS",
            "value": f"{float(engine['avg_nps_score'].mean()):.1f}",
            "chartData": [5, 6, 5, 8, 7, 9, 7],
            "highlight": 5,
            "color": "indigo",
        },
    ]

    customer_churn = engine.loc[:, ["customer_id", "plan_type", "contract_type", "churned"]].head(10).copy()
    customer_churn["score"] = load_ensemble_df()["ensemble_proba"].reindex(engine.index).fillna(0).head(10)
    customer_churn["status"] = np.where(customer_churn["churned"] == 1, "Churned", "Not Churned")
    customer_churn["image"] = [sample_images[i % len(sample_images)] for i in range(len(customer_churn))]
    customer_churn = customer_churn.rename(columns={"customer_id": "id", "plan_type": "type"})
    customer_churn["type"] = customer_churn["type"].astype(str) + "/" + customer_churn["contract_type"].astype(str)
    customer_churn["score"] = customer_churn["score"].map(lambda v: f"{float(v):.3f}")
    customer_churn = customer_churn.drop(columns=["contract_type", "churned"])

    feedback_data = [
        {"id": "C-0267", "text": "UI responsif, prediksi sangat akurat.", "nps": 9, "sentiment": "Positive"},
        {"id": "C-0091", "text": "Performa lambat saat muat dataset.", "nps": 5, "sentiment": "Negative"},
        {"id": "C-0176", "text": "Analisis sentimen NLP luar biasa!", "nps": 8, "sentiment": "Positive"},
        {"id": "C-0056", "text": "Bagus, butuh fitur ekspor PDF.", "nps": 10, "sentiment": "Positive"},
        {"id": "C-0002", "text": "Dokumentasi API masih kurang lengkap.", "nps": 6, "sentiment": "Netral"},
    ]

    return {
        "summaryStats": summary_stats,
        "customerChurnData": customer_churn.to_dict(orient="records"),
        "feedbackData": feedback_data,
        "plans": get_plan_summary()["plans"],
    }


@app.get("/api/customer/{customer_id}/features")
def api_customer_features(customer_id: str, plan_type: Optional[str] = None) -> Dict[str, Any]:
    engine = load_engineered_df()
    customer = engine[engine["customer_id"].astype(str) == customer_id]
    if customer.empty:
        raise HTTPException(status_code=404, detail="Customer not found")

    row = customer.iloc[0]
    actual_plan = normalize_plan(str(row.get("plan_type", "")))
    selected_plan = normalize_plan(plan_type or actual_plan)

    return {
        "customer_id": customer_id,
        "plan_type": selected_plan,
        "actual_status": int(row.get("churned", 0)),
        "actual_status_text": "YES (Churned)" if int(row.get("churned", 0)) else "NO (Retained)",
        "profile": {
            "contract_type": row.get("contract_type", "N/A"),
            "annual_value": float(row.get("annual_value", 0)),
            "avg_monthly_usage_hours": float(row.get("avg_monthly_usage_hours", 0)),
            "feature_adoption_pct_mean": float(row.get("feature_adoption_pct_mean", 0)),
            "days_since_last_login": float(row.get("days_since_last_login", 0)),
            "total_tickets": float(row.get("total_tickets", 0)),
            "dunning_event_count": float(row.get("dunning_event_count", 0)),
            "critical_ticket_ratio": float(row.get("critical_ticket_ratio", 0)),
            "payment_health_score": float(row.get("payment_health_score", 0)),
            "avg_nps_score": float(row.get("avg_nps_score", 0)),
            "payment_delay_days_mean": float(row.get("payment_delay_days_mean", 0)),
            "revenue_at_risk": float(row.get("revenue_at_risk", 0)),
        },
    }


@app.post("/api/predict/churn")
def api_predict_churn(payload: PredictRequest) -> Dict[str, Any]:
    engine = load_engineered_df()
    customer = engine[engine["customer_id"].astype(str) == payload.customer_id]
    if customer.empty:
        raise HTTPException(status_code=404, detail="Customer not found")

    row = apply_overrides(customer.iloc[0], payload.overrides)
    plan = normalize_plan(payload.plan_type)
    features = selected_features_for_plan(plan)
    models = load_models(plan)
    if not models:
        raise HTTPException(status_code=404, detail=f"Models not found for plan {plan}")

    try:
        x = row[features].fillna(0).astype(float).to_numpy().reshape(1, -1)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to build feature vector: {exc}") from exc

    preds: Dict[str, float] = {}
    if payload.model_choice in ("XGBoost Only", "Ensemble (Recommended)") and "xgboost" in models:
        preds["xgboost"] = float(models["xgboost"].predict_proba(x)[0][1])
    if payload.model_choice in ("CatBoost Only", "Ensemble (Recommended)") and "catboost" in models:
        preds["catboost"] = float(models["catboost"].predict_proba(x)[0][1])

    if payload.model_choice == "XGBoost Only" and "xgboost" in preds:
        final_pred = preds["xgboost"]
        model_name = "XGBoost"
    elif payload.model_choice == "CatBoost Only" and "catboost" in preds:
        final_pred = preds["catboost"]
        model_name = "CatBoost"
    elif "xgboost" in preds and "catboost" in preds:
        final_pred = 0.6 * preds["xgboost"] + 0.4 * preds["catboost"]
        model_name = "Ensemble"
    elif "xgboost" in preds:
        final_pred = preds["xgboost"]
        model_name = "XGBoost"
    elif "catboost" in preds:
        final_pred = preds["catboost"]
        model_name = "CatBoost"
    else:
        raise HTTPException(status_code=400, detail="No valid predictions could be generated")

    actual_status = int(row.get("churned", 0))
    predicted_churn = 1 if final_pred > 0.25 else 0
    evaluation, explanation = evaluation_label(actual_status, predicted_churn)

    return {
        "customer_id": payload.customer_id,
        "plan_type": plan,
        "model": model_name,
        "probability": round(final_pred, 4),
        "risk_level": risk_label(final_pred),
        "actual_status": actual_status,
        "predicted_status": predicted_churn,
        "evaluation": evaluation,
        "explanation": explanation,
        "model_predictions": preds,
        "risk_factors": compute_risk_factors(row),
        "customer_profile": {
            "contract_type": row.get("contract_type", "N/A"),
            "annual_value": float(row.get("annual_value", 0)),
            "avg_monthly_usage_hours": float(row.get("avg_monthly_usage_hours", 0)),
            "feature_adoption_pct_mean": float(row.get("feature_adoption_pct_mean", 0)),
            "days_since_last_login": float(row.get("days_since_last_login", 0)),
            "total_tickets": float(row.get("total_tickets", 0)),
            "dunning_event_count": float(row.get("dunning_event_count", 0)),
            "critical_ticket_ratio": float(row.get("critical_ticket_ratio", 0)),
            "payment_health_score": float(row.get("payment_health_score", 0)),
            "avg_nps_score": float(row.get("avg_nps_score", 0)),
            "revenue_at_risk": float(row.get("revenue_at_risk", 0)),
        },
    }


@app.get("/api/sentiment/analysis")
def api_sentiment_analysis() -> Dict[str, Any]:
    summary = SESSION_SUMMARY_PATH.read_text(encoding="utf-8") if SESSION_SUMMARY_PATH.exists() else ""
    raw_feedback = [
        {"time": "14:44:14", "elapsed": "0:00:00", "author": "@m0ndazee2", "message": "L thumbnail", "sentiment": "Netral", "emotion": "Neutral", "confidence": "88%"},
        {"time": "14:44:14", "elapsed": "0:00:00", "author": "@ranzehandsomebgt", "message": "gcc makanan gw hampir habis", "sentiment": "Netral", "emotion": "Anticipation", "confidence": "76%"},
        {"time": "14:44:15", "elapsed": "0:00:01", "author": "@sia2008", "message": "damn", "sentiment": "Negative", "emotion": "Surprise", "confidence": "82%"},
        {"time": "14:44:16", "elapsed": "0:00:02", "author": "@hostfytalhcpunk", "message": "lesss goooo", "sentiment": "Positive", "emotion": "Excitement", "confidence": "95%"},
        {"time": "14:44:16", "elapsed": "0:00:02", "author": "@dellyapingg-m8o", "message": "BANG KATA ILHAM KENAPA ITU OPENING NYA terlalu di besar besar kan", "sentiment": "Negative", "emotion": "Annoyance", "confidence": "91%"},
        {"time": "14:44:17", "elapsed": "0:00:03", "author": "@putra1-s5u", "message": "l nunggu", "sentiment": "Netral", "emotion": "Boredom", "confidence": "80%"},
        {"time": "14:49:10", "elapsed": "0:04:56", "author": "@calvin-p8r5b", "message": "akuuu", "sentiment": "Netral", "emotion": "Neutral", "confidence": "90%"},
        {"time": "14:49:10", "elapsed": "0:04:56", "author": "@MuhammadHabibie-j1p", "message": "goib", "sentiment": "Netral", "emotion": "Confusion", "confidence": "78%"},
        {"time": "14:49:10", "elapsed": "0:04:56", "author": "@gamau-n9i", "message": "BANG", "sentiment": "Netral", "emotion": "Neutral", "confidence": "99%"},
        {"time": "14:49:10", "elapsed": "0:04:56", "author": "@sabrnarsy", "message": "yaelah ilham ilhamm", "sentiment": "Negative", "emotion": "Annoyance", "confidence": "85%"},
        {"time": "14:49:11", "elapsed": "0:04:57", "author": "@LaFamme234", "message": "L ilham", "sentiment": "Negative", "emotion": "Dislike", "confidence": "89%"},
    ]

    return {
        "executive_summary": summary,
        "total_feedback": 12450,
        "sentiment_distribution": {"positive": 20, "negative": 20, "neutral": 60},
        "emotion_distribution": [
            {"label": "Neutral / Calm", "value": 60},
            {"label": "Excitement / Anticipation", "value": 20},
            {"label": "Annoyance / Negative", "value": 20},
        ],
        "keywords": [
            {"word": "Ilham", "freq": 412, "type": "Netral"},
            {"word": "Opening", "freq": 289, "type": "Negative"},
            {"word": "Lesss Goooo", "freq": 205, "type": "Positive"},
            {"word": "Nunggu", "freq": 154, "type": "Negative"},
            {"word": "Bang", "freq": 142, "type": "Netral"},
        ],
        "raw_feedback": raw_feedback,
    }


@app.get("/api/sentiment/messages")
def api_sentiment_messages() -> List[Dict[str, Any]]:
    return api_sentiment_analysis()["raw_feedback"]

