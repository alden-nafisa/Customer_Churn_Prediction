"""
Generate NLP visualizations for sentiment analysis and session summaries.
This script creates sentiment models and session summaries from the YouTube dataset,
then integrates them into the app_lapisai.py dashboard.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
import re
import math

import joblib
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "youtube_chat_5_menit_cleaned.csv"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "nlp"
TEXT_COLUMN = "message"
TIME_COLUMN = "time"
AUTHOR_COLUMN = "author"
RANDOM_STATE = 42
TEST_SIZE = 0.2

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

POSITIVE_LEXICON = {
    "good", "great", "nice", "awesome", "amazing", "mantap", "keren", "bagus",
    "hebat", "pintar", "pinter", "semangat", "gass", "gas", "lets", "let", "go",
    "gooo", "goooo", "suka", "senang", "terbaik", "love", "sukses", "juara",
    "mantul", "ok", "oke", "excited", "love", "beautiful", "perfect", "wonderful",
    "excellent", "fantastic", "incredible", "joss", "epik", "bestie",
}

NEGATIVE_LEXICON = {
    "bad", "worse", "worst", "jelek", "buruk", "gagal", "sedih", "marah", "bosan",
    "lelah", "capek", "parah", "anjir", "nggak", "ga", "gak", "tidak", "kurang",
    "benci", "susah", "ribet", "hate", "horrible", "terrible", "awful", "poor",
    "disappointing", "sad", "angry", "frustrated", "annoying", "boring", "dumb",
}

STOP_WORDS = set(stopwords.words('english')) | set(stopwords.words('indonesian'))


def clean_text(text: object) -> str:
    """Clean and normalize text."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    value = str(text).lower()
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    value = re.sub(r"@\w+", " ", value)
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def infer_sentiment_label(text: object) -> str:
    """Infer sentiment from text using lexicon-based approach."""
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


def load_youtube_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load YouTube chat data."""
    df = pd.read_csv(path)
    if TEXT_COLUMN not in df.columns:
        raise ValueError(f"Dataset missing column: {TEXT_COLUMN}")
    return df.copy()


def build_labeled_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Add sentiment labels to dataset using weak supervision."""
    labeled = df.copy()
    labeled["sentiment_label"] = labeled[TEXT_COLUMN].map(infer_sentiment_label)
    return labeled


def train_sentiment_model(labeled_df: pd.DataFrame) -> tuple[Pipeline, dict, pd.DataFrame]:
    """Train sentiment classification model."""
    # Split data
    x_train, x_test, y_train, y_test = train_test_split(
        labeled_df[TEXT_COLUMN],
        labeled_df["sentiment_label"],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=labeled_df["sentiment_label"],
    )
    
    # Build pipeline
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            preprocessor=clean_text,
            ngram_range=(1, 2),
            min_df=2,
            max_features=10000,
        )),
        ("model", MultinomialNB(alpha=0.5)),
    ])
    
    # Train
    pipeline.fit(x_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(x_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_macro": float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
    }
    
    # Test predictions for preview
    test_predictions = pd.DataFrame({
        "message": x_test.values,
        "true_sentiment": y_test.values,
        "predicted_sentiment": y_pred,
    })
    
    return pipeline, metrics, test_predictions


def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    """Extract keywords from text."""
    cleaned = clean_text(text)
    tokens = cleaned.split()
    keywords = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    counter = Counter(keywords)
    return counter.most_common(top_n)


def build_session_summary(df: pd.DataFrame) -> dict:
    """Build comprehensive session summary."""
    # Basic stats
    total_comments = len(df)
    unique_commenters = df[AUTHOR_COLUMN].nunique() if AUTHOR_COLUMN in df.columns else 0
    
    # Combine all messages
    all_text = " ".join(df[TEXT_COLUMN].astype(str).values)
    
    # Extract keywords
    top_keywords_list = extract_keywords(all_text, top_n=15)
    top_keywords = [{"keyword": k, "frequency": v} for k, v in top_keywords_list]
    
    # Sentiment distribution
    sentiment_counts = df["sentiment_label"].value_counts().to_dict() if "sentiment_label" in df.columns else {}
    
    # Representative comments (from each sentiment class)
    representative = []
    if "sentiment_label" in df.columns:
        for sentiment in ["Positive", "Negative", "Neutral"]:
            sentiment_df = df[df["sentiment_label"] == sentiment]
            if not sentiment_df.empty:
                # Get a comment with good length
                good_comments = sentiment_df[sentiment_df[TEXT_COLUMN].str.len() > 15]
                if not good_comments.empty:
                    comment = good_comments.iloc[0][TEXT_COLUMN]
                else:
                    comment = sentiment_df.iloc[0][TEXT_COLUMN]
                representative.append({
                    "sentiment": sentiment,
                    "comment": comment,
                    "author": sentiment_df.iloc[0].get(AUTHOR_COLUMN, "Unknown"),
                })
    
    # Timeline of sentiments (convert timestamps to strings for JSON serialization)
    if TIME_COLUMN in df.columns and "sentiment_label" in df.columns:
        df_timeline = df.copy()
        df_timeline[TIME_COLUMN] = pd.to_datetime(df_timeline[TIME_COLUMN], errors='coerce')
        df_timeline = df_timeline.dropna(subset=[TIME_COLUMN])
        if not df_timeline.empty:
            sentiment_timeline = df_timeline.groupby(
                pd.Grouper(key=TIME_COLUMN, freq='1min')
            )["sentiment_label"].apply(lambda x: (x == "Positive").sum())
            # Convert timestamps to strings for JSON serialization
            timeline_data = {str(k): v for k, v in sentiment_timeline.to_dict().items()}
        else:
            timeline_data = {}
    else:
        timeline_data = {}
    
    # Extractive summary (key sentences)
    summary_sentences = []
    try:
        sentences = sent_tokenize(all_text[:2000])  # Limit to first part
        for sent in sentences[:3]:
            if len(sent.split()) >= 5:
                summary_sentences.append(sent)
    except:
        pass
    
    summary_text = " ".join(summary_sentences) if summary_sentences else all_text[:200]
    
    return {
        "total_comments": int(total_comments),
        "unique_commenters": int(unique_commenters),
        "sentiment_distribution": sentiment_counts,
        "top_keywords": top_keywords,
        "representative_comments": representative,
        "extractive_summary": summary_text,
        "timeline_data": timeline_data,
    }


def create_sentiment_visualizations(labeled_df: pd.DataFrame, metrics: dict) -> dict:
    """Create sentiment analysis visualizations."""
    visualizations = {}
    
    # 1. Sentiment distribution pie chart
    sentiment_dist = labeled_df["sentiment_label"].value_counts()
    fig_pie = px.pie(
        values=sentiment_dist.values,
        names=sentiment_dist.index,
        title="YouTube Session: Sentiment Distribution",
        color_discrete_map={"Positive": "#10b981", "Neutral": "#6b7280", "Negative": "#ef4444"},
    )
    visualizations["sentiment_pie"] = fig_pie
    
    # 2. Message length vs sentiment
    labeled_df_copy = labeled_df.copy()
    labeled_df_copy["message_length"] = labeled_df_copy[TEXT_COLUMN].str.len()
    fig_scatter = px.scatter(
        labeled_df_copy,
        x="message_length",
        y="sentiment_label",
        color="sentiment_label",
        size=[5] * len(labeled_df_copy),
        title="Message Length by Sentiment",
        color_discrete_map={"Positive": "#10b981", "Neutral": "#6b7280", "Negative": "#ef4444"},
    )
    fig_scatter.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
    visualizations["message_length_scatter"] = fig_scatter
    
    # 3. Model performance metrics
    metrics_data = {
        "Metric": ["Accuracy", "Precision", "Recall", "F1-Score"],
        "Value": [
            metrics.get("accuracy", 0),
            metrics.get("precision_macro", 0),
            metrics.get("recall_macro", 0),
            metrics.get("f1_macro", 0),
        ]
    }
    fig_metrics = px.bar(
        metrics_data,
        x="Metric",
        y="Value",
        title="Sentiment Model Performance",
        color="Value",
        color_continuous_scale="Blues",
    )
    fig_metrics.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
    visualizations["metrics_bar"] = fig_metrics
    
    return visualizations


def save_nlp_artifacts(pipeline: Pipeline, metrics: dict, test_predictions: pd.DataFrame, session_summary: dict, summary_text: str) -> None:
    """Save all NLP artifacts."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save pipeline
    joblib.dump(pipeline, ARTIFACT_DIR / "naive_bayes_sentiment_pipeline.pkl")
    
    # Save metrics
    metrics_payload = {
        "naive_bayes": metrics,
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
    (ARTIFACT_DIR / "sentiment_metrics.json").write_text(
        json.dumps(metrics_payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    # Save test predictions
    test_predictions.to_csv(ARTIFACT_DIR / "sentiment_test_predictions.csv", index=False)
    
    # Save session summary
    session_summary["summary_text"] = summary_text
    (ARTIFACT_DIR / "session_summary.json").write_text(
        json.dumps(session_summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"✅ NLP artifacts saved to {ARTIFACT_DIR}")


def load_nlp_assets() -> dict:
    """Load NLP assets for the dashboard."""
    try:
        # Load metrics
        with open(ARTIFACT_DIR / "sentiment_metrics.json", "r", encoding="utf-8") as f:
            sentiment_metrics = json.load(f)
        
        # Load test predictions
        sentiment_test_predictions = pd.read_csv(ARTIFACT_DIR / "sentiment_test_predictions.csv")
        
        # Load session summary
        with open(ARTIFACT_DIR / "session_summary.json", "r", encoding="utf-8") as f:
            session_summary = json.load(f)
        
        session_summary_text = session_summary.pop("summary_text", "")
        
        return {
            "sentiment_metrics": sentiment_metrics,
            "sentiment_test_predictions": sentiment_test_predictions,
            "session_summary": session_summary,
            "session_summary_text": session_summary_text,
        }
    except Exception as e:
        print(f"⚠️ Error loading NLP assets: {e}")
        return {
            "sentiment_metrics": {},
            "sentiment_test_predictions": pd.DataFrame(),
            "session_summary": {},
            "session_summary_text": "",
        }


def main() -> None:
    """Main execution."""
    print("=" * 70)
    print("📊 GENERATING NLP VISUALIZATIONS FOR YOUTUBE SENTIMENT ANALYSIS")
    print("=" * 70)
    
    # Load data
    print("\n1️⃣  Loading YouTube chat data...")
    df = load_youtube_data()
    print(f"   ✓ Loaded {len(df)} comments")
    
    # Label with sentiment
    print("\n2️⃣  Inferring sentiment labels...")
    labeled_df = build_labeled_dataset(df)
    sentiment_counts = labeled_df["sentiment_label"].value_counts()
    print(f"   ✓ Sentiment distribution:")
    for sentiment, count in sentiment_counts.items():
        pct = count / len(labeled_df) * 100
        print(f"     - {sentiment}: {count} ({pct:.1f}%)")
    
    # Train model
    print("\n3️⃣  Training sentiment classification model...")
    pipeline, metrics, test_predictions = train_sentiment_model(labeled_df)
    print(f"   ✓ Model trained:")
    print(f"     - Accuracy: {metrics['accuracy']:.3f}")
    print(f"     - Precision: {metrics['precision_macro']:.3f}")
    print(f"     - Recall: {metrics['recall_macro']:.3f}")
    print(f"     - F1-Score: {metrics['f1_macro']:.3f}")
    
    # Build session summary
    print("\n4️⃣  Building session summary...")
    session_summary = build_session_summary(labeled_df)
    summary_text = session_summary.pop("extractive_summary", "")
    print(f"   ✓ Session summary built:")
    print(f"     - Total comments: {session_summary['total_comments']}")
    print(f"     - Unique commenters: {session_summary['unique_commenters']}")
    print(f"     - Top keywords: {', '.join([k['keyword'] for k in session_summary['top_keywords'][:5]])}")
    
    # Save artifacts
    print("\n5️⃣  Saving NLP artifacts...")
    save_nlp_artifacts(pipeline, metrics, test_predictions, session_summary, summary_text)
    
    # Create visualizations (for reference)
    print("\n6️⃣  Creating visualizations...")
    visualizations = create_sentiment_visualizations(labeled_df, metrics)
    print(f"   ✓ Created {len(visualizations)} visualization objects")
    
    print("\n" + "=" * 70)
    print("✅ NLP VISUALIZATIONS GENERATION COMPLETE!")
    print("=" * 70)
    print("\n📍 Next steps:")
    print("   1. Run the app: streamlit run app_lapisai.py")
    print("   2. Login with credentials: Admin123 / 12345678")
    print("   3. Navigate to the NLP section to see sentiment analysis")
    print("=" * 70)


if __name__ == "__main__":
    main()
