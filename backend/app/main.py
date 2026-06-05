from __future__ import annotations

import ast
import json
import os
import pickle
import re
import string
import time
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ========== NLP LIBRARY IMPORTS ==========
from dotenv import load_dotenv
import emoji
import nltk
from nltk.corpus import stopwords
from transformers import pipeline
from googleapiclient.discovery import build

# ========== LOCAL INDOBERT IMPORTS ==========
from indobert_summarizer import IndoBERTSummarizationEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENGINEERED_FEATURES_PATH = PROJECT_ROOT / "engineered_features" / "lapisai_engineered_features.csv"
ENSEMBLE_PREDICTIONS_PATH = PROJECT_ROOT / "model_results" / "ensemble_predictions.csv"
EVALUATION_METRICS_PATH = PROJECT_ROOT / "model_results" / "evaluation_metrics.csv"
PREPROCESSED_DIR = PROJECT_ROOT / "preprocessed_data"
TRAINED_MODELS_DIR = PROJECT_ROOT / "trained_models" / "plan_specific"
CHAT_DATA_PATH = PROJECT_ROOT / "youtube_chat_5_menit_cleaned.csv"
NLP_ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "nlp"

FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app = FastAPI(title="Customer Churn & NLP API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== LOAD ENV & LOCAL INDOBERT ==========
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize local IndoBERT summarizer (no external APIs needed)
print("🚀 Initializing local IndoBERT summarization engine...")
try:
    summarizer_engine = IndoBERTSummarizationEngine(cache_enabled=True)
    health = summarizer_engine.health_check()
    print(f"✅ IndoBERT engine ready | {health}")
except Exception as e:
    print(f"⚠️ Warning initializing IndoBERT: {e}")
    summarizer_engine = None


class LoginRequest(BaseModel):
    username: str
    password: str

class PredictRequest(BaseModel):
    customer_id: str
    plan_type: str
    model_choice: Literal["XGBoost Only", "CatBoost Only", "Ensemble (Recommended)"] = "Ensemble (Recommended)"
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    overrides: Dict[str, float] = Field(default_factory=dict)

class ManualSentimentRequest(BaseModel):
    text: str = Field(default='', min_length=1)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return pd.read_csv(path)

@lru_cache(maxsize=1)
def load_engineered_df() -> pd.DataFrame:
    return _read_csv(ENGINEERED_FEATURES_PATH)

@lru_cache(maxsize=1)
def load_ensemble_df() -> pd.DataFrame:
    return _read_csv(ENSEMBLE_PREDICTIONS_PATH)

@lru_cache(maxsize=1)
def load_eval_df() -> pd.DataFrame:
    return _read_csv(EVALUATION_METRICS_PATH)

@lru_cache(maxsize=1)
def load_chat_df() -> pd.DataFrame:
    if not CHAT_DATA_PATH.exists():
        return pd.DataFrame(columns=['time', 'author', 'message'])
    return _read_csv(CHAT_DATA_PATH)

@lru_cache(maxsize=1)
def load_prediction_results() -> pd.DataFrame:
    engineered = load_engineered_df().reset_index(drop=True)
    results_path = PROJECT_ROOT / "model_results" / "final_predictions.csv"
    if results_path.exists():
        results = _read_csv(results_path).reset_index(drop=True)
    else:
        results = load_ensemble_df().reset_index(drop=True)

    limit = min(len(engineered), len(results))
    engineered_subset = engineered.iloc[:limit].copy()
    results_subset = results.iloc[:limit].copy()
    
    # Merge dengan suffix untuk menghindari conflict
    merged = pd.concat([engineered_subset, results_subset], axis=1)

    merged["customer_id"] = merged["customer_id"].astype(str)
    merged["plan_type"] = merged["plan_type"].astype(str).str.capitalize()
    merged["plan"] = merged["plan"].astype(str).str.capitalize() if "plan" in merged.columns else merged["plan_type"]
    
    actual_col = "actual_churn" if "actual_churn" in merged.columns else "actual"
    proba_col = "churn_probability" if "churn_probability" in merged.columns else "ensemble_proba"
    pred_col = "prediction_threshold_0.50" if "prediction_threshold_0.50" in merged.columns else "ensemble_prediction"
    
    merged["actual"] = merged[actual_col].astype(int)
    merged["ensemble_proba"] = merged[proba_col].astype(float)
    merged["ensemble_prediction"] = merged[pred_col].astype(int)
    
    # Ensure xgb_proba and cat_proba exist
    if "xgb_proba" not in merged.columns:
        if "xgb_probability" in merged.columns:
            merged["xgb_proba"] = merged["xgb_probability"].astype(float)
        else:
            merged["xgb_proba"] = merged["ensemble_proba"]
        
    if "cat_proba" not in merged.columns:
        if "cat_probability" in merged.columns:
            merged["cat_proba"] = merged["cat_probability"].astype(float)
        else:
            merged["cat_proba"] = merged["ensemble_proba"]
    else:
        merged["cat_proba"] = merged["cat_proba"].astype(float)
        
    merged["xgb_proba"] = merged["xgb_proba"].astype(float)
    merged["risk_level"] = merged["ensemble_proba"].apply(risk_label)
    return merged

@lru_cache(maxsize=1)
def load_preprocessing_info() -> Dict[str, List[str]]:
    info: Dict[str, List[str]] = {}
    for plan in ("starter", "professional", "enterprise"):
        info_path = PREPROCESSED_DIR / f"{plan}_preprocessing_info.json"
        if not info_path.exists():
            continue
        data = json.loads(info_path.read_text(encoding="utf-8"))
        features = ast.literal_eval(data.get("features_selected", "[]"))
        info[plan.capitalize()] = [str(x) for x in features]
    return info

@lru_cache(maxsize=6)
def load_models(plan_type: str) -> Dict[str, Any]:
    models: Dict[str, Any] = {}
    plan = plan_type.strip().lower()
    for name in ("xgboost", "catboost"):
        path = TRAINED_MODELS_DIR / f"{plan}_{name}.pkl"
        if path.exists():
            with path.open("rb") as f:
                models[name] = pickle.load(f)
    return models


# ==============================================================================
# ======================== NLP CORE (LOCAL INDOBERT ONLY) ========================
# ==============================================================================

@lru_cache(maxsize=1)
def get_nlp_components():
    """Load IndoBERT model and stopwords (Cached in memory for API speed)"""
    print("Membaca model IndoBERT ke dalam memori...")
    indobert = pipeline(
        "sentiment-analysis",
        model="mdhugol/indonesia-bert-sentiment-classification",
        tokenizer="mdhugol/indonesia-bert-sentiment-classification"
    )
    
    nltk_data_local = NLP_ARTIFACTS_DIR / "nltk_data"
    try:
        nltk.download('stopwords', quiet=True)
        stop_words_eng = set(stopwords.words('english'))
    except Exception:
        stop_words_eng = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and'}

    # Menambahkan artefak demojize (Face, Tears, Joy) agar dibuang dari analisis Keyword
    stop_words_eng.update({'face', 'tears', 'joy', 'with', 'smiling', 'sweat', 'loudly', 'crying', 'rolling', 'eyes', 'heavy', 'heart', 'hands', 'folded', 'fire'})

    stop_words_indo = {
        'yg', 'di', 'ke', 'dari', 'ini', 'itu', 'dan', 'atau', 'tapi', 'yang', 'buat', 'sama', 'kok', 'sih', 'nya', 'aja', 'kalo', 
        'udah', 'gak', 'ga', 'ada', 'untuk', 'dengan', 'dalam', 'pada', 'juga', 'sudah', 'saya', 'dia', 'mereka', 'kita', 'kami',
        'kamu', 'aku', 'bisa', 'tidak', 'ya', 'yaudah', 'saja', 'belum', 'kalau', 'jadi', 'lagi', 'terus', 'biar', 'pas', 'kan',
        'lebih', 'paling', 'baru', 'sekarang', 'banyak', 'sangat', 'sekali', 'memang', 'pasti', 'karena', 'seperti', 'apa', 'siapa',
        'bagaimana', 'kenapa', 'kapan', 'dimana', 'mana', 'dong', 'deh', 'lah', 'pun', 'gini', 'gitu', 'begini', 'begitu',
        'mah', 'nah', 'loh', 'nih', 'tuh', 'eh', 'oh', 'ah', 'ih', 'uh', 'bgt', 'banget', 'gw', 'gua', 'lu', 'lo', 'emang',
        'dgn', 'klo', 'karna', 'krn', 'jd', 'jgn', 'jangan', 'bkn', 'bukan', 'bs', 'tp', 'dpt', 'dapet', 'org', 'orang', 'gk', 'tetap'
    }
    context_noise = {'video', 'youtube', 'apple', 'macbook', 'neo', 'laptop', 'david', 'gadgetin', 'bang', 'review', 'hp', 'handphone', 'smartphone'}
    all_stopwords = stop_words_eng.union(stop_words_indo).union(context_noise)
    
    return indobert, all_stopwords

def get_video_id(url: str) -> Optional[str]:
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def scrape_youtube_comments(video_id: str, max_comments: int = 2000) -> List[Dict[str, Any]]:
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY tidak ditemukan di .env")
        
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    comments = []
    try:
        request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
        while request and len(comments) < max_comments:
            response = request.execute()
            for item in response['items']:
                snippet = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'time': snippet['publishedAt'],
                    'author': snippet['authorDisplayName'],
                    'message': snippet['textDisplay']
                })
            if 'nextPageToken' in response:
                request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText", pageToken=response['nextPageToken'])
            else:
                break
        return comments
    except Exception as e:
        raise ValueError(f"Gagal mengambil data dari YouTube API: {str(e)}")

def clean_text(text: str, stopwords_set: set) -> str:
    if not isinstance(text, str): return ""
    # Hapus emoji sepenuhnya sebelum diproses (mencegah demojize leaking)
    if hasattr(emoji, 'replace_emoji'):
        text = emoji.replace_emoji(text, replace='')
    else:
        text = emoji.demojize(text)
        text = re.sub(r':[a-zA-Z_]+:', '', text)
        
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|\@\w+|\#\w+', ' ', text)
    text = text.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    tokens = text.split()
    return " ".join([w for w in tokens if w not in stopwords_set and len(w) > 2])

def classify_sentiment(raw_text: str, model, stopwords_set) -> str:
    cleaned_text = clean_text(raw_text, stopwords_set)
    try:
        result = model(cleaned_text[:512])[0]
        if result['label'] == "LABEL_0": return "Positive"
        elif result['label'] == "LABEL_1": return "Neutral"
        else: return "Negative"
    except Exception:
        return "Neutral"

def classify_sentiment_rule_based(raw_text: str) -> str:
    text = clean_text(raw_text, set())
    positive_hints = {'bagus', 'mantap', 'keren', 'suka', 'senang', 'terbaik', 'hebat', 'puas', 'helpful', 'mantul', 'gooo', 'asik'}
    negative_hints = {'buruk', 'jelek', 'kecewa', 'lambat', 'parah', 'gagal', 'benci', 'marah', 'susah', 'ribet', 'spam', 'lemot'}
    tokens = set(text.split())
    if tokens & negative_hints:
        return 'Negative'
    if tokens & positive_hints:
        return 'Positive'
    return 'Neutral'

EMOTION_KEYWORDS = {
    'Annoyance': ['marah', 'kesal', 'jengkel', 'annoy', 'ngambek', 'risih', 'benci', 'jelek', 'buruk', 'gagal', 'mahal', 'overpriced', 'scam', 'lemot', 'parah', 'males', 'nyebelin', 'kecewa', 'sampah'],
    'Excitement': ['senang', 'happy', 'excited', 'asik', 'mantap', 'hebat', 'wah', 'seru', 'bagus', 'keren', 'berguna', 'membantu', 'gokil', 'kece', 'suka', 'terbaik', 'top', 'wih', 'menyala'],
    'Sadness': ['sedih', 'kecewa', 'duka', 'galau', 'sayang', 'menangis', 'sad', 'nangis', 'huhu', 'yah', 'rugi'],
}

def infer_sentiment_emotion(text: str, sentiment: str) -> str:
    normalized = text.lower()
    for emotion, terms in EMOTION_KEYWORDS.items():
        if any(term in normalized for term in terms):
            return emotion
    # Logika fallback: jika sentimen kuat, arahkan ke emosi agar grafik tidak kosong
    if sentiment == 'Negative': return 'Annoyance'
    if sentiment == 'Positive': return 'Excitement'
    return 'Neutral'

def build_sentiment_keywords(messages: pd.Series, stopwords_set: set, top_n: int = 7) -> List[Dict[str, Any]]:
    counter = Counter()
    for message in messages.dropna().astype(str):
        for token in clean_text(message, stopwords_set).split():
            if len(token) >= 3:
                counter[token] += 1

    results = []
    positive_hints = ['bagus', 'puas', 'mantap', 'keren', 'suka', 'terbaik', 'mudah', 'membantu']
    negative_hints = ['buruk', 'kecewa', 'lambat', 'gagal', 'error', 'mahal', 'jelek', 'bug', 'susah']
    
    for word, freq in counter.most_common(top_n):
        w_type = 'Neutral'
        if word in positive_hints: w_type = 'Positive'
        elif word in negative_hints: w_type = 'Negative'
        results.append({'word': word, 'freq': int(freq), 'type': w_type})
    return results

def generate_indobert_summary(df: pd.DataFrame) -> str:
    """Generate summary menggunakan local IndoBERT (no external APIs)"""
    if not summarizer_engine:
        return None
    
    try:
        pos_df = df[df['sentiment'] == 'Positive']
        neg_df = df[df['sentiment'] == 'Negative']
        
        # Get sample texts
        pos_texts = pos_df['message'].dropna().head(5).tolist()
        neg_texts = neg_df['message'].dropna().head(5).tolist()
        
        pos_summary = ""
        neg_summary = ""
        
        # Summarize positive feedback
        if pos_texts:
            combined_pos = " ".join(pos_texts)
            pos_summary = summarizer_engine.summarize_text(combined_pos, max_length=100, min_length=30)
        
        # Summarize negative feedback
        if neg_texts:
            combined_neg = " ".join(neg_texts)
            neg_summary = summarizer_engine.summarize_text(combined_neg, max_length=100, min_length=30)
        
        pos_count = len(pos_df)
        neg_count = len(neg_df)
        total = len(df)
        
        summary = f"""
📊 **Ringkasan Analisis Sentimen (IndoBERT Local Processing)**

1. **Apa yang Paling Disukai (Demands):**
Berdasarkan {pos_count} komentar positif: {pos_summary or 'Audiens memberikan respons positif terhadap produk/layanan.'}

2. **Apa yang Dikeluhkan (Pain Points):**
Dari {neg_count} komentar negatif: {neg_summary or 'Audiens memiliki beberapa keluhan yang perlu diperhatikan.'}

3. **Kesimpulan Akhir:**
Dari total {total} feedback, sentimen positif: {pos_count/total*100:.1f}%, negatif: {neg_count/total*100:.1f}%, netral: {(total-pos_count-neg_count)/total*100:.1f}%.
"""
        return summary.strip()
    
    except Exception as e:
        print(f"⚠️ IndoBERT summary generation failed: {e}")
        return None

def generate_extractive_summary(df: pd.DataFrame, stopwords_set: set) -> str:
    pos_df = df[df['sentiment'] == 'Positive']
    neg_df = df[df['sentiment'] == 'Negative']
    
    pos_words = []
    for msg in pos_df['message']:
        words = [w.strip() for w in str(msg).lower().split() if len(w) > 2 and w not in stopwords_set]
        pos_words.extend(words)
            
    neg_words = []
    for msg in neg_df['message']:
        words = [w.strip() for w in str(msg).lower().split() if len(w) > 2 and w not in stopwords_set]
        neg_words.extend(words)
            
    top_pos = [w[0] for w in Counter(pos_words).most_common(7)] if pos_words else ["(data positif kurang)"]
    top_neg = [w[0] for w in Counter(neg_words).most_common(7)] if neg_words else ["(data negatif kurang)"]
    dominant = df['sentiment'].mode()[0].upper() if not df.empty else "NETRAL"
    
    return f"""
📊 **Ringkasan Analisis Sentimen (Local NLP Processing)**

1. **Apa yang Paling Disukai (Demands):**
Berdasarkan analisis {len(pos_df)} komentar positif, audiens merespons dengan sangat baik pada topik seputar: **{', '.join(top_pos).upper()}**. 

2. **Apa yang Dikeluhkan (Pain Points):**
Dari {len(neg_df)} komentar negatif, keluhan dan kritik audiens sangat mengerucut pada kata kunci: **{', '.join(top_neg).upper()}**. Hal ini harus menjadi perhatian utama.

3. **Kesimpulan Akhir:**
Secara keseluruhan, sentimen audiens saat ini didominasi oleh respons **{dominant}**.
"""

def create_sentiment_analysis_payload(df: pd.DataFrame) -> Dict[str, Any]:
    indobert, all_stopwords = get_nlp_components()
    df['message'] = df['message'].astype(str)
    
    # NLP INFERENCE
    sentiments = []
    emotions = []
    for msg in df['message']:
        sentiment = classify_sentiment(msg, indobert, all_stopwords)
        emotion = infer_sentiment_emotion(msg, sentiment)
        sentiments.append(sentiment)
        emotions.append(emotion)
        
    df['sentiment'] = sentiments
    df['emotion'] = emotions

    # EXPORT KE CSV OTOMATIS
    try:
        output_dir = PROJECT_ROOT / "artifacts" / "nlp"
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / "gadgetin_2000_comments_analyzed.csv"
        df.to_csv(csv_path, index=False)
        print(f"✅ Berhasil menyimpan {len(df)} komentar ke CSV: {csv_path}")
    except Exception as e:
        print(f"⚠️ Gagal menyimpan CSV: {e}")

    total = len(df)
    positive = int((df['sentiment'] == 'Positive').sum())
    negative = int((df['sentiment'] == 'Negative').sum())
    neutral = int((df['sentiment'] == 'Neutral').sum())

    sentiment_counts = {
        'positive': positive,
        'negative': negative,
        'neutral': neutral,
    }

    # PRIORITIZED LLM SUMMARIZATION: INDOBERT LOCAL (No External APIs)
    executive_summary = ""
    
    # Use local IndoBERT for all summarization (no external APIs needed)
    print("🤖 Using local IndoBERT for summary generation...")
    executive_summary = generate_indobert_summary(df)
    
    if not executive_summary:
        print("📊 Fallback to local extractive NLP...")
        executive_summary = generate_extractive_summary(df, all_stopwords)

    raw_feedback = []
    for _, row in df.head(15).iterrows():
        raw_feedback.append({
            'time': str(row.get('time', '')), 
            'author': str(row.get('author', 'Unknown')),
            'message': str(row.get('message', '')),
            'sentiment': str(row.get('sentiment', 'Neutral')),
            'emotion': str(row.get('emotion', 'Neutral')),
        })

    emotion_counts = Counter(df['emotion'])
    emotion_distribution = []
    for label in ['Neutral', 'Excitement', 'Annoyance', 'Sadness']:
        emotion_distribution.append({'label': label, 'value': int(emotion_counts.get(label, 0))})

    # BUAT TREND DATA YANG HALUS (10 Titik Kronologis)
    try:
        trend_df = df.copy()
        trend_df['time'] = pd.to_datetime(trend_df['time'], errors='coerce')
        trend_df = trend_df.sort_values('time').reset_index(drop=True)
        # Bagi data menjadi 10 bagian waktu (chunks) agar grafik selalu halus
        trend_df['chunk'] = pd.qcut(np.arange(len(trend_df)), q=10, labels=False, duplicates='drop')
        grouped = trend_df.groupby(['chunk', 'sentiment']).size().unstack(fill_value=0).reset_index()
        
        for col in ['Positive', 'Negative', 'Neutral']:
            if col not in grouped.columns:
                grouped[col] = 0
                
        trend_data = []
        for idx, row in grouped.iterrows():
            trend_data.append({
                'time': f"Fase {int(row['chunk']) + 1}",
                'Positive': int(row['Positive']),
                'Negative': int(row['Negative']),
                'Neutral': int(row['Neutral'])
            })
    except Exception as e:
        print(f"Error memproses trend data: {e}")
        trend_data = []

    return {
        'executive_summary': executive_summary,
        'total_feedback': total,
        'sentiment_distribution': sentiment_counts,
        'emotion_distribution': emotion_distribution,
        'keywords': build_sentiment_keywords(df['message'], all_stopwords, top_n=7),
        'raw_feedback': raw_feedback,
        'trend_data': trend_data,
    }

def create_sentiment_analysis_payload_fast(df: pd.DataFrame) -> Dict[str, Any]:
    """Fast fallback sentiment payload that avoids loading large NLP models."""
    df = df.copy()
    df['message'] = df['message'].astype(str)

    sentiments = []
    emotions = []
    for msg in df['message']:
        sentiment = classify_sentiment_rule_based(msg)
        emotion = infer_sentiment_emotion(msg, sentiment)
        sentiments.append(sentiment)
        emotions.append(emotion)

    df['sentiment'] = sentiments
    df['emotion'] = emotions

    all_stopwords = set()
    try:
        all_stopwords.update(stopwords.words('english'))
    except Exception:
        pass
    all_stopwords.update({
        'yg', 'di', 'ke', 'dari', 'ini', 'itu', 'dan', 'atau', 'tapi', 'yang', 'buat', 'sama', 'kok', 'sih', 'nya', 'aja', 'kalo',
        'udah', 'gak', 'ga', 'ada', 'untuk', 'dengan', 'dalam', 'pada', 'juga', 'sudah', 'saya', 'dia', 'mereka', 'kita', 'kami',
        'kamu', 'aku', 'bisa', 'tidak', 'ya', 'yaudah', 'saja', 'belum', 'kalau', 'jadi', 'lagi', 'terus', 'biar', 'pas', 'kan',
        'lebih', 'paling', 'baru', 'sekarang', 'banyak', 'sangat', 'sekali', 'memang', 'pasti', 'karena', 'seperti', 'apa', 'siapa',
        'bagaimana', 'kenapa', 'kapan', 'dimana', 'mana', 'dong', 'deh', 'lah', 'pun', 'gini', 'gitu', 'begini', 'begitu',
        'mah', 'nah', 'loh', 'nih', 'tuh', 'eh', 'oh', 'ah', 'ih', 'uh', 'bgt', 'banget', 'gw', 'gua', 'lu', 'lo', 'emang',
        'dgn', 'klo', 'karna', 'krn', 'jd', 'jgn', 'jangan', 'bkn', 'bukan', 'bs', 'tp', 'dpt', 'dapet', 'org', 'orang', 'gk', 'tetap'
    })

    total = len(df)
    positive = int((df['sentiment'] == 'Positive').sum())
    negative = int((df['sentiment'] == 'Negative').sum())
    neutral = int((df['sentiment'] == 'Neutral').sum())

    sentiment_counts = {'positive': positive, 'negative': negative, 'neutral': neutral}
    executive_summary = generate_extractive_summary(df, all_stopwords)

    raw_feedback = []
    for _, row in df.head(15).iterrows():
        raw_feedback.append({
            'time': str(row.get('time', '')),
            'author': str(row.get('author', 'Unknown')),
            'message': str(row.get('message', '')),
            'sentiment': str(row.get('sentiment', 'Neutral')),
            'emotion': str(row.get('emotion', 'Neutral')),
        })

    emotion_counts = Counter(df['emotion'])
    emotion_distribution = []
    for label in ['Neutral', 'Excitement', 'Annoyance', 'Sadness']:
        emotion_distribution.append({'label': label, 'value': int(emotion_counts.get(label, 0))})

    try:
        trend_df = df.copy()
        trend_df['time'] = pd.to_datetime(trend_df['time'], errors='coerce')
        trend_df = trend_df.sort_values('time').reset_index(drop=True)
        trend_df['chunk'] = pd.qcut(np.arange(len(trend_df)), q=10, labels=False, duplicates='drop')
        grouped = trend_df.groupby(['chunk', 'sentiment']).size().unstack(fill_value=0).reset_index()
        for col in ['Positive', 'Negative', 'Neutral']:
            if col not in grouped.columns:
                grouped[col] = 0
        trend_data = []
        for _, row in grouped.iterrows():
            trend_data.append({
                'time': f"Fase {int(row['chunk']) + 1}",
                'Positive': int(row['Positive']),
                'Negative': int(row['Negative']),
                'Neutral': int(row['Neutral'])
            })
    except Exception:
        trend_data = []

    return {
        'executive_summary': executive_summary,
        'total_feedback': total,
        'sentiment_distribution': sentiment_counts,
        'emotion_distribution': emotion_distribution,
        'keywords': build_sentiment_keywords(df['message'], all_stopwords, top_n=7),
        'raw_feedback': raw_feedback,
        'trend_data': trend_data,
    }

def load_local_sentiment_source(max_rows: int = 2000) -> pd.DataFrame:
    """Load a local sentiment dataset as a fallback when YouTube scraping is unavailable."""
    candidate_paths = [
        CHAT_DATA_PATH,
        PROJECT_ROOT / "artifacts" / "nlp" / "gadgetin_2000_comments_analyzed.csv",
    ]

    for path in candidate_paths:
        if not path.exists():
            continue

        df = pd.read_csv(path).copy()
        if "message" not in df.columns:
            if "text" in df.columns:
                df = df.rename(columns={"text": "message"})
            else:
                continue

        if "time" not in df.columns:
            df["time"] = pd.Timestamp.now().isoformat()
        if "author" not in df.columns:
            df["author"] = "LocalCache"

        return df.loc[:, [c for c in ["time", "author", "message"] if c in df.columns]].head(max_rows)

    fallback_rows = [
        {"time": "2026-01-01 10:00:00", "author": "@sample1", "message": "Bagus banget, informatif dan jelas."},
        {"time": "2026-01-01 10:00:01", "author": "@sample2", "message": "Kurang cepat, agak membosankan."},
        {"time": "2026-01-01 10:00:02", "author": "@sample3", "message": "Mantap, sangat membantu!"},
    ]
    return pd.DataFrame(fallback_rows)

# ==============================================================================
# ============================== CHURN FUNCTIONS ===============================
# ==============================================================================

def normalize_plan(plan_type: str) -> str:
    plan = plan_type.strip().lower()
    if plan == "starter": return "Starter"
    if plan == "professional": return "Professional"
    if plan == "enterprise": return "Enterprise"
    return plan_type.strip().title()

def selected_features_for_plan(plan_type: str) -> List[str]:
    info = load_preprocessing_info()
    plan = normalize_plan(plan_type)
    if plan in info: return info[plan]
    for key, value in info.items():
        if key.lower() == plan.lower(): return value
    raise HTTPException(status_code=404, detail=f"No training features found for plan: {plan_type}")

def apply_overrides(row: pd.Series, overrides: Dict[str, float]) -> pd.Series:
    mapping = {
        "payment_delay_days": "payment_delay_days_mean", "days_since_login": "days_since_last_login", "avg_nps_score": "avg_nps_score",
        "feature_adoption_pct": "feature_adoption_pct_mean", "annual_value": "annual_value", "avg_monthly_usage_hours": "avg_monthly_usage_hours",
        "total_tickets": "total_tickets", "payment_health_score": "payment_health_score",
    }
    updated = row.copy()
    for key, value in overrides.items():
        col = mapping.get(key, key)
        if col in updated.index: updated[col] = value
    return updated

def risk_label(prob: float) -> str:
    if prob > 0.7: return "VERY HIGH"
    if prob > 0.5: return "HIGH"
    if prob > 0.3: return "MEDIUM"
    return "LOW"

def evaluation_label(actual: int, predicted: int) -> tuple[str, str]:
    if actual == 1 and predicted == 1: return "TRUE_POSITIVE", "Model correctly identified this customer as churned."
    if actual == 0 and predicted == 0: return "TRUE_NEGATIVE", "Model correctly predicted this customer will be retained."
    if actual == 1 and predicted == 0: return "FALSE_NEGATIVE", "Model missed this churn case."
    return "FALSE_POSITIVE", "Model predicted churn but customer actually retained."

def compute_risk_factors(row: pd.Series) -> List[Dict[str, Any]]:
    candidates = []
    names = [
        ("Days Since Login", "days_since_last_login", True), ("Payment Delay Days", "payment_delay_days_mean", True), ("Critical Ticket Ratio", "critical_ticket_ratio", True),
        ("Unresolved Ratio", "unresolved_ratio", True), ("Revenue at Risk", "revenue_at_risk", True), ("Avg NPS Score", "avg_nps_score", False),
        ("Feature Adoption %", "feature_adoption_pct_mean", False), ("Payment Health Score", "payment_health_score", False), ("Monthly Usage Hours", "avg_monthly_usage_hours", False),
    ]
    for label, col, higher_is_riskier in names:
        if col not in row.index or pd.isna(row[col]): continue
        value = float(row[col])
        score = value if higher_is_riskier else -value
        candidates.append({"label": label, "value": value, "score": score})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:3]

def classification_summary(actual: pd.Series, predicted: pd.Series) -> Dict[str, Any]:
    actual_series = actual.astype(int)
    predicted_series = predicted.astype(int)
    tp = int(((actual_series == 1) & (predicted_series == 1)).sum())
    tn = int(((actual_series == 0) & (predicted_series == 0)).sum())
    fp = int(((actual_series == 0) & (predicted_series == 1)).sum())
    fn = int(((actual_series == 1) & (predicted_series == 0)).sum())
    total = int(len(actual_series))

    accuracy = (tp + tn) / total if total else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

    return {
        "accuracy": round(float(accuracy), 4), "recall": round(float(recall), 4), "precision": round(float(precision), 4),
        "f1": round(float(f1), 4), "counts": {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "total": total},
    }

def build_risk_distribution(plan_df: pd.DataFrame) -> List[Dict[str, Any]]:
    risk_levels = pd.cut(plan_df["ensemble_proba"], bins=[0, 0.3, 0.5, 0.7, 1.0], labels=["Low", "Medium", "High", "Very High"], include_lowest=True)
    counts = risk_levels.value_counts().reindex(["Low", "Medium", "High", "Very High"], fill_value=0)
    return [{"label": label, "value": int(counts[label])} for label in counts.index]

def build_probability_distribution(plan_df: pd.DataFrame, bins: int = 10) -> Dict[str, Any]:
    values = plan_df["ensemble_proba"].astype(float).to_numpy()
    if len(values) == 0: return {"bins": [], "counts": []}
    counts, edges = np.histogram(values, bins=bins, range=(0, 1))
    labels = [f"{edges[i]:.1f}-{edges[i + 1]:.1f}" for i in range(len(edges) - 1)]
    return {"bins": labels, "counts": [int(value) for value in counts]}

def build_feature_dominance(plan_df: pd.DataFrame) -> List[Dict[str, Any]]:
    feature_order = ["nps_trend", "is_on_time_sum", "feature_adoption_pct_mean", "churned", "ensemble_prediction", "cat_proba", "xgb_proba", "ensemble_proba", "actual"]
    available = [column for column in feature_order if column in plan_df.columns]
    if not available: return []
    correlations = plan_df[available].corrwith(plan_df["actual"]).abs().sort_values()
    return [{"label": label, "value": round(float(correlations[label]), 4)} for label in correlations.index]

def build_revenue_at_risk(plan_df: pd.DataFrame) -> Dict[str, Any]:
    working = plan_df.copy()
    working["risk_category"] = pd.cut(working["ensemble_proba"], bins=[0, 0.3, 0.5, 1.0], labels=["Low", "Medium", "High"], include_lowest=True)
    grouped = working.groupby("risk_category", observed=False)["annual_value"].agg(["sum", "count", "mean"])
    grouped = grouped.reindex(["Low", "Medium", "High"]).fillna(0)
    rows = []
    for category, row in grouped.iterrows():
        rows.append({"risk_category": category, "total_value": round(float(row["sum"]), 4), "customer_count": int(row["count"]), "avg_value_per_customer": round(float(row["mean"]), 4)})
    high_risk_df = working[working["ensemble_proba"] > 0.5]
    high_risk_value = float(high_risk_df["annual_value"].sum())
    total_value = float(working["annual_value"].sum())
    pct_of_total = (high_risk_value / total_value * 100) if total_value else 0.0
    return {"value_at_high_risk": round(high_risk_value, 4), "pct_of_total_value": round(float(pct_of_total), 4), "high_risk_customers": int(len(high_risk_df)), "rows": rows}

def build_top_customers(plan_df: pd.DataFrame, limit: int = 15) -> List[Dict[str, Any]]:
    top_df = plan_df.sort_values("ensemble_proba", ascending=False).head(limit).copy()
    result: List[Dict[str, Any]] = []
    for _, row in top_df.iterrows():
        result.append({
            "customer_id": str(row.get("customer_id", "")), "plan": str(row.get("plan", row.get("plan_type", ""))), "tenure_months": round(float(row.get("tenure_months", 0)), 4),
            "annual_value": round(float(row.get("annual_value", 0)), 4), "nps": round(float(row.get("avg_nps_score", 0)), 4), "risk_pct": round(float(row.get("ensemble_proba", 0)) * 100, 1),
        })
    return result

def build_model_comparison(plan_df: pd.DataFrame) -> Dict[str, Any]:
    xgb_pred = (plan_df["xgb_proba"] > 0.5).astype(int)
    cat_pred = (plan_df["cat_proba"] > 0.5).astype(int)
    ensemble_pred = plan_df["ensemble_prediction"].astype(int)
    return {
        "high_risk_detected": [{"model": "XGBoost", "value": int((plan_df["xgb_proba"] > 0.5).sum())}, {"model": "CatBoost", "value": int((plan_df["cat_proba"] > 0.5).sum())}, {"model": "Ensemble", "value": int((plan_df["ensemble_proba"] > 0.5).sum())}],
        "scorecards": {"xgboost": classification_summary(plan_df["actual"], xgb_pred), "catboost": classification_summary(plan_df["actual"], cat_pred), "ensemble": classification_summary(plan_df["actual"], ensemble_pred)},
    }

def build_recommendation_actions(row: pd.Series, probability: float, evaluation: str) -> List[str]:
    actions: List[str] = []
    if probability > 0.7: actions.append("Contact customer immediately by phone and trigger a retention case.")
    elif probability > 0.5: actions.append("Schedule a proactive success call within 24 hours.")
    else: actions.append("Monitor the account and keep a light-touch check-in cadence.")
    if float(row.get("payment_delay_days_mean", 0)) > 15: actions.append("Review payment delays and offer a temporary billing resolution plan.")
    if float(row.get("total_tickets", 0)) > 2: actions.append("Escalate open support tickets to the technical owner.")
    if float(row.get("avg_nps_score", 0)) < 6: actions.append("Run an executive check-in to recover satisfaction and product fit.")
    if evaluation == "FALSE_POSITIVE": actions.append("Validate the latest activity before offering discounts to avoid unnecessary incentive spend.")
    return actions[:4]

def build_dashboard_summary_stats(engine: pd.DataFrame, predictions: pd.DataFrame) -> List[Dict[str, Any]]:
    risk_counts, _ = np.histogram(predictions["ensemble_proba"].astype(float).to_numpy(), bins=7, range=(0, 1))
    revenue_counts, _ = np.histogram(engine["revenue_at_risk"].astype(float).to_numpy(), bins=7)
    nps_values = engine["avg_nps_score"].astype(float).to_numpy()
    if len(nps_values):
        nps_counts, _ = np.histogram(nps_values, bins=7, range=(0, 10))
        avg_nps = float(engine["avg_nps_score"].mean())
        nps_highlight = min(len(nps_counts) - 1, max(0, int((avg_nps / 10) * len(nps_counts))))
    else:
        nps_counts = np.array([0, 0, 0, 0, 0, 0, 0])
        avg_nps = 0.0
        nps_highlight = 0
    return [
        {"id": "risk", "label": "Customers at Risk", "value": f"{int((predictions['ensemble_proba'] > 0.5).sum()):,}", "chartData": [int(value) for value in risk_counts.tolist()], "color": "indigo"},
        {"id": "revenue", "label": "Revenue at Risk", "value": f"${float(engine['revenue_at_risk'].sum()):,.0f}", "chartData": [int(value) for value in revenue_counts.tolist()], "color": "indigo"},
        {"id": "nps", "label": "Average NPS", "value": f"{avg_nps:.1f}", "chartData": [int(value) for value in nps_counts.tolist()], "highlight": nps_highlight, "color": "indigo"},
    ]

def build_dashboard_customer_churn(limit_per_status: int = 10) -> List[Dict[str, Any]]:
    predictions = load_prediction_results().copy()
    churned_df = predictions[predictions["actual"] == 1].sort_values("ensemble_proba", ascending=False).head(limit_per_status)
    retained_df = predictions[predictions["actual"] == 0].sort_values("ensemble_proba", ascending=False).head(limit_per_status)
    combined = pd.concat([churned_df, retained_df], axis=0).head(limit_per_status * 2).copy()
    combined["status"] = np.where(combined["actual"] == 1, "Churned", "Not Churned")
    combined["type"] = combined["plan_type"].astype(str) + "/" + combined["contract_type"].astype(str)
    combined["score"] = combined["ensemble_proba"].map(lambda value: f"{float(value):.3f}")
    return combined.loc[:, ["customer_id", "type", "score", "status"]].rename(columns={"customer_id": "id"}).to_dict(orient="records")

def get_plan_summary() -> Dict[str, Any]:
    engine = load_engineered_df()
    plans = sorted(engine["plan_type"].dropna().astype(str).str.capitalize().unique().tolist())
    items = []
    for plan in plans:
        plan_df = engine[engine["plan_type"].astype(str).str.capitalize() == plan].copy()
        churned = int(plan_df["churned"].sum())
        total = int(len(plan_df))
        items.append({"plan": plan, "total_customers": total, "churned": churned, "retained": total - churned, "churn_rate": round((churned / total) if total else 0, 4)})
    return {"plans": items}

# ==============================================================================
# ================================= ENDPOINTS ==================================
# ==============================================================================

@app.get("/health")
def health() -> Dict[str, str]: return {"status": "ok"}

@app.post("/api/auth/login")
def api_auth_login(payload: LoginRequest) -> Dict[str, Any]:
    if not payload.username.strip() or not payload.password.strip(): raise HTTPException(status_code=400, detail="Username and password are required")
    return {"token": "mock-jwt-token", "user": {"username": payload.username, "role": "admin"}}

@app.get("/api/plans")
def api_plans() -> Dict[str, Any]: return get_plan_summary()

@app.get("/api/customers")
def api_customers(plan_type: Optional[str] = None, limit: int = 5000) -> Dict[str, Any]:
    engine = load_engineered_df()
    df = engine.copy()
    if plan_type: df = df[df["plan_type"].astype(str).str.capitalize() == normalize_plan(plan_type)]
    df = df.sort_values("customer_id")
    if limit is not None and limit > 0: df = df.head(limit)
    rows = []
    for _, row in df.iterrows():
        rows.append({"customer_id": row.get("customer_id"), "plan_type": row.get("plan_type"), "contract_type": row.get("contract_type"), "status": "Churned" if int(row.get("churned", 0)) else "Not Churned"})
    return {"plan_type": normalize_plan(plan_type) if plan_type else None, "customers": rows}

@app.get("/api/churn/analysis")
def api_churn_analysis(plan_type: Optional[str] = None) -> Dict[str, Any]:
    predictions = load_prediction_results()
    
    # Normalize plan names
    predictions["plan"] = predictions["plan"].astype(str).str.capitalize()
    available_plans = sorted(predictions["plan"].unique().tolist())
    
    plan = normalize_plan(plan_type) if plan_type else available_plans[0]
    
    # Find plan_df, try multiple columns
    if "plan" in predictions.columns:
        plan_df = predictions[predictions["plan"].astype(str).str.capitalize() == plan].copy()
    elif "plan_type" in predictions.columns:
        plan_df = predictions[predictions["plan_type"].astype(str).str.capitalize() == plan].copy()
    else:
        plan_df = predictions.copy()
    
    if plan_df.empty: raise HTTPException(status_code=404, detail=f"No churn analysis data found for plan: {plan}")

    plan_summary = {
        "plan_type": plan, "total_customers": int(len(plan_df)), "actual_churned": int(plan_df["actual"].sum()), "high_risk_customers": int((plan_df["ensemble_proba"] > 0.5).sum()),
        "model_accuracies": {
            "xgboost": classification_summary(plan_df["actual"], (plan_df["xgb_proba"] > 0.5).astype(int))["accuracy"],
            "catboost": classification_summary(plan_df["actual"], (plan_df["cat_proba"] > 0.5).astype(int))["accuracy"],
            "ensemble": classification_summary(plan_df["actual"], plan_df["ensemble_prediction"])["accuracy"],
        },
    }
    overall = {
        "risk_distribution": build_risk_distribution(plan_df), "probability_distribution": build_probability_distribution(plan_df),
        "feature_dominance": build_feature_dominance(plan_df), "revenue_at_risk": build_revenue_at_risk(plan_df),
        "top_risk_customers": build_top_customers(plan_df, limit=15), "top15_customers": build_top_customers(predictions, limit=15),
    }
    evaluation = classification_summary(plan_df["actual"], plan_df["ensemble_prediction"])
    confusion = evaluation["counts"]
    model_comparison = build_model_comparison(plan_df)

    return {
        "plan_type": plan, "customers": sorted(plan_df["customer_id"].astype(str).unique().tolist()), "plan_summary": plan_summary, "overall": overall,
        "evaluation": {
            "scorecard": {"accuracy": evaluation["accuracy"], "recall": evaluation["recall"], "precision": evaluation["precision"], "f1": evaluation["f1"]},
            "confusion_matrix": {"labels": ["Retained", "Churned"], "predicted_labels": ["Retained", "Churned"], "matrix": [[confusion["tn"], confusion["fp"]], [confusion["fn"], confusion["tp"]]], "counts": confusion},
            "model_comparison": model_comparison,
        },
    }

@app.get("/api/dashboard/summary")
def api_dashboard_summary() -> Dict[str, Any]:
    engine = load_engineered_df()
    predictions = load_prediction_results()
    summary_stats = build_dashboard_summary_stats(engine, predictions)
    customer_churn = build_dashboard_customer_churn(limit_per_status=10)
    feedback_data = [
        {"id": "C-0267", "text": "UI responsif, prediksi sangat akurat.", "nps": 9, "sentiment": "Positive"},
        {"id": "C-0091", "text": "Performa lambat saat muat dataset.", "nps": 5, "sentiment": "Negative"},
        {"id": "C-0176", "text": "Analisis sentimen NLP luar biasa!", "nps": 8, "sentiment": "Positive"},
    ]
    return {"summaryStats": summary_stats, "customerChurnData": customer_churn, "totalCustomers": int(len(engine)), "feedbackData": feedback_data, "plans": get_plan_summary()["plans"]}

@app.get("/api/customer/{customer_id}/features")
def api_customer_features(customer_id: str, plan_type: Optional[str] = None) -> Dict[str, Any]:
    engine = load_engineered_df()
    customer = engine[engine["customer_id"].astype(str) == customer_id]
    if customer.empty: raise HTTPException(status_code=404, detail="Customer not found")
    row = customer.iloc[0]
    selected_plan = normalize_plan(plan_type or str(row.get("plan_type", "")))
    return {
        "customer_id": customer_id, "plan_type": selected_plan, "actual_status": int(row.get("churned", 0)), "actual_status_text": "YES (Churned)" if int(row.get("churned", 0)) else "NO (Retained)",
        "profile": {
            "contract_type": row.get("contract_type", "N/A"), "annual_value": float(row.get("annual_value", 0)), "avg_monthly_usage_hours": float(row.get("avg_monthly_usage_hours", 0)),
            "feature_adoption_pct_mean": float(row.get("feature_adoption_pct_mean", 0)), "days_since_last_login": float(row.get("days_since_last_login", 0)),
            "total_tickets": float(row.get("total_tickets", 0)), "dunning_event_count": float(row.get("dunning_event_count", 0)), "critical_ticket_ratio": float(row.get("critical_ticket_ratio", 0)),
            "payment_health_score": float(row.get("payment_health_score", 0)), "avg_nps_score": float(row.get("avg_nps_score", 0)), "payment_delay_days_mean": float(row.get("payment_delay_days_mean", 0)),
            "revenue_at_risk": float(row.get("revenue_at_risk", 0)),
        },
    }

@app.post("/api/predict/churn")
def api_predict_churn(payload: PredictRequest) -> Dict[str, Any]:
    engine = load_engineered_df()
    customer = engine[engine["customer_id"].astype(str) == payload.customer_id]
    if customer.empty: raise HTTPException(status_code=404, detail="Customer not found")
    row = apply_overrides(customer.iloc[0], payload.overrides)
    plan = normalize_plan(payload.plan_type)
    features = selected_features_for_plan(plan)
    models = load_models(plan)
    if not models: raise HTTPException(status_code=404, detail=f"Models not found for plan {plan}")
    try: x = row[features].fillna(0).astype(float).to_numpy().reshape(1, -1)
    except Exception as exc: raise HTTPException(status_code=400, detail=f"Failed to build feature vector: {exc}") from exc

    preds: Dict[str, float] = {}
    if payload.model_choice in ("XGBoost Only", "Ensemble (Recommended)") and "xgboost" in models: preds["xgboost"] = float(models["xgboost"].predict_proba(x)[0][1])
    if payload.model_choice in ("CatBoost Only", "Ensemble (Recommended)") and "catboost" in models: preds["catboost"] = float(models["catboost"].predict_proba(x)[0][1])

    if payload.model_choice == "XGBoost Only" and "xgboost" in preds: final_pred, model_name = preds["xgboost"], "XGBoost"
    elif payload.model_choice == "CatBoost Only" and "catboost" in preds: final_pred, model_name = preds["catboost"], "CatBoost"
    elif "xgboost" in preds and "catboost" in preds: final_pred, model_name = 0.6 * preds["xgboost"] + 0.4 * preds["catboost"], "Ensemble"
    elif "xgboost" in preds: final_pred, model_name = preds["xgboost"], "XGBoost"
    elif "catboost" in preds: final_pred, model_name = preds["catboost"], "CatBoost"
    else: raise HTTPException(status_code=400, detail="No valid predictions could be generated")

    actual_status = int(row.get("churned", 0))
    predicted_churn = 1 if final_pred > payload.threshold else 0
    evaluation, explanation = evaluation_label(actual_status, predicted_churn)
    
    return {
        "customer_id": payload.customer_id, "plan_type": plan, "model": model_name, "probability": round(final_pred, 4), "threshold": round(float(payload.threshold), 4),
        "risk_level": risk_label(final_pred), "actual_status": actual_status, "actual_status_text": "YES (Churned)" if actual_status else "NO (Retained)",
        "predicted_status": predicted_churn, "evaluation": evaluation, "explanation": explanation, "model_predictions": preds, "risk_factors": compute_risk_factors(row),
        "recommendation_actions": build_recommendation_actions(row, final_pred, evaluation),
        "customer_profile": { "contract_type": row.get("contract_type", "N/A"), "annual_value": float(row.get("annual_value", 0)), "avg_nps_score": float(row.get("avg_nps_score", 0)), }
    }

@app.get("/api/sentiment/analysis")
def api_sentiment_analysis() -> Dict[str, Any]:
    try:
        # Jika API key tidak tersedia, gunakan dataset lokal sebagai fallback.
        if YOUTUBE_API_KEY:
            video_id = "MBRtCiE7-v8"
            max_comments = 2000
            raw_comments = scrape_youtube_comments(video_id, max_comments)
            if not raw_comments:
                raise HTTPException(status_code=400, detail="Gagal mengambil komentar dari YouTube.")
            df = pd.DataFrame(raw_comments)
            payload = create_sentiment_analysis_payload(df)
            payload["data_source"] = "youtube_api"
            return payload
        else:
            df = load_local_sentiment_source(max_rows=2000)
            if df.empty:
                raise HTTPException(status_code=400, detail="Tidak ada data sentimen lokal yang tersedia.")
            payload = create_sentiment_analysis_payload_fast(df)
            payload["data_source"] = "local_fallback"
            return payload
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        print(f"Error pada proses NLP utama: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis sentimen: {str(exc)}")

@app.get("/api/sentiment/export")
def api_sentiment_export():
    file_path = NLP_ARTIFACTS_DIR / "gadgetin_2000_comments_analyzed.csv"
    if file_path.exists():
        return FileResponse(path=file_path, filename="gadgetin_2000_comments_analyzed.csv", media_type="text/csv")
    raise HTTPException(status_code=404, detail="File CSV belum tersedia. Silakan jalankan analisis terlebih dahulu.")

@app.post("/api/sentiment/manual")
def api_sentiment_manual(payload: ManualSentimentRequest) -> Dict[str, Any]:
    try:
        indobert, all_stopwords = get_nlp_components()
        sentiment = classify_sentiment(payload.text, indobert, all_stopwords)
        emotion = infer_sentiment_emotion(payload.text, sentiment)
        return {
            "text": payload.text,
            "sentiment": sentiment,
            "emotion": emotion,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis teks manual: {str(exc)}")