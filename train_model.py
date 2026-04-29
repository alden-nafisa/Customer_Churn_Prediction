from __future__ import annotations

import json
from math import ceil
from pathlib import Path

import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from src.churn_pipeline import (
    ARTIFACT_DIR,
    DATA_PATH,
    PLAN_TYPES,
    build_imbalance_aware_pipeline,
    build_catboost_pipeline,
    build_xgb_pipeline,
    detect_feature_types,
    evaluate_model,
    get_feature_names,
    get_model_feature_frame,
    get_plan_slug,
    load_dataset,
    save_artifact,
    split_features_target,
    train_test_data,
)

FEATURE_SELECTION_COVERAGE = 0.90
MIN_SELECTED_FEATURES = 5
SELECTION_XGB_N_ESTIMATORS = 80
SELECTION_PERMUTATION_REPEATS = 5


def select_important_features(
    model,
    x_validation: pd.DataFrame,
    y_validation: pd.Series,
    minimum_features: int = MIN_SELECTED_FEATURES,
    coverage: float = FEATURE_SELECTION_COVERAGE,
) -> list[str]:
    importance = permutation_importance(
        model,
        x_validation,
        y_validation,
        n_repeats=SELECTION_PERMUTATION_REPEATS,
        random_state=42,
        scoring="roc_auc",
        n_jobs=-1,
    )

    ranking = pd.DataFrame(
        {
            "feature": x_validation.columns,
            "importance_mean": importance["importances_mean"],
            "importance_std": importance["importances_std"],
        }
    ).sort_values("importance_mean", ascending=False)

    ranking["importance_mean"] = ranking["importance_mean"].clip(lower=0.0)
    total_importance = float(ranking["importance_mean"].sum())
    if total_importance <= 0:
        return ranking.head(max(minimum_features, 1))["feature"].tolist()

    ranking["normalized_importance"] = ranking["importance_mean"] / total_importance
    ranking["cumulative_importance"] = ranking["normalized_importance"].cumsum()

    cutoff_index = ranking.index[ranking["cumulative_importance"] >= coverage]
    if len(cutoff_index) == 0:
        selected_count = max(minimum_features, ceil(len(ranking) * coverage))
    else:
        selected_count = max(minimum_features, int(cutoff_index[0]) + 1)

    selected = ranking.head(selected_count)["feature"].tolist()
    return selected


def main() -> None:
    dataset = load_dataset(DATA_PATH)
    features = get_model_feature_frame(dataset)
    target = dataset["churned"].astype(int)
    numeric_features, categorical_features = detect_feature_types(features)

    x_train, x_test, y_train, y_test = train_test_data(features, target)

    x_train_selection, x_selection, y_train_selection, y_selection = train_test_split(
        x_train,
        y_train,
        test_size=0.25,
        random_state=42,
        stratify=y_train,
    )

    selection_pipeline = build_imbalance_aware_pipeline(
        numeric_features,
        categorical_features,
        scale_numeric=False,
        model=XGBClassifier(
            n_estimators=SELECTION_XGB_N_ESTIMATORS,
            learning_rate=0.1,
            max_depth=3,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=1,
            reg_alpha=0.0,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            eval_metric="logloss",
            tree_method="hist",
        ),
    )
    print("Training feature-selection XGBoost model...")
    selection_pipeline.fit(x_train_selection, y_train_selection)

    selected_features = select_important_features(selection_pipeline, x_selection, y_selection)
    selected_numeric_features = [column for column in numeric_features if column in selected_features]
    selected_categorical_features = [column for column in categorical_features if column in selected_features]

    selected_importance_frame = pd.DataFrame(
        {
            "feature": x_selection.columns,
            "selected": x_selection.columns.isin(selected_features),
        }
    )

    print(f"Selected features ({len(selected_features)}): {selected_features}")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    plan_metrics: dict[str, dict[str, object]] = {}

    for plan_type in PLAN_TYPES:
        plan_dataset = dataset[dataset["plan_type"] == plan_type].copy()
        plan_features = get_model_feature_frame(plan_dataset)
        plan_target = plan_dataset["churned"].astype(int)
        plan_x_train, plan_x_test, plan_y_train, plan_y_test = train_test_data(plan_features, plan_target)

        xgb_pipeline = build_xgb_pipeline(selected_numeric_features, selected_categorical_features)
        catboost_pipeline = build_catboost_pipeline(selected_numeric_features, selected_categorical_features)

        print(f"Training XGBoost model for {plan_type}...")
        xgb_pipeline.fit(plan_x_train, plan_y_train)

        print(f"Training CatBoost model for {plan_type}...")
        catboost_pipeline.fit(plan_x_train, plan_y_train)

        xgb_metrics = evaluate_model(xgb_pipeline, plan_x_test, plan_y_test)
        catboost_metrics = evaluate_model(catboost_pipeline, plan_x_test, plan_y_test)
        feature_names = get_feature_names(xgb_pipeline)

        plan_slug = get_plan_slug(plan_type)
        plan_artifact_dir = ARTIFACT_DIR / "plan_models" / plan_slug
        plan_artifact_dir.mkdir(parents=True, exist_ok=True)

        test_predictions = pd.DataFrame(
            {
                "customer_id": plan_dataset.loc[plan_x_test.index, "customer_id"],
                "plan_type": plan_type,
                "actual_churn": plan_y_test.values,
                "xgb_probability": xgb_pipeline.predict_proba(plan_x_test)[:, 1],
                "catboost_probability": catboost_pipeline.predict_proba(plan_x_test)[:, 1],
            }
        )
        test_predictions["xgb_predicted"] = (test_predictions["xgb_probability"] >= 0.5).astype(int)
        test_predictions["catboost_predicted"] = (test_predictions["catboost_probability"] >= 0.5).astype(int)

        save_artifact(xgb_pipeline, plan_artifact_dir / "xgb_pipeline.joblib")
        save_artifact(catboost_pipeline, plan_artifact_dir / "catboost_pipeline.joblib")
        test_predictions.to_csv(plan_artifact_dir / "test_predictions.csv", index=False)

        plan_metrics[plan_type] = {
            "xgboost": xgb_metrics,
            "catboost": catboost_metrics,
            "feature_names": feature_names,
            "selected_features": selected_features,
            "feature_columns": {
                "numeric": selected_numeric_features,
                "categorical": selected_categorical_features,
            },
            "training_strategy": {
                "split": "stratified_80_20",
                "feature_selection": {
                    "method": "permutation_importance_on_holdout",
                    "coverage": FEATURE_SELECTION_COVERAGE,
                    "minimum_features": MIN_SELECTED_FEATURES,
                    "validation_split": 0.25,
                },
                "resampling": "SMOTE_on_training_only",
                "plan_scope": plan_type,
            },
        }

        print(f"\n=== {plan_type} Model Comparison ===")
        for name, values in (("XGBoost", xgb_metrics), ("CatBoost", catboost_metrics)):
            print(f"\n{name}")
            for metric_name, metric_value in values.items():
                if metric_name == "confusion_matrix":
                    print(f"{metric_name}: {metric_value}")
                else:
                    print(f"{metric_name}: {metric_value:.4f}")

    summary_payload = {
        "selected_features": selected_features,
        "feature_columns": {
            "numeric": selected_numeric_features,
            "categorical": selected_categorical_features,
        },
        "plans": plan_metrics,
        "training_strategy": {
            "split": "stratified_80_20_per_plan",
            "feature_selection": {
                "method": "permutation_importance_on_holdout_from_full_dataset",
                "coverage": FEATURE_SELECTION_COVERAGE,
                "minimum_features": MIN_SELECTED_FEATURES,
                "validation_split": 0.25,
            },
            "resampling": "SMOTE_on_training_only",
            "plan_routing": "one_model_pair_per_plan_type",
        },
    }
    (ARTIFACT_DIR / "plan_model_metrics.json").write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    selected_importance_frame.to_csv(ARTIFACT_DIR / "feature_selection_summary.csv", index=False)

    print(f"\nArtifacts saved to: {Path(ARTIFACT_DIR).resolve()}")


if __name__ == "__main__":
    main()