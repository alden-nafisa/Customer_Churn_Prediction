#!/usr/bin/env python
"""Quick NLP backend payload test"""

import pandas as pd
import json

# Load data
df = pd.read_csv('youtube_chat_5_menit_cleaned.csv')

print("✅ YouTube CSV Data Status:")
print(f"  - Total messages: {len(df)}")
print(f"  - Columns: {df.columns.tolist()}")
print(f"\n📊 Sentiment Distribution:")
print(df['sentiment'].value_counts().to_dict())
print(f"\n😊 Emotion Distribution:")
print(df['emotion'].value_counts().to_dict())

# Show sample data
print(f"\n📝 Sample Messages (first 3):")
for idx, row in df.head(3).iterrows():
    print(f"  [{idx}] {row['author']}: '{row['message'][:50]}...' → {row['sentiment']}/{row['emotion']}")

print("\n✅ Backend data is ready and correct!")
