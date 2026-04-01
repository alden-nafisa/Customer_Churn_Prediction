from __future__ import annotations

import json
import math
import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "youtube_chat_5_menit_cleaned.csv"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "nlp"
TEXT_COLUMN = "message"
RANDOM_STATE = 42
TEST_SIZE = 0.2

POSITIVE_LEXICON = {
    "good",
    "great",
    "nice",
    "awesome",
    "amazing",
    "mantap",
    "keren",
    "bagus",
    "hebat",
    "pintar",
    "pinter",
    "semangat",
    "gass",
    "gas",
    "lets",
    "let",
    "go",
    "gooo",
    "goooo",
    "suka",
    "senang",
    "terbaik",
    "love",
    "sukses",
    "juara",
    "mantul",
    "ok",
    "oke",
}

NEGATIVE_LEXICON = {
    "bad",
    "worse",
    "worst",
    "jelek",
    "buruk",
    "gagal",
    "sedih",
    "marah",
    "bosan",
    "lelah",
    "capek",
    "parah",
    "anjir",
    "nggak",
    "ga",
    "gak",
    "tidak",
    "kurang",
    "benci",
    "susah",
    "ribet",
}


def clean_text(text: object) -> str:
    if text is None:
        value = ""
    elif isinstance(text, float) and math.isnan(text):
        value = ""
    else:
        value = str(text)
    value = value.lower()
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    value = re.sub(r"@\w+", " ", value)
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def load_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if TEXT_COLUMN not in frame.columns:
        raise ValueError(f"Dataset is missing required column: {TEXT_COLUMN}")
    return frame[[TEXT_COLUMN]].dropna().copy()


def infer_sentiment_label(text: object) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return "Neutral"

    tokens = cleaned.split()
    positive_hits = sum(token in POSITIVE_LEXICON for token in tokens)
    negative_hits = sum(token in NEGATIVE_LEXICON for token in tokens)

    if positive_hits > negative_hits:
        return "Positive"
    if negative_hits > positive_hits:
        return "Negative"
    return "Neutral"


def build_label_frame(frame: pd.DataFrame) -> pd.DataFrame:
    labeled = frame.copy()
    labeled["sentiment_label"] = labeled[TEXT_COLUMN].map(infer_sentiment_label)
    return labeled


def train_test_data(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    x_train, x_test, y_train, y_test = train_test_split(
        frame[TEXT_COLUMN],
        frame["sentiment_label"],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=frame["sentiment_label"],
    )
    return x_train, x_test, y_train, y_test


def build_logistic_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=clean_text,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=10000,
                ),
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=4000,
                    solver="lbfgs",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def build_naive_bayes_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=clean_text,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=10000,
                ),
            ),
            ("model", MultinomialNB(alpha=0.5)),
        ]
    )


def evaluate_model(model: Pipeline, x_test: pd.Series, y_test: pd.Series) -> dict[str, object]:
    predicted = model.predict(x_test)
    return {
        "accuracy": float(accuracy_score(y_test, predicted)),
        "precision_macro": float(precision_score(y_test, predicted, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, predicted, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, predicted, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, predicted).tolist(),
        "classification_report": classification_report(y_test, predicted, output_dict=True, zero_division=0),
    }


def save_artifact(obj: object, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)
    return path


def main() -> None:
    dataset = load_dataset()
    labeled_dataset = build_label_frame(dataset)
    x_train, x_test, y_train, y_test = train_test_data(labeled_dataset)

    logistic_pipeline = build_logistic_pipeline()
    naive_bayes_pipeline = build_naive_bayes_pipeline()

    print("Training Logistic Regression sentiment model from cleaned comments...")
    logistic_pipeline.fit(x_train, y_train)

    print("Training Naive Bayes sentiment model from cleaned comments...")
    naive_bayes_pipeline.fit(x_train, y_train)

    logistic_metrics = evaluate_model(logistic_pipeline, x_test, y_test)
    naive_bayes_metrics = evaluate_model(naive_bayes_pipeline, x_test, y_test)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    save_artifact(logistic_pipeline, ARTIFACT_DIR / "logistic_sentiment_pipeline.pkl")
    save_artifact(naive_bayes_pipeline, ARTIFACT_DIR / "naive_bayes_sentiment_pipeline.pkl")

    test_predictions = pd.DataFrame(
        {
            "message": x_test.values,
            "pseudo_sentiment": y_test.values,
            "logistic_prediction": logistic_pipeline.predict(x_test),
            "naive_bayes_prediction": naive_bayes_pipeline.predict(x_test),
        }
    )
    test_predictions.to_csv(ARTIFACT_DIR / "sentiment_test_predictions.csv", index=False)

    metrics = {
        "logistic_regression": logistic_metrics,
        "naive_bayes": naive_bayes_metrics,
        "label_strategy": {
            "source": "comment_text_only",
            "sentiment_column_used": False,
            "label_method": "lexicon_based_weak_supervision",
            "label_column": "sentiment_label",
            "dataset": DATA_PATH.name,
        },
        "training_strategy": {
            "split": "stratified_80_20",
            "text_features": "tfidf_ngrams_1_2",
        },
    }
    (ARTIFACT_DIR / "sentiment_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\n=== Sentiment Model Comparison ===")
    for name, values in (("Logistic Regression", logistic_metrics), ("Naive Bayes", naive_bayes_metrics)):
        print(f"\n{name}")
        for metric_name, metric_value in values.items():
            if metric_name in {"confusion_matrix", "classification_report"}:
                print(f"{metric_name}: {metric_value}")
            else:
                print(f"{metric_name}: {metric_value:.4f}")

    print(f"\nArtifacts saved to: {ARTIFACT_DIR.resolve()}")


if __name__ == "__main__":
    main()
