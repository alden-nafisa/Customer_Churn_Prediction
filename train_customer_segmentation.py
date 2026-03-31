from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline

from src.churn_pipeline import (
    ARTIFACT_DIR,
    DATA_PATH,
    detect_feature_types,
    load_dataset,
    make_preprocessor,
    save_artifact,
    split_features_target,
)

SEGMENTATION_DIR = ARTIFACT_DIR / "segmentation"
RANDOM_STATE = 42
CANDIDATE_CLUSTERS = range(2, 8)


def transform_matrix(model: Pipeline, features: pd.DataFrame) -> np.ndarray:
    transformed = model.named_steps["preprocessor"].transform(features)
    if sparse.issparse(transformed):
        transformed = transformed.toarray()
    return np.asarray(transformed)


def build_segmentation_pipeline(numeric_features: list[str], categorical_features: list[str], n_clusters: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", make_preprocessor(numeric_features, categorical_features, scale_numeric=True)),
            (
                "kmeans",
                KMeans(
                    n_clusters=n_clusters,
                    random_state=RANDOM_STATE,
                    n_init=20,
                ),
            ),
        ]
    )


def choose_best_cluster_count(features: pd.DataFrame, numeric_features: list[str], categorical_features: list[str]) -> tuple[int, list[dict[str, float]]]:
    candidates: list[dict[str, float]] = []
    best_k = 2
    best_score = -1.0

    for n_clusters in CANDIDATE_CLUSTERS:
        pipeline = build_segmentation_pipeline(numeric_features, categorical_features, n_clusters)
        pipeline.fit(features)
        transformed = transform_matrix(pipeline, features)
        labels = pipeline.named_steps["kmeans"].labels_
        score = float(silhouette_score(transformed, labels))
        candidate = {"n_clusters": float(n_clusters), "silhouette_score": score, "inertia": float(pipeline.named_steps["kmeans"].inertia_)}
        candidates.append(candidate)
        if score > best_score:
            best_score = score
            best_k = n_clusters

    return best_k, candidates


def main() -> None:
    dataset = load_dataset(DATA_PATH)
    features, _ = split_features_target(dataset)
    numeric_features, categorical_features = detect_feature_types(features)

    best_k, candidate_scores = choose_best_cluster_count(features, numeric_features, categorical_features)
    final_pipeline = build_segmentation_pipeline(numeric_features, categorical_features, best_k)
    final_pipeline.fit(features)

    transformed = transform_matrix(final_pipeline, features)
    cluster_labels = final_pipeline.named_steps["kmeans"].labels_

    SEGMENTATION_DIR.mkdir(parents=True, exist_ok=True)

    cluster_frame = dataset[["customer_id"]].copy()
    cluster_frame["cluster"] = cluster_labels
    cluster_frame.to_csv(SEGMENTATION_DIR / "customer_clusters.csv", index=False)

    cluster_summary = (
        dataset.assign(cluster=cluster_labels)
        .groupby("cluster")
        .agg(
            customer_count=("customer_id", "count"),
            avg_tenure_months=("tenure_months", "mean"),
            avg_monthly_revenue=("monthly_revenue", "mean"),
            avg_last_login_days_ago=("last_login_days_ago", "mean"),
            avg_support_tickets_last_90d=("support_tickets_last_90d", "mean"),
            avg_nps_score=("nps_score", "mean"),
            avg_payment_delay_count=("payment_delay_count", "mean"),
            churn_rate=("churned", "mean"),
        )
        .reset_index()
    )

    save_artifact(final_pipeline, SEGMENTATION_DIR / "customer_segmentation_pipeline.joblib")
    cluster_summary.to_csv(SEGMENTATION_DIR / "cluster_summary.csv", index=False)

    metrics = {
        "best_n_clusters": best_k,
        "candidate_scores": candidate_scores,
        "final_silhouette_score": float(silhouette_score(transformed, cluster_labels)),
        "cluster_counts": cluster_frame["cluster"].value_counts().sort_index().to_dict(),
    }
    (SEGMENTATION_DIR / "segmentation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\n=== Customer Segmentation Summary ===")
    print(f"Best cluster count: {best_k}")
    print(f"Final silhouette score: {metrics['final_silhouette_score']:.4f}")
    print(f"Cluster counts: {metrics['cluster_counts']}")
    print(f"Artifacts saved to: {SEGMENTATION_DIR.resolve()}")


if __name__ == "__main__":
    main()
