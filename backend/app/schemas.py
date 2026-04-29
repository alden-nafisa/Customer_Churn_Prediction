from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PlanType = Literal["Starter", "Professional", "Enterprise"]
ModelName = Literal["XGBoost", "CatBoost"]


class FeatureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    data_type: Literal["numeric", "categorical"]
    minimum: float | None = None
    maximum: float | None = None
    default_value: Any | None = None
    step: float | None = None


class PlanSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_type: PlanType
    selected_features: list[str]
    feature_specs: list[FeatureSpec]
    metrics: dict[str, Any]
    available_models: list[ModelName]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_type: PlanType
    model_name: ModelName = "XGBoost"
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    features: dict[str, Any]


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_type: PlanType
    model_name: ModelName
    threshold: float
    probability: float
    prediction: int
    risk_label: Literal["High Risk", "Low Risk"]
    selected_features: list[str]
    used_features: dict[str, Any]
    missing_features: list[str]
    metrics: dict[str, Any]
