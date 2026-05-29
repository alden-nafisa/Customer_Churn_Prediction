#!/usr/bin/env python
"""Add emotion detection to YouTube chat data"""

import pandas as pd
import re
import string

PROJECT_ROOT = r'c:\Users\Dhanny\Documents\CODING\Customer_Churn_Prediction'
CHAT_DATA_PATH = f'{PROJECT_ROOT}\youtube_chat_5_menit_cleaned.csv'

SENTIMENT_STOPWORDS = {
    'yg', 'di', 'ke', 'dari', 'ini', 'itu', 'dan', 'atau', 'tapi', 'yang', 'buat', 'sama', 'kok', 'sih', 'nya', 'aja',
    'kalo', 'udah', 'gak', 'ga', 'ada', 'untuk', 'dengan', 'dalam', 'pada', 'juga', 'sudah', 'saya', 'dia', 'mereka',
}

EMOTION_KEYWORDS = {
    'Marah': ['marah', 'kesal', 'jengkel', 'annoy', 'ngambek', 'risih', 'benci', 'amarah', 'geram', 'emosi'],
    'Senang': ['senang', 'happy', 'excited', 'asik', 'mantap', 'hebat', 'wah', 'seru', 'suka', 'love'],
    'Sedih': ['sedih', 'kecewa', 'duka', 'galau', 'sayang', 'menangis', 'down', 'sad'],
}

def clean_sentiment_text(text: str) -> str:
    """Preprocess text"""
    if not isinstance(text, str):
        return ""
    normalized = text.lower()
    normalized = re.sub(r'http\S+|www\S+|\@\w+|\#\w+', ' ', normalized)
    normalized = normalized.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    return ' '.join(normalized.split())

def infer_sentiment_emotion(text: str) -> str:
    """Infer emotion from text"""
    normalized = clean_sentiment_text(text)
    for emotion, terms in EMOTION_KEYWORDS.items():
        if any(term in normalized for term in terms):
            return emotion
    return 'Neutral'

# Load data
df = pd.read_csv(CHAT_DATA_PATH)

# Add emotion column
print("Adding emotion detection...")
df['emotion'] = df['message'].apply(infer_sentiment_emotion)

# Save back
df.to_csv(CHAT_DATA_PATH, index=False)
print(f"✅ Updated {CHAT_DATA_PATH}")
print(f"Emotion distribution:")
print(df['emotion'].value_counts())
print("\nSample:")
print(df[['message', 'sentiment', 'emotion']].head(10))
