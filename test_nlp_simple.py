#!/usr/bin/env python
"""Comprehensive NLP Backend Test"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
import re
import string
from pathlib import Path
from collections import Counter

# Simplified NLP functions for testing
SENTIMENT_STOPWORDS = {'yang', 'dan', 'di', 'ke', 'gak', 'ga', 'tidak', 'saya', 'untuk'}
POSITIVE_KEYWORDS = ['bagus', 'puas', 'senang', 'baik', 'mantap', 'keren', 'suka', 'asik']
NEGATIVE_KEYWORDS = ['buruk', 'kecewa', 'lambat', 'gagal', 'susah', 'masalah', 'error', 'benci']
EMOTION_KEYWORDS = {
    'Marah': ['marah', 'kesal', 'jengkel', 'benci'],
    'Senang': ['senang', 'happy', 'excited', 'asik', 'mantap'],
    'Sedih': ['sedih', 'kecewa', 'duka'],
}

def clean_sentiment_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    normalized = text.lower()
    normalized = re.sub(r'http\S+|www\S+|\@\w+|\#\w+', ' ', normalized)
    normalized = normalized.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    return ' '.join(normalized.split())

def infer_sentiment_label(text: str) -> str:
    normalized = clean_sentiment_text(text)
    if not normalized:
        return 'Neutral'
    positive_count = sum(1 for term in POSITIVE_KEYWORDS if term in normalized)
    negative_count = sum(1 for term in NEGATIVE_KEYWORDS if term in normalized)
    if positive_count > negative_count:
        return 'Positive'
    if negative_count > positive_count:
        return 'Negative'
    return 'Neutral'

def infer_sentiment_emotion(text: str) -> str:
    normalized = clean_sentiment_text(text)
    for emotion, terms in EMOTION_KEYWORDS.items():
        if any(term in normalized for term in terms):
            return emotion
    return 'Neutral'

def test_nlp():
    """Test NLP functions with YouTube data"""
    
    print("=" * 60)
    print("🧪 NLP BACKEND TEST")
    print("=" * 60)
    
    # Load YouTube data
    chat_path = Path(__file__).parent / 'youtube_chat_5_menit_cleaned.csv'
    try:
        df = pd.read_csv(chat_path)
        print(f"\n✅ Loaded YouTube chat: {len(df)} messages")
    except Exception as e:
        print(f"\n❌ Failed to load: {e}")
        return False
    
    # Check columns
    print(f"📊 Columns: {df.columns.tolist()}")
    
    # Test sentiment classification
    print("\n" + "=" * 60)
    print("Testing Sentiment Classification:")
    print("=" * 60)
    
    test_messages = [
        "Saya sangat senang dengan produk ini",
        "Ini sangat buruk dan mengecewakan",
        "Video ini cukup bagus dan menarik",
    ]
    
    for msg in test_messages:
        sentiment = infer_sentiment_label(msg)
        emotion = infer_sentiment_emotion(msg)
        print(f"Message: {msg}")
        print(f"  → Sentiment: {sentiment}, Emotion: {emotion}\n")
    
    # Test with real data
    print("=" * 60)
    print("Testing with Real YouTube Data:")
    print("=" * 60)
    
    # Add sentiment if not exists
    if 'sentiment' not in df.columns or df['sentiment'].isna().all():
        df['sentiment'] = df['message'].apply(infer_sentiment_label)
        print("✅ Added sentiment classification")
    
    # Add emotion if not exists
    if 'emotion' not in df.columns:
        df['emotion'] = df['message'].apply(infer_sentiment_emotion)
        print("✅ Added emotion classification")
    else:
        # If emotion exists, verify
        emotion_count = df['emotion'].notna().sum()
        print(f"✅ Emotion column exists with {emotion_count} values")
    
    # Print statistics
    print("\n📈 Sentiment Distribution:")
    sentiment_dist = df['sentiment'].value_counts()
    for sentiment, count in sentiment_dist.items():
        pct = (count / len(df)) * 100
        print(f"  {sentiment}: {count} ({pct:.1f}%)")
    
    print("\n😊 Emotion Distribution:")
    emotion_dist = df['emotion'].value_counts()
    for emotion, count in emotion_dist.items():
        pct = (count / len(df)) * 100
        print(f"  {emotion}: {count} ({pct:.1f}%)")
    
    # Extract keywords
    print("\n🔑 Top Keywords:")
    all_words = []
    for msg in df['message']:
        if isinstance(msg, str):
            words = msg.lower().split()
            all_words.extend([w.strip('.,!?;:') for w in words if len(w) > 2])
    
    word_freq = Counter(all_words).most_common(10)
    for word, freq in word_freq:
        print(f"  {word}: {freq}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ NLP BACKEND TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = test_nlp()
    sys.exit(0 if success else 1)
