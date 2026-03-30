from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "customers_dataset.csv"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

TARGET_COLUMN = "churned"
ID_COLUMN = "customer_id"
RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_dataset(data_path: str | Path = DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(data_path)


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    features = df.drop(columns=[TARGET_COLUMN, ID_COLUMN])
    target = df[TARGET_COLUMN].astype(int)
    return features, target


def detect_feature_types(features: pd.DataFrame) -> tuple[list[str], list[str]]:
    categorical_features = features.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    numeric_features = [column for column in features.columns if column not in categorical_features]
    return numeric_features, categorical_features


def make_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
    scale_numeric: bool,
) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    categorical_steps = [
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ]

    return ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=numeric_steps), numeric_features),
            ("cat", Pipeline(steps=categorical_steps), categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_logistic_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", make_preprocessor(numeric_features, categorical_features, scale_numeric=True)),
            (
                "model",
                LogisticRegression(
                    max_iter=4000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def build_xgb_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", make_preprocessor(numeric_features, categorical_features, scale_numeric=False)),
            (
                "model",
                XGBClassifier(
                    n_estimators=300,
                    learning_rate=0.05,
                    max_depth=4,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    min_child_weight=1,
                    reg_alpha=0.0,
                    reg_lambda=1.0,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    eval_metric="logloss",
                    tree_method="hist",
                ),
            ),
        ]
    )


def build_naive_bayes_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", make_preprocessor(numeric_features, categorical_features, scale_numeric=False)),
            (
                "model",
                GaussianNB(var_smoothing=1e-9),
            ),
        ]
    )


def train_test_data(
    features: pd.DataFrame,
    target: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    return train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target,
    )


def evaluate_model(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    predicted = model.predict(x_test)
    probability = model.predict_proba(x_test)[:, 1]

    return {
        "accuracy": float(accuracy_score(y_test, predicted)),
        "precision": float(precision_score(y_test, predicted, zero_division=0)),
        "recall": float(recall_score(y_test, predicted, zero_division=0)),
        "f1": float(f1_score(y_test, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "pr_auc": float(average_precision_score(y_test, probability)),
        "confusion_matrix": confusion_matrix(y_test, predicted).tolist(),
    }


def transform_features(model: Pipeline, features: pd.DataFrame) -> np.ndarray:
    transformed = model.named_steps["preprocessor"].transform(features)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    return np.asarray(transformed)


def get_feature_names(model: Pipeline) -> list[str]:
    preprocessor = model.named_steps["preprocessor"]
    return preprocessor.get_feature_names_out().tolist()


def build_shap_explainer(model: Pipeline) -> shap.TreeExplainer:
    return shap.TreeExplainer(model.named_steps["model"])


def predict_frame(model: Pipeline, frame: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    result = frame.copy()
    probabilities = model.predict_proba(frame)[:, 1]
    result["churn_probability"] = probabilities
    result["risk_segment"] = np.where(
        probabilities >= threshold,
        "High Risk",
        np.where(probabilities >= threshold * 0.7, "Moderate Risk", "Low Risk"),
    )
    return result


def save_artifact(obj: Any, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)
    return path


def load_artifact(path: str | Path) -> Any:
    return joblib.load(path)