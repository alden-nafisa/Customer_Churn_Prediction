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
# Switch to online_shoppers dataset for better training (12k rows, no missing values)
# To use Ravenstack, change to: RAW_DATA_DIR = PROJECT_ROOT / "ravenstack"
RAW_DATA_DIR = PROJECT_ROOT / "online_shoppers"
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
    "monthly_usage_per_user",
    "feature_adoption_pct",
    "last_login_days_ago",
    "support_tickets_last_90d",
    "nps_score",
    "payment_delay_count",
    "monthly_revenue",
    "revenue_per_user",
    "is_enterprise",
    "high_engagement_flag",
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
    # If Ravenstack dataset structure detected, use specialized builder
    if (raw_path / "ravenstack_accounts.csv").exists():
        return build_ravenstack_feature_table(raw_path)
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

    # Engineered per-user and flag features
    feature_frame["total_users"] = feature_frame["total_users"].fillna(1).astype(float) if "total_users" in feature_frame.columns else 1.0
    feature_frame["monthly_usage_per_user"] = (
        feature_frame["monthly_usage_hrs"].fillna(0.0) / feature_frame["total_users"].replace({0: 1})
    ).astype(float)
    feature_frame["revenue_per_user"] = (
        feature_frame["monthly_revenue"].fillna(0.0) / feature_frame["total_users"].replace({0: 1})
    ).astype(float)
    feature_frame["is_enterprise"] = (feature_frame.get("plan_type", "").astype(str) == "Enterprise").astype(int)
    # high_engagement_flag: above-median monthly_usage_per_user
    try:
        median_usage_pp = float(feature_frame["monthly_usage_per_user"].median())
    except Exception:
        median_usage_pp = 0.0
    feature_frame["high_engagement_flag"] = (feature_frame["monthly_usage_per_user"].fillna(0.0) > median_usage_pp).astype(int)

    model_frame = feature_frame[["customer_id"] + FEATURE_COLUMNS + [TARGET_COLUMN]].copy()
    model_frame.drop(columns=["anchor_date"], errors="ignore", inplace=True)
    return model_frame


def build_ravenstack_feature_table(raw_dir: str | Path = RAW_DATA_DIR) -> pd.DataFrame:
    raw_path = Path(raw_dir)
    accounts = _read_csv_with_dates(raw_path / "ravenstack_accounts.csv", ["signup_date"])  # account-level
    churn_events = _read_csv_with_dates(raw_path / "ravenstack_churn_events.csv", ["churn_date"]) if (raw_path / "ravenstack_churn_events.csv").exists() else pd.DataFrame()
    usage = _read_csv_with_dates(raw_path / "ravenstack_feature_usage.csv", ["usage_date"]) if (raw_path / "ravenstack_feature_usage.csv").exists() else pd.DataFrame()
    subs = _read_csv_with_dates(raw_path / "ravenstack_subscriptions.csv", ["start_date", "end_date"]) if (raw_path / "ravenstack_subscriptions.csv").exists() else pd.DataFrame()
    tickets = _read_csv_with_dates(raw_path / "ravenstack_support_tickets.csv", ["submitted_at", "closed_at"]) if (raw_path / "ravenstack_support_tickets.csv").exists() else pd.DataFrame()

    # canonicalize ids
    accounts = accounts.rename(columns={"account_id": "customer_id", "signup_date": "subscription_date", "plan_tier": "plan_type"}, errors="ignore")
    subs = subs.rename(columns={"account_id": "customer_id", "plan_tier": "plan_type", "mrr_amount": "mrr", "seats": "seats"}, errors="ignore")

    # reference date = max available timestamp
    reference_date = _reference_date(
        accounts.get("subscription_date", pd.Series([])),
        churn_events.get("churn_date", pd.Series([])),
        usage.get("usage_date", pd.Series([])),
        subs.get("start_date", pd.Series([])),
        subs.get("end_date", pd.Series([])),
        tickets.get("submitted_at", pd.Series([])),
    )

    # base frame
    feature_frame = accounts[["customer_id", "plan_type", "subscription_date"]].copy()
    # churn label from churn_events or subscription churn_flag if present
    if not churn_events.empty and "account_id" in churn_events.columns:
        last_churn = churn_events.groupby("account_id", as_index=True)["churn_date"].max()
        feature_frame["churned"] = feature_frame["customer_id"].map(last_churn.notna().to_dict()).fillna(False).astype(int)
    elif "churn_flag" in accounts.columns:
        feature_frame["churned"] = accounts["churn_flag"].astype(bool).astype(int)
    else:
        feature_frame["churned"] = 0

    # anchor date
    feature_frame["anchor_date"] = feature_frame["subscription_date"].fillna(reference_date)

    tenure_days = (feature_frame["anchor_date"] - feature_frame["subscription_date"]).dt.days.clip(lower=0)
    feature_frame["tenure_months"] = np.rint(tenure_days / 30.4375).astype(int)

    # seats / total users and revenue from subscriptions
    if not subs.empty:
        subs_idx = subs.groupby("customer_id", as_index=True)
        seats = subs_idx["seats"].median()
        mrr = subs_idx["mrr"].median() if "mrr" in subs.columns else subs_idx["mrr_amount"].median()
        feature_frame["total_users"] = feature_frame["customer_id"].map(seats).fillna(1).astype(float)
        feature_frame["monthly_revenue"] = feature_frame["customer_id"].map(mrr).fillna(0).astype(float)
        # contract_type from billing_frequency if present
        if "billing_frequency" in subs.columns:
            freq = subs_idx["billing_frequency"].agg(lambda s: s.dropna().iloc[0] if not s.dropna().empty else "monthly")
            feature_frame["contract_type"] = feature_frame["customer_id"].map(freq).fillna("monthly").astype(str)
        else:
            feature_frame["contract_type"] = "monthly"
    else:
        feature_frame["total_users"] = 1.0
        feature_frame["monthly_revenue"] = 0.0
        feature_frame["contract_type"] = "monthly"

    # usage -> monthly_usage_hrs, feature_adoption_pct, last_login_days_ago
    if not usage.empty and "subscription_id" in usage.columns:
        # map subscription_id to account via subs
        if not subs.empty and "subscription_id" in subs.columns:
            sub_to_acc = subs.set_index("subscription_id")["customer_id"].to_dict()
            usage["customer_id"] = usage["subscription_id"].map(sub_to_acc)
        else:
            usage["customer_id"] = None
        usage_agg = usage.groupby("customer_id").agg({"usage_duration_secs": "sum", "usage_date": "max", "feature_name": lambda s: s.nunique()})
        usage_agg.rename(columns={"usage_duration_secs": "total_usage_secs", "feature_name": "unique_features"}, inplace=True)
        usage_agg["monthly_usage_hrs"] = usage_agg["total_usage_secs"].fillna(0) / 3600.0
        usage_agg["last_usage_date"] = usage_agg["usage_date"]
        feature_frame["monthly_usage_hrs"] = feature_frame["customer_id"].map(usage_agg["monthly_usage_hrs"].to_dict()).fillna(0.0).astype(float)
        feature_frame["feature_adoption_pct"] = feature_frame["customer_id"].map((usage_agg["unique_features"] / max(usage_agg["unique_features"].max(), 1)).to_dict()).fillna(0.0).astype(float)
        last_usage = usage_agg["last_usage_date"].to_dict()
        feature_frame["last_login_days_ago"] = (
            feature_frame.apply(
                lambda r: (r["anchor_date"] - last_usage.get(r["customer_id"], reference_date)).days if pd.notna(r["anchor_date"]) else None,
                axis=1,
            )
            .fillna(0)
            .astype(int)
            .clip(lower=0)
        )
    else:
        feature_frame["monthly_usage_hrs"] = 0.0
        feature_frame["feature_adoption_pct"] = 0.0
        feature_frame["last_login_days_ago"] = 0

    # support tickets in last 90 days
    if not tickets.empty and "account_id" in tickets.columns:
        tickets["customer_id"] = tickets["account_id"]
        tickets["submitted_at"] = pd.to_datetime(tickets["submitted_at"], errors="coerce")
        cutoff = reference_date - pd.Timedelta(days=90)
        recent = tickets[tickets["submitted_at"] >= cutoff]
        ticket_counts = recent.groupby("customer_id").size()
        feature_frame["support_tickets_last_90d"] = feature_frame["customer_id"].map(ticket_counts.to_dict()).fillna(0).astype(int)
    else:
        feature_frame["support_tickets_last_90d"] = 0

    # nps_score approximate from ticket satisfaction_score if present
    if not tickets.empty and "satisfaction_score" in tickets.columns:
        sat = tickets.groupby("customer_id")["satisfaction_score"].mean()
        feature_frame["nps_score"] = feature_frame["customer_id"].map(sat.to_dict()).fillna(0.0).astype(float)
    else:
        feature_frame["nps_score"] = 0.0

    # payment_delay_count approximate from subscriptions downgrade/upgrade flags or churn events
    if not subs.empty and "downgrade_flag" in subs.columns:
        delays = subs.groupby("customer_id")["downgrade_flag"].sum()
        feature_frame["payment_delay_count"] = feature_frame["customer_id"].map(delays.to_dict()).fillna(0).astype(int)
    else:
        feature_frame["payment_delay_count"] = 0

    # select columns matching FEATURE_COLUMNS + target
    model_frame = feature_frame[["customer_id"] + [c for c in FEATURE_COLUMNS if c in feature_frame.columns] + ["churned"]].copy()
    model_frame.rename(columns={"customer_id": "customer_id"}, inplace=True)
    model_frame.drop(columns=["anchor_date"], errors="ignore", inplace=True)
    return model_frame


def build_online_shoppers_feature_table(csv_path: str | Path) -> pd.DataFrame:
    """Load Online Shoppers dataset and prepare for churn prediction."""
    path = Path(csv_path)
    if path.is_dir():
        # If folder, look for the CSV inside
        csv_files = list(path.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV found in {path}")
        path = csv_files[0]
    
    # Read CSV - Online Shoppers uses comma separator by default
    df = pd.read_csv(path)
    
    # Rename target column for consistency
    if "Revenue" in df.columns:
        df["churned"] = (~df["Revenue"]).astype(int)  # invert: True (purchase) -> 0 (no churn), False -> 1 (churn)
    else:
        raise ValueError("Revenue column not found in Online Shoppers dataset")
    
    # Create customer_id from index if not present
    if "user_id" not in df.columns:
        df["customer_id"] = range(len(df))
    else:
        df["customer_id"] = df["user_id"]
    
    # Select and rename features for model compatibility
    feature_map = {
        "Administrative": "administrative_pages",
        "Administrative_Duration": "administrative_duration",
        "Informational": "informational_pages",
        "Informational_Duration": "informational_duration",
        "ProductRelated": "product_related_pages",
        "ProductRelated_Duration": "product_related_duration",
        "BounceRates": "bounce_rate",
        "ExitRates": "exit_rate",
        "PageValues": "page_values",
        "SpecialDay": "special_day",
        "Month": "month",
        "OperatingSystems": "operating_system",
        "Browser": "browser",
        "Region": "region",
        "TrafficType": "traffic_type",
        "VisitorType": "visitor_type",
        "Weekend": "is_weekend",
    }
    
    # Select available features
    available_feats = [col for col in feature_map.keys() if col in df.columns]
    model_data = df[["customer_id"] + available_feats + ["churned"]].copy()
    model_data.rename(columns=feature_map, inplace=True)
    
    # Engineer features for better prediction
    model_data["total_pages"] = (
        model_data.get("administrative_pages", 0) +
        model_data.get("informational_pages", 0) +
        model_data.get("product_related_pages", 0)
    )
    model_data["avg_page_duration"] = (
        model_data.get("administrative_duration", 0) +
        model_data.get("informational_duration", 0) +
        model_data.get("product_related_duration", 0)
    ) / (model_data["total_pages"].replace(0, 1))
    model_data["bounce_exit_avg"] = (
        (model_data.get("bounce_rate", 0) + model_data.get("exit_rate", 0)) / 2
    )
    model_data["engagement_score"] = (
        model_data.get("page_values", 0) * 10 - 
        model_data.get("bounce_rate", 0) - 
        model_data.get("exit_rate", 0)
    ).clip(lower=0)
    
    # Convert categorical to numeric
    if "visitor_type" in model_data.columns:
        visitor_map = {"Returning_Visitor": 1, "New_Visitor": 0, "Other": 0}
        model_data["visitor_type"] = model_data["visitor_type"].map(visitor_map).fillna(0).astype(int)
    
    if "month" in model_data.columns:
        model_data["month"] = pd.Categorical(model_data["month"]).codes
    
    # Convert boolean to int
    if "is_weekend" in model_data.columns:
        model_data["is_weekend"] = model_data["is_weekend"].astype(int)
    
    # Fill missing values
    numeric_cols = model_data.select_dtypes(include=[np.number]).columns
    model_data[numeric_cols] = model_data[numeric_cols].fillna(0)
    
    return model_data


def load_dataset(data_path: str | Path = DATA_PATH) -> pd.DataFrame:
    path = Path(data_path)
    
    # Load SaaS churn dataset from churn_analysis_datasets folder
    if path.is_dir():
        return build_churn_feature_table(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    
    # Fallback to standard CSV
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