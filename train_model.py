from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.churn_pipeline import (
    ARTIFACT_DIR,
    DATA_PATH,
    build_logistic_pipeline,
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


def main() -> None:
    dataset = load_dataset(DATA_PATH)
    features, target = split_features_target(dataset)
    numeric_features, categorical_features = detect_feature_types(features)

    x_train, x_test, y_train, y_test = train_test_data(features, target)

    logistic_pipeline = build_logistic_pipeline(numeric_features, categorical_features)
    naive_bayes_pipeline = build_naive_bayes_pipeline(numeric_features, categorical_features)
    xgb_pipeline = build_xgb_pipeline(numeric_features, categorical_features)

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
        "feature_columns": {
            "numeric": numeric_features,
            "categorical": categorical_features,
        },
    }
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

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