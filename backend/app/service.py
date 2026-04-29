from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from src.churn_pipeline import ARTIFACT_DIR, DATA_PATH, PLAN_TYPES, get_plan_slug, load_artifact, load_dataset

from .schemas import FeatureSpec, ModelName, PlanSummary, PredictionRequest, PredictionResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICS_PATH = PROJECT_ROOT / "artifacts" / "plan_model_metrics.json"


@dataclass(frozen=True)
class PlanRuntime:
    xgb_pipeline: Any
    catboost_pipeline: Any
    selected_features: list[str]
    feature_specs: list[FeatureSpec]
    metrics: dict[str, Any]


class ChurnModelService:
    def __init__(self) -> None:
        self.dataset = load_dataset(DATA_PATH)
        self.metrics_payload = self._load_metrics_payload()
        self.plan_runtimes = self._load_plan_runtimes()

    def _load_metrics_payload(self) -> dict[str, Any]:
        if METRICS_PATH.exists():
            return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        return {"plans": {}}

    def _build_feature_specs(self, frame: pd.DataFrame, selected_features: list[str]) -> list[FeatureSpec]:
        specs: list[FeatureSpec] = []
        for column in selected_features:
            if column not in frame.columns:
                continue

            series = frame[column].dropna()
            if series.empty:
                continue

            if pd.api.types.is_numeric_dtype(frame[column]):
                default_value = series.median()
                if pd.api.types.is_integer_dtype(frame[column]):
                    default_value = int(round(float(default_value)))
                    step = 1.0
                else:
                    default_value = float(default_value)
                    step = 0.1

                specs.append(
                    FeatureSpec(
                        name=column,
                        data_type="numeric",
                        minimum=float(series.min()),
                        maximum=float(series.max()),
                        default_value=default_value.item() if hasattr(default_value, "item") else default_value,
                        step=step,
                    )
                )
            else:
                defaults = series.mode()
                specs.append(
                    FeatureSpec(
                        name=column,
                        data_type="categorical",
                        default_value=defaults.iat[0] if not defaults.empty else str(series.iloc[0]),
                    )
                )

        return specs

    def _load_plan_runtimes(self) -> dict[str, PlanRuntime]:
        plan_runtimes: dict[str, PlanRuntime] = {}
        plans_payload = self.metrics_payload.get("plans", {})

        for plan_type in PLAN_TYPES:
            plan_slug = get_plan_slug(plan_type)
            plan_dir = ARTIFACT_DIR / "plan_models" / plan_slug
            plan_frame = self.dataset[self.dataset["plan_type"] == plan_type].copy()
            plan_metrics = plans_payload.get(plan_type, {})
            selected_features = list(plan_metrics.get("selected_features", []))
            if not selected_features:
                selected_features = list(self.metrics_payload.get("selected_features", []))

            xgb_pipeline = load_artifact(plan_dir / "xgb_pipeline.joblib")
            catboost_pipeline = load_artifact(plan_dir / "catboost_pipeline.joblib")

            plan_runtimes[plan_type] = PlanRuntime(
                xgb_pipeline=xgb_pipeline,
                catboost_pipeline=catboost_pipeline,
                selected_features=selected_features,
                feature_specs=self._build_feature_specs(plan_frame, selected_features),
                metrics=plan_metrics,
            )

        return plan_runtimes

    def list_plans(self) -> list[PlanSummary]:
        summaries: list[PlanSummary] = []
        for plan_type in PLAN_TYPES:
            runtime = self.plan_runtimes[plan_type]
            summaries.append(
                PlanSummary(
                    plan_type=plan_type,
                    selected_features=runtime.selected_features,
                    feature_specs=runtime.feature_specs,
                    metrics=runtime.metrics,
                    available_models=["XGBoost", "CatBoost"],
                )
            )
        return summaries

    def predict(self, payload: PredictionRequest) -> PredictionResponse:
        runtime = self.plan_runtimes.get(payload.plan_type)
        if runtime is None:
            raise ValueError(f"Unknown plan type: {payload.plan_type}")

        model_name = payload.model_name
        pipeline = runtime.xgb_pipeline if model_name == "XGBoost" else runtime.catboost_pipeline

        feature_values = {feature: payload.features.get(feature) for feature in runtime.selected_features}
        missing_features = [feature for feature, value in feature_values.items() if value is None]
        feature_frame = pd.DataFrame([feature_values])
        for column in runtime.selected_features:
            feature_frame[column] = pd.to_numeric(feature_frame[column], errors="coerce")

        probability = float(pipeline.predict_proba(feature_frame)[:, 1][0])
        prediction = int(probability >= payload.threshold)
        risk_label = "High Risk" if prediction == 1 else "Low Risk"

        return PredictionResponse(
            plan_type=payload.plan_type,
            model_name=model_name,
            threshold=payload.threshold,
            probability=probability,
            prediction=prediction,
            risk_label=risk_label,
            selected_features=runtime.selected_features,
            used_features=feature_values,
            missing_features=missing_features,
            metrics=runtime.metrics.get("xgboost" if model_name == "XGBoost" else "catboost", {}),
        )


@lru_cache(maxsize=1)
def get_service() -> ChurnModelService:
    return ChurnModelService()
