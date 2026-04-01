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
    build_logistic_pipeline,
    build_imbalance_aware_pipeline,
    build_naive_bayes_pipeline,
    build_xgb_pipeline,
    detect_feature_types,
    evaluate_model,
    get_feature_names,
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
    features, target = split_features_target(dataset)
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

    logistic_pipeline = build_logistic_pipeline(selected_numeric_features, selected_categorical_features)
    naive_bayes_pipeline = build_naive_bayes_pipeline(selected_numeric_features, selected_categorical_features)
    xgb_pipeline = build_xgb_pipeline(selected_numeric_features, selected_categorical_features)

    print("Training Logistic Regression baseline...")
    logistic_pipeline.fit(x_train, y_train)

    print("Training Naive Bayes baseline...")
    naive_bayes_pipeline.fit(x_train, y_train)

    print("Training XGBoost model...")
    xgb_pipeline.fit(x_train, y_train)

    logistic_metrics = evaluate_model(logistic_pipeline, x_test, y_test)
    naive_bayes_metrics = evaluate_model(naive_bayes_pipeline, x_test, y_test)
    xgb_metrics = evaluate_model(xgb_pipeline, x_test, y_test)

    feature_names = get_feature_names(xgb_pipeline)

    test_predictions = pd.DataFrame(
        {
            "customer_id": dataset.loc[x_test.index, "customer_id"],
            "actual_churn": y_test.values,
            "logistic_probability": logistic_pipeline.predict_proba(x_test)[:, 1],
            "naive_bayes_probability": naive_bayes_pipeline.predict_proba(x_test)[:, 1],
            "xgb_probability": xgb_pipeline.predict_proba(x_test)[:, 1],
        }
    )
    test_predictions["logistic_predicted"] = (test_predictions["logistic_probability"] >= 0.5).astype(int)
    test_predictions["naive_bayes_predicted"] = (test_predictions["naive_bayes_probability"] >= 0.5).astype(int)
    test_predictions["xgb_predicted"] = (test_predictions["xgb_probability"] >= 0.5).astype(int)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    save_artifact(logistic_pipeline, ARTIFACT_DIR / "logistic_pipeline.joblib")
    save_artifact(naive_bayes_pipeline, ARTIFACT_DIR / "naive_bayes_pipeline.joblib")
    save_artifact(xgb_pipeline, ARTIFACT_DIR / "xgb_pipeline.joblib")
    test_predictions.to_csv(ARTIFACT_DIR / "test_predictions.csv", index=False)

    metrics = {
        "logistic_regression": logistic_metrics,
        "naive_bayes": naive_bayes_metrics,
        "xgboost": xgb_metrics,
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
        },
    }
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    selected_importance_frame.to_csv(ARTIFACT_DIR / "feature_selection_summary.csv", index=False)

    print("\n=== Model Comparison ===")
    for name, values in (
        ("Logistic Regression", logistic_metrics),
        ("Naive Bayes", naive_bayes_metrics),
        ("XGBoost", xgb_metrics),
    ):
        print(f"\n{name}")
        for metric_name, metric_value in values.items():
            if metric_name == "confusion_matrix":
                print(f"{metric_name}: {metric_value}")
            else:
                print(f"{metric_name}: {metric_value:.4f}")

    print(f"\nArtifacts saved to: {Path(ARTIFACT_DIR).resolve()}")


if __name__ == "__main__":
    main()