from __future__ import annotations

from os import getenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import PredictionRequest, PredictionResponse
from .service import get_service

app = FastAPI(
    title="Customer Churn API",
    version="1.0.0",
    description="FastAPI backend for plan-specific churn prediction.",
)

allowed_origins = [
    origin.strip()
    for origin in getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    service = get_service()
    return {
        "status": "ok",
        "plans": [plan.plan_type for plan in service.list_plans()],
    }


@app.get("/api/plans")
def list_plans() -> dict[str, object]:
    service = get_service()
    return {"plans": [plan.model_dump() for plan in service.list_plans()]}


@app.post("/api/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    service = get_service()
    try:
        return service.predict(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
