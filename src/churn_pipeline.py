from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
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
from sklearn.pipeline import Pipeline as SkPipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from catboost import CatBoostClassifier
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "churn_analysis_datasets"
DATA_PATH = RAW_DATA_DIR
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

TARGET_COLUMN = "churned"
ID_COLUMN = "customer_id"
PLAN_TYPE_COLUMN = "plan_type"
PLAN_TYPES = ["Starter", "Professional", "Enterprise"]
RANDOM_STATE = 42
TEST_SIZE = 0.2
FEATURE_COLUMNS = [
    "plan_type",
    "contract_type",
    "tenure_months",
    "total_users",
    "monthly_usage_hrs",
    "feature_adoption_pct",
    "last_login_days_ago",
    "support_tickets_last_90d",
    "nps_score",
    "payment_delay_count",
    "monthly_revenue",
]


def _read_csv_with_dates(path: Path, date_columns: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in date_columns:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", dayfirst=True)
    return frame


def _reference_date(*series_list: pd.Series) -> pd.Timestamp:
    candidates = []
    for series in series_list:
        valid_values = pd.to_datetime(series, errors="coerce").dropna()
        if not valid_values.empty:
            candidates.append(valid_values.max())

    if not candidates:
        return pd.Timestamp.today().normalize()

    return max(candidates)


def build_churn_feature_table(raw_dir: str | Path = RAW_DATA_DIR) -> pd.DataFrame:
    raw_path = Path(raw_dir)
    accounts = _read_csv_with_dates(raw_path / "customer_accounts.csv", ["subscription_date", "unsubscribed_date"])
    usage = _read_csv_with_dates(raw_path / "monthly_usage_metrics.csv", ["last_login_date"])
    billing = _read_csv_with_dates(raw_path / "billing_data.csv", ["billing_date", "payment_date"])
    nps = _read_csv_with_dates(raw_path / "nps_surveys.csv", ["survey_date"])
    tickets = _read_csv_with_dates(raw_path / "support_tickets.csv", ["created_date"])

    reference_date = _reference_date(
        accounts["subscription_date"],
        accounts["unsubscribed_date"],
        usage["last_login_date"],
        billing["billing_date"],
        billing["payment_date"],
        nps["survey_date"],
        tickets["created_date"],
    )

    feature_frame = accounts[["customer_id", "plan_type", "contract_type", "subscription_date", "unsubscribed_date", "total_users"]].copy()
    feature_frame["churned"] = feature_frame["unsubscribed_date"].notna().astype(int)
    feature_frame["anchor_date"] = feature_frame["unsubscribed_date"].fillna(reference_date)

    tenure_days = (feature_frame["anchor_date"] - feature_frame["subscription_date"]).dt.days.clip(lower=0)
    feature_frame["tenure_months"] = np.rint(tenure_days / 30.4375).astype(int)

    usage_frame = feature_frame[["customer_id", "anchor_date"]].merge(
        usage[["customer_id", "monthly_usage_hrs", "feature_adoption_pct", "last_login_date"]],
        on="customer_id",
        how="left",
    )
    feature_frame["monthly_usage_hrs"] = usage_frame["monthly_usage_hrs"].astype(float)
    feature_frame["feature_adoption_pct"] = usage_frame["feature_adoption_pct"].astype(float)
    feature_frame["last_login_days_ago"] = (feature_frame["anchor_date"] - usage_frame["last_login_date"]).dt.days.clip(lower=0)

    billing_frame = feature_frame[["customer_id", "anchor_date"]].merge(
        billing[["customer_id", "billing_date", "payment_value", "record_type"]],
        on="customer_id",
        how="left",
    )
    billing_frame = billing_frame[
        billing_frame["billing_date"].notna() & (billing_frame["billing_date"] <= billing_frame["anchor_date"])
    ].copy()
    payment_rows = billing_frame[billing_frame["record_type"].astype(str).str.lower() == "payment"].copy()
    dunning_rows = billing_frame[billing_frame["record_type"].astype(str).str.lower() == "dunning"].copy()

    monthly_revenue = payment_rows.groupby("customer_id", as_index=True)["payment_value"].median()
    payment_delay_count = dunning_rows.groupby("customer_id", as_index=True).size()

    ticket_frame = feature_frame[["customer_id", "anchor_date"]].merge(
        tickets[["customer_id", "created_date"]],
        on="customer_id",
        how="left",
    )
    ticket_frame = ticket_frame[
        ticket_frame["created_date"].notna()
        & (ticket_frame["created_date"] <= ticket_frame["anchor_date"])
        & (ticket_frame["created_date"] >= ticket_frame["anchor_date"] - pd.Timedelta(days=90))
    ].copy()
    support_tickets_last_90d = ticket_frame.groupby("customer_id", as_index=True).size()

    nps_frame = feature_frame[["customer_id", "anchor_date"]].merge(
        nps[["customer_id", "survey_date", "nps_score"]],
        on="customer_id",
        how="left",
    )
    nps_frame = nps_frame[
        nps_frame["survey_date"].notna() & (nps_frame["survey_date"] <= nps_frame["anchor_date"])
    ].sort_values(["customer_id", "survey_date"])
    latest_nps = nps_frame.groupby("customer_id", as_index=True)["nps_score"].last()

    feature_frame["monthly_revenue"] = feature_frame["customer_id"].map(monthly_revenue).astype(float)
    feature_frame["payment_delay_count"] = feature_frame["customer_id"].map(payment_delay_count).fillna(0).astype(int)
    feature_frame["support_tickets_last_90d"] = feature_frame["customer_id"].map(support_tickets_last_90d).fillna(0).astype(int)
    feature_frame["nps_score"] = feature_frame["customer_id"].map(latest_nps).astype(float)

    model_frame = feature_frame[["customer_id"] + FEATURE_COLUMNS + [TARGET_COLUMN]].copy()
    model_frame.drop(columns=["anchor_date"], errors="ignore", inplace=True)
    return model_frame


def load_dataset(data_path: str | Path = DATA_PATH) -> pd.DataFrame:
    path = Path(data_path)
    if path.is_dir():
        return build_churn_feature_table(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    features = df.drop(columns=[TARGET_COLUMN, ID_COLUMN])
    target = df[TARGET_COLUMN].astype(int)
    return features, target


def get_model_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    excluded_columns = [TARGET_COLUMN, ID_COLUMN, PLAN_TYPE_COLUMN]
    return df.drop(columns=[column for column in excluded_columns if column in df.columns]).copy()


def get_plan_slug(plan_type: str) -> str:
    return plan_type.strip().lower().replace(" ", "-")


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
            ("num", SkPipeline(steps=numeric_steps), numeric_features),
            ("cat", SkPipeline(steps=categorical_steps), categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_imbalance_aware_pipeline(
    numeric_features: list[str],
    categorical_features: list[str],
    scale_numeric: bool,
    model: Any,
    use_smote: bool = True,
) -> ImbPipeline:
    steps: list[tuple[str, Any]] = [
        ("preprocessor", make_preprocessor(numeric_features, categorical_features, scale_numeric=scale_numeric)),
    ]
    if use_smote:
        steps.append(("smote", SMOTE(random_state=RANDOM_STATE)))
    steps.append(("model", model))
    return ImbPipeline(steps=steps)


def build_xgb_pipeline(numeric_features: list[str], categorical_features: list[str]) -> ImbPipeline:
    return build_imbalance_aware_pipeline(
        numeric_features,
        categorical_features,
        scale_numeric=False,
        model=XGBClassifier(
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
    )


def build_catboost_pipeline(numeric_features: list[str], categorical_features: list[str]) -> ImbPipeline:
    return build_imbalance_aware_pipeline(
        numeric_features,
        categorical_features,
        scale_numeric=False,
        model=CatBoostClassifier(
            iterations=400,
            learning_rate=0.05,
            depth=6,
            loss_function="Logloss",
            random_seed=RANDOM_STATE,
            verbose=False,
            allow_writing_files=False,
        ),
    )


def train_test_data(
    features: pd.DataFrame,
    target: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    return tuple(train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target,
    ))  # type: ignore[return-value]


def evaluate_model(model: ImbPipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
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


def transform_features(model: ImbPipeline, features: pd.DataFrame) -> np.ndarray:
    transformed = model.named_steps["preprocessor"].transform(features)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    return np.asarray(transformed)


def get_feature_names(model: ImbPipeline) -> list[str]:
    preprocessor = model.named_steps["preprocessor"]
    return preprocessor.get_feature_names_out().tolist()


def build_shap_explainer(model: ImbPipeline) -> shap.TreeExplainer:
    return shap.TreeExplainer(model.named_steps["model"])


def predict_frame(model: ImbPipeline, frame: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
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