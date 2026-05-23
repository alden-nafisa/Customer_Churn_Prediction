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
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
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
def load_prediction_results() -> pd.DataFrame:
    """Load final prediction results joined with engineered customer features."""
    engineered = load_engineered_df().reset_index(drop=True)
    results = _read_csv(PROJECT_ROOT / "model_results" / "final_predictions.csv").reset_index(drop=True)

    limit = min(len(engineered), len(results))
    merged = pd.concat(
        [engineered.iloc[:limit].copy(), results.iloc[:limit].copy()],
        axis=1,
    )

    merged["customer_id"] = merged["customer_id"].astype(str)
    merged["plan_type"] = merged["plan_type"].astype(str).str.capitalize()
    merged["plan"] = merged["plan"].astype(str).str.capitalize()
    merged["actual"] = merged["actual_churn"].astype(int)
    merged["ensemble_proba"] = merged["churn_probability"].astype(float)
    merged["ensemble_prediction"] = merged["prediction_threshold_0.50"].astype(int)
    merged["xgb_proba"] = merged["xgb_probability"].astype(float)
    merged["cat_proba"] = merged["cat_probability"].astype(float)
    merged["risk_level"] = merged["ensemble_proba"].apply(risk_label)
    return merged


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


def classification_summary(actual: pd.Series, predicted: pd.Series) -> Dict[str, Any]:
    """Build accuracy, recall, precision, F1, and confusion counts."""
    actual_series = actual.astype(int)
    predicted_series = predicted.astype(int)

    tp = int(((actual_series == 1) & (predicted_series == 1)).sum())
    tn = int(((actual_series == 0) & (predicted_series == 0)).sum())
    fp = int(((actual_series == 0) & (predicted_series == 1)).sum())
    fn = int(((actual_series == 1) & (predicted_series == 0)).sum())
    total = int(len(actual_series))

    accuracy = (tp + tn) / total if total else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    return {
        "accuracy": round(float(accuracy), 4),
        "recall": round(float(recall), 4),
        "precision": round(float(precision), 4),
        "f1": round(float(f1), 4),
        "counts": {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "total": total},
    }


def build_risk_distribution(plan_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Return risk distribution buckets for the overall analysis chart."""
    risk_levels = pd.cut(
        plan_df["ensemble_proba"],
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=["Low", "Medium", "High", "Very High"],
        include_lowest=True,
    )
    counts = risk_levels.value_counts().reindex(["Low", "Medium", "High", "Very High"], fill_value=0)
    return [{"label": label, "value": int(counts[label])} for label in counts.index]


def build_probability_distribution(plan_df: pd.DataFrame, bins: int = 10) -> Dict[str, Any]:
    """Return histogram bins for churn probability distribution."""
    values = plan_df["ensemble_proba"].astype(float).to_numpy()
    if len(values) == 0:
        return {"bins": [], "counts": []}

    counts, edges = np.histogram(values, bins=bins, range=(0, 1))
    labels = [f"{edges[i]:.1f}-{edges[i + 1]:.1f}" for i in range(len(edges) - 1)]
    return {"bins": labels, "counts": [int(value) for value in counts]}


def build_feature_dominance(plan_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Build the feature dominance list used by the UI chart."""
    feature_order = [
        "nps_trend",
        "is_on_time_sum",
        "feature_adoption_pct_mean",
        "churned",
        "ensemble_prediction",
        "cat_proba",
        "xgb_proba",
        "ensemble_proba",
        "actual",
    ]

    available = [column for column in feature_order if column in plan_df.columns]
    if not available:
        return []

    correlations = plan_df[available].corrwith(plan_df["actual"]).abs().sort_values()
    return [{"label": label, "value": round(float(correlations[label]), 4)} for label in correlations.index]


def build_revenue_at_risk(plan_df: pd.DataFrame) -> Dict[str, Any]:
    """Summarize revenue impact by risk segment."""
    working = plan_df.copy()
    working["risk_category"] = pd.cut(
        working["ensemble_proba"],
        bins=[0, 0.3, 0.5, 1.0],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    )

    grouped = working.groupby("risk_category", observed=False)["annual_value"].agg(["sum", "count", "mean"])
    grouped = grouped.reindex(["Low", "Medium", "High"]).fillna(0)

    rows = []
    for category, row in grouped.iterrows():
        rows.append(
            {
                "risk_category": category,
                "total_value": round(float(row["sum"]), 4),
                "customer_count": int(row["count"]),
                "avg_value_per_customer": round(float(row["mean"]), 4),
            }
        )

    high_risk_df = working[working["ensemble_proba"] > 0.5]
    high_risk_value = float(high_risk_df["annual_value"].sum())
    total_value = float(working["annual_value"].sum())
    pct_of_total = (high_risk_value / total_value * 100) if total_value else 0.0

    return {
        "value_at_high_risk": round(high_risk_value, 4),
        "pct_of_total_value": round(float(pct_of_total), 4),
        "high_risk_customers": int(len(high_risk_df)),
        "rows": rows,
    }


def build_top_customers(plan_df: pd.DataFrame, limit: int = 15) -> List[Dict[str, Any]]:
    """Return top at-risk customers for a plan slice."""
    top_df = plan_df.sort_values("ensemble_proba", ascending=False).head(limit).copy()
    result: List[Dict[str, Any]] = []
    for _, row in top_df.iterrows():
        result.append(
            {
                "customer_id": str(row.get("customer_id", "")),
                "plan": str(row.get("plan", row.get("plan_type", ""))),
                "tenure_months": round(float(row.get("tenure_months", 0)), 4),
                "annual_value": round(float(row.get("annual_value", 0)), 4),
                "nps": round(float(row.get("avg_nps_score", 0)), 4),
                "risk_pct": round(float(row.get("ensemble_proba", 0)) * 100, 1),
            }
        )
    return result


def build_model_comparison(plan_df: pd.DataFrame) -> Dict[str, Any]:
    """Compare high-risk counts and scorecard metrics across models."""
    xgb_pred = (plan_df["xgb_proba"] > 0.5).astype(int)
    cat_pred = (plan_df["cat_proba"] > 0.5).astype(int)
    ensemble_pred = plan_df["ensemble_prediction"].astype(int)

    return {
        "high_risk_detected": [
            {"model": "XGBoost", "value": int((plan_df["xgb_proba"] > 0.5).sum())},
            {"model": "CatBoost", "value": int((plan_df["cat_proba"] > 0.5).sum())},
            {"model": "Ensemble", "value": int((plan_df["ensemble_proba"] > 0.5).sum())},
        ],
        "scorecards": {
            "xgboost": classification_summary(plan_df["actual"], xgb_pred),
            "catboost": classification_summary(plan_df["actual"], cat_pred),
            "ensemble": classification_summary(plan_df["actual"], ensemble_pred),
        },
    }


def build_recommendation_actions(row: pd.Series, probability: float, evaluation: str) -> List[str]:
    """Generate concise next-step recommendations for the selected customer."""
    actions: List[str] = []

    if probability > 0.7:
        actions.append("Contact customer immediately by phone and trigger a retention case.")
    elif probability > 0.5:
        actions.append("Schedule a proactive success call within 24 hours.")
    else:
        actions.append("Monitor the account and keep a light-touch check-in cadence.")

    if float(row.get("payment_delay_days_mean", 0)) > 15:
        actions.append("Review payment delays and offer a temporary billing resolution plan.")

    if float(row.get("total_tickets", 0)) > 2:
        actions.append("Escalate open support tickets to the technical owner.")

    if float(row.get("avg_nps_score", 0)) < 6:
        actions.append("Run an executive check-in to recover satisfaction and product fit.")

    if evaluation == "FALSE_POSITIVE":
        actions.append("Validate the latest activity before offering discounts to avoid unnecessary incentive spend.")

    return actions[:4]


def build_dashboard_summary_stats(engine: pd.DataFrame, predictions: pd.DataFrame) -> List[Dict[str, Any]]:
    """Build the dashboard KPI cards and sparkline data from real backend values."""
    risk_counts, _ = np.histogram(predictions["ensemble_proba"].astype(float).to_numpy(), bins=7, range=(0, 1))
    revenue_counts, _ = np.histogram(engine["revenue_at_risk"].astype(float).to_numpy(), bins=7)
    nps_values = engine["avg_nps_score"].astype(float).to_numpy()
    if len(nps_values):
        nps_counts, _ = np.histogram(nps_values, bins=7, range=(0, 10))
        avg_nps = float(engine["avg_nps_score"].mean())
        nps_highlight = min(len(nps_counts) - 1, max(0, int((avg_nps / 10) * len(nps_counts))))
    else:
        nps_counts = np.array([0, 0, 0, 0, 0, 0, 0])
        avg_nps = 0.0
        nps_highlight = 0

    return [
        {
            "id": "risk",
            "label": "Customers at Risk",
            "value": f"{int((predictions['ensemble_proba'] > 0.5).sum()):,}",
            "chartData": [int(value) for value in risk_counts.tolist()],
            "color": "indigo",
        },
        {
            "id": "revenue",
            "label": "Revenue at Risk",
            "value": f"${float(engine['revenue_at_risk'].sum()):,.0f}",
            "chartData": [int(value) for value in revenue_counts.tolist()],
            "color": "indigo",
        },
        {
            "id": "nps",
            "label": "Average NPS",
            "value": f"{avg_nps:.1f}",
            "chartData": [int(value) for value in nps_counts.tolist()],
            "highlight": nps_highlight,
            "color": "indigo",
        },
    ]


def build_dashboard_customer_churn(limit_per_status: int = 10) -> List[Dict[str, Any]]:
    """Return a balanced churn/non-churn sample for the dashboard table."""
    predictions = load_prediction_results().copy()
    churned_df = predictions[predictions["actual"] == 1].sort_values("ensemble_proba", ascending=False).head(limit_per_status)
    retained_df = predictions[predictions["actual"] == 0].sort_values("ensemble_proba", ascending=False).head(limit_per_status)
    combined = pd.concat([churned_df, retained_df], axis=0).head(limit_per_status * 2).copy()

    combined["status"] = np.where(combined["actual"] == 1, "Churned", "Not Churned")
    combined["type"] = combined["plan_type"].astype(str) + "/" + combined["contract_type"].astype(str)
    combined["score"] = combined["ensemble_proba"].map(lambda value: f"{float(value):.3f}")

    return (
        combined.loc[:, ["customer_id", "type", "score", "status"]]
        .rename(columns={"customer_id": "id"})
        .to_dict(orient="records")
    )


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
def api_customers(plan_type: Optional[str] = None, limit: int = 5000) -> Dict[str, Any]:
    engine = load_engineered_df()
    df = engine.copy()
    if plan_type:
        df = df[df["plan_type"].astype(str).str.capitalize() == normalize_plan(plan_type)]

    df = df.sort_values("customer_id")
    if limit is not None and limit > 0:
        df = df.head(limit)

    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "customer_id": row.get("customer_id"),
                "plan_type": row.get("plan_type"),
                "contract_type": row.get("contract_type"),
                "status": "Churned" if int(row.get("churned", 0)) else "Not Churned",
            }
        )
    return {"plan_type": normalize_plan(plan_type) if plan_type else None, "customers": rows}


@app.get("/api/churn/analysis")
def api_churn_analysis(plan_type: Optional[str] = None) -> Dict[str, Any]:
    predictions = load_prediction_results()
    plan = normalize_plan(plan_type) if plan_type else sorted(predictions["plan"].unique().tolist())[0]
    plan_df = predictions[predictions["plan"] == plan].copy()

    if plan_df.empty:
        raise HTTPException(status_code=404, detail=f"No churn analysis data found for plan: {plan}")

    plan_summary = {
        "plan_type": plan,
        "total_customers": int(len(plan_df)),
        "actual_churned": int(plan_df["actual"].sum()),
        "high_risk_customers": int((plan_df["ensemble_proba"] > 0.5).sum()),
        "model_accuracies": {
            "xgboost": classification_summary(plan_df["actual"], (plan_df["xgb_proba"] > 0.5).astype(int))["accuracy"],
            "catboost": classification_summary(plan_df["actual"], (plan_df["cat_proba"] > 0.5).astype(int))["accuracy"],
            "ensemble": classification_summary(plan_df["actual"], plan_df["ensemble_prediction"])["accuracy"],
        },
    }

    overall = {
        "risk_distribution": build_risk_distribution(plan_df),
        "probability_distribution": build_probability_distribution(plan_df),
        "feature_dominance": build_feature_dominance(plan_df),
        "revenue_at_risk": build_revenue_at_risk(plan_df),
        "top_risk_customers": build_top_customers(plan_df, limit=15),
        "top15_customers": build_top_customers(predictions, limit=15),
    }

    evaluation = classification_summary(plan_df["actual"], plan_df["ensemble_prediction"])
    confusion = evaluation["counts"]
    model_comparison = build_model_comparison(plan_df)

    return {
        "plan_type": plan,
        "customers": sorted(plan_df["customer_id"].astype(str).unique().tolist()),
        "plan_summary": plan_summary,
        "overall": overall,
        "evaluation": {
            "scorecard": {
                "accuracy": evaluation["accuracy"],
                "recall": evaluation["recall"],
                "precision": evaluation["precision"],
                "f1": evaluation["f1"],
            },
            "confusion_matrix": {
                "labels": ["Retained", "Churned"],
                "predicted_labels": ["Retained", "Churned"],
                "matrix": [
                    [confusion["tn"], confusion["fp"]],
                    [confusion["fn"], confusion["tp"]],
                ],
                "counts": confusion,
            },
            "model_comparison": model_comparison,
        },
    }


@app.get("/api/dashboard/summary")
def api_dashboard_summary() -> Dict[str, Any]:
    engine = load_engineered_df()
    predictions = load_prediction_results()

    summary_stats = build_dashboard_summary_stats(engine, predictions)
    customer_churn = build_dashboard_customer_churn(limit_per_status=10)

    feedback_data = [
        {"id": "C-0267", "text": "UI responsif, prediksi sangat akurat.", "nps": 9, "sentiment": "Positive"},
        {"id": "C-0091", "text": "Performa lambat saat muat dataset.", "nps": 5, "sentiment": "Negative"},
        {"id": "C-0176", "text": "Analisis sentimen NLP luar biasa!", "nps": 8, "sentiment": "Positive"},
        {"id": "C-0056", "text": "Bagus, butuh fitur ekspor PDF.", "nps": 10, "sentiment": "Positive"},
        {"id": "C-0002", "text": "Dokumentasi API masih kurang lengkap.", "nps": 6, "sentiment": "Netral"},
    ]

    return {
        "summaryStats": summary_stats,
        "customerChurnData": customer_churn,
        "totalCustomers": int(len(engine)),
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
    predicted_churn = 1 if final_pred > payload.threshold else 0
    evaluation, explanation = evaluation_label(actual_status, predicted_churn)
    customer_profile = {
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
    }

    return {
        "customer_id": payload.customer_id,
        "plan_type": plan,
        "model": model_name,
        "probability": round(final_pred, 4),
        "threshold": round(float(payload.threshold), 4),
        "risk_level": risk_label(final_pred),
        "actual_status": actual_status,
        "actual_status_text": "YES (Churned)" if actual_status else "NO (Retained)",
        "predicted_status": predicted_churn,
        "evaluation": evaluation,
        "explanation": explanation,
        "model_predictions": preds,
        "risk_factors": compute_risk_factors(row),
        "recommendation_actions": build_recommendation_actions(row, final_pred, evaluation),
        "customer_profile": customer_profile,
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

