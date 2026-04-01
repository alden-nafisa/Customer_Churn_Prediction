from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "youtube_chat_5_menit_cleaned.csv"
SUMMARY_DIR = PROJECT_ROOT / "artifacts" / "nlp"
TEXT_COLUMN = "message"
TOP_KEYWORDS = 12
TOP_COMMENTS = 8
RANDOM_STATE = 42

STOPWORDS = {
    "yang",
    "dan",
    "di",
    "ke",
    "dari",
    "untuk",
    "itu",
    "ini",
    "aku",
    "kamu",
    "dia",
    "aja",
    "aja",
    "nya",
    "bang",
    "bg",
    "bro",
    "sis",
    "ya",
    "yah",
    "deh",
    "dong",
    "nih",
    "lah",
    "loh",
    "sih",
    "aja",
    "ga",
    "gak",
    "nggak",
    "tidak",
    "the",
    "and",
    "or",
    "to",
    "of",
    "in",
    "is",
    "are",
    "a",
    "an",
}


class KeywordEntry(TypedDict):
    term: str
    frequency: int


class RepresentativeComment(TypedDict):
    rank: int
    comment: str
    score: float


class SessionSummary(TypedDict):
    dataset: str
    total_comments: int
    unique_commenters: int | None
    top_keywords: list[KeywordEntry]
    representative_comments: list[RepresentativeComment]
    most_common_terms: list[tuple[str, int]]
    summary_note: str


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
    comments = frame[[TEXT_COLUMN]].dropna().copy()
    comments[TEXT_COLUMN] = comments[TEXT_COLUMN].astype(str)
    comments["clean_text"] = comments[TEXT_COLUMN].map(clean_text)
    comments = comments[comments["clean_text"].str.len() > 0].copy()
    return comments


def get_top_keywords(comments: pd.Series) -> list[KeywordEntry]:
    vectorizer = CountVectorizer(
        preprocessor=clean_text,
        stop_words=list(STOPWORDS),
        ngram_range=(1, 2),
        min_df=2,
        max_features=60,
    )
    matrix = vectorizer.fit_transform(comments)
    matrix_any = cast(Any, matrix)
    totals = np.asarray(matrix_any.sum(axis=0)).ravel()
    terms = vectorizer.get_feature_names_out()
    keyword_frame = pd.DataFrame({"term": terms, "frequency": totals})
    keyword_frame = keyword_frame.sort_values(["frequency", "term"], ascending=[False, True]).head(TOP_KEYWORDS)
    return [
        {"term": str(term), "frequency": int(frequency)}
        for term, frequency in keyword_frame.itertuples(index=False, name=None)
    ]


def get_representative_comments(comments: pd.Series) -> list[RepresentativeComment]:
    vectorizer = TfidfVectorizer(
        preprocessor=clean_text,
        stop_words=list(STOPWORDS),
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
    )
    matrix = vectorizer.fit_transform(comments)
    matrix_any = cast(Any, matrix)
    centroid = np.asarray(matrix_any.mean(axis=0)).reshape(1, -1)
    similarities = cosine_similarity(matrix, centroid)
    top_indices = similarities.ravel().argsort()[::-1][:TOP_COMMENTS]

    representative = []
    for position in top_indices:
        representative.append(
            {
                "rank": len(representative) + 1,
                "comment": str(comments.iloc[position]),
                "score": float(similarities[position, 0]),
            }
        )
    return representative


def build_session_summary(frame: pd.DataFrame) -> SessionSummary:
    comments = frame[TEXT_COLUMN].astype(str)
    keywords = get_top_keywords(comments)
    representative_comments = get_representative_comments(comments)
    word_count = Counter()
    for text in frame["clean_text"]:
        word_count.update(token for token in text.split() if token not in STOPWORDS)

    return {
        "dataset": DATA_PATH.name,
        "total_comments": int(len(frame)),
        "unique_commenters": int(frame["author"].nunique()) if "author" in frame.columns else None,
        "top_keywords": keywords,
        "representative_comments": representative_comments,
        "most_common_terms": word_count.most_common(20),
        "summary_note": "This summary is extractive and based only on the cleaned comment text.",
    }


def build_summary_text(summary: SessionSummary) -> str:
    lines = [
        f"Session summary for {summary['dataset']}",
        f"Total comments: {summary['total_comments']}",
    ]
    if summary.get("unique_commenters") is not None:
        lines.append(f"Unique commenters: {summary['unique_commenters']}")
    lines.append("")
    lines.append("Top keywords:")
    for item in summary["top_keywords"]:
        lines.append(f"- {item['term']} ({int(item['frequency'])})")
    lines.append("")
    lines.append("Representative comments:")
    for item in summary["representative_comments"]:
        lines.append(f"- {item['comment']}")
    lines.append("")
    lines.append(summary["summary_note"])
    return "\n".join(lines)


def main() -> None:
    frame = load_dataset()
    summary = build_session_summary(frame)

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    (SUMMARY_DIR / "session_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (SUMMARY_DIR / "session_summary.txt").write_text(build_summary_text(summary), encoding="utf-8")

    print(f"Session summary saved to: {SUMMARY_DIR.resolve()}")


if __name__ == "__main__":
    main()
