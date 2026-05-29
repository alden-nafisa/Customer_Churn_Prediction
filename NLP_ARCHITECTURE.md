# 🏗️ NLP INTEGRATION ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                  │
│              http://localhost:3000                          │
├─────────────────────────────────────────────────────────────┤
│                   SentimentView.jsx (8 Components)          │
│                                                             │
│  1. AI Executive Summary  ──┐                              │
│  2. Raw Voice Quotes      ──┤                              │
│  3. Emotion Distribution  ──┤─→ HTTP GET /api/sentiment    │
│  4. Total Feedback        ──┤      /analysis               │
│  5. Sentiment & Keywords  ──┤    (Fetches Live Data)       │
│  6. Sentiment Trend       ──┤                              │
│  7. RAW CUSTOMER FEEDBACK ──┤                              │
│  8. Manual Sentiment Test ──┘                              │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP Request
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│              http://localhost:8000                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  API Endpoints:                                            │
│  • GET  /api/sentiment/analysis         (Main Endpoint)    │
│  • POST /api/sentiment/manual           (Custom Text)      │
│  • GET  /api/sentiment/messages         (Raw Messages)     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  create_sentiment_analysis_payload()                │   │
│  │                                                     │   │
│  │  1. Load youtube_chat_5_menit_cleaned.csv           │   │
│  │  2. Process 1348 messages                           │   │
│  │  3. Get sentiment from CSV                          │   │
│  │  4. Infer emotions using keywords                   │   │
│  │  5. Extract top keywords                            │   │
│  │  6. Build summary                                   │   │
│  │  7. Return complete payload                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  NLP Processing Functions                           │   │
│  │                                                     │   │
│  │  • clean_sentiment_text()                           │   │
│  │    → Remove URLs, normalize, lowercase              │   │
│  │                                                     │   │
│  │  • infer_sentiment_label()                          │   │
│  │    → Match against POSITIVE/NEGATIVE keywords      │   │
│  │    → Return: Positive | Negative | Neutral         │   │
│  │                                                     │   │
│  │  • infer_sentiment_emotion()                        │   │
│  │    → Match against EMOTION_KEYWORDS                │   │
│  │    → Return: Marah | Senang | Sedih | Neutral      │   │
│  │                                                     │   │
│  │  • build_sentiment_keywords()                       │   │
│  │    → Extract top 7 keywords with frequency          │   │
│  │    → Classify each as Positive/Negative/Neutral     │   │
│  │                                                     │   │
│  │  • build_sentiment_summary()                        │   │
│  │    → Generate AI summary (Indonesian)               │   │
│  │    → Include percentages and tone description       │   │
│  │                                                     │   │
│  │  • build_emotion_distribution()                     │   │
│  │    → Calculate emotion counts                       │   │
│  │    → Return ordered by: Senang, Marah, Sedih       │   │
│  │                                                     │   │
│  │  • build_raw_feedback()                             │   │
│  │    → Extract first 12 messages                      │   │
│  │    → Include confidence scores                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Keyword Dictionaries                               │   │
│  │                                                     │   │
│  │  POSITIVE_KEYWORDS: 50+ words                       │   │
│  │    bagus, puas, senang, baik, mantap, keren, suka  │   │
│  │    awesome, great, love, happy, worth, gokil, ajib │   │
│  │                                                     │   │
│  │  NEGATIVE_KEYWORDS: 50+ words                       │   │
│  │    buruk, kecewa, lambat, gagal, susah, masalah    │   │
│  │    error, benci, tidak suka, jengkel, marah, trash │   │
│  │                                                     │   │
│  │  EMOTION_KEYWORDS:                                  │   │
│  │    Marah: marah, kesal, jengkel, benci, geram...   │   │
│  │    Senang: senang, happy, excited, asik, mantap...│   │
│  │    Sedih: sedih, kecewa, duka, galau, sad...       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ Fetch Data
                           │
┌──────────────────────────▼──────────────────────────────────┐
│             DATA SOURCE (YouTube CSV)                       │
│                                                             │
│  📄 youtube_chat_5_menit_cleaned.csv                        │
│                                                             │
│  1,348 messages with:                                       │
│  • time: Message timestamp                                  │
│  • elapsed: Time since stream start                         │
│  • author: YouTube username                                 │
│  • message: Comment text                                    │
│  • sentiment: Positive | Negative | Neutral                │
│  • emotion: Marah | Senang | Sedih | Neutral               │
│                                                             │
│  Sentiment Distribution:                                    │
│  • Neutral: 1,284 (95.3%)                                   │
│  • Negative: 53 (3.9%)                                      │
│  • Positive: 11 (0.8%)                                      │
│                                                             │
│  Emotion Distribution:                                      │
│  • Neutral: 1,342 (99.6%)                                   │
│  • Senang: 4 (0.3%)                                         │
│  • Sedih: 2 (0.1%)                                          │
│  • Marah: 0 (0%)                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow

```
YouTube CSV (1348 messages)
    ↓
Backend loads data
    ↓
Sentiment classification (from CSV + inference)
    ↓
Emotion detection (keyword matching)
    ↓
Keyword extraction & analysis
    ↓
Summary generation
    ↓
Payload creation
    ↓
HTTP Response (/api/sentiment/analysis)
    ↓
Frontend receives data
    ↓
React components render:
  ✅ AI Executive Summary
  ✅ Raw Voice Quotes  
  ✅ Emotion Distribution
  ✅ Total Feedback
  ✅ Sentiment & Keywords
  ✅ Sentiment Trend
  ✅ RAW FEEDBACK (LIVE NLP)
  ✅ Manual Sentiment Test
```

## 🔄 Response Payload Structure

```json
{
  "executive_summary": "String - AI-generated summary",
  "total_feedback": 1348,
  "sentiment_distribution": {
    "positive": 0.8,
    "negative": 3.9,
    "neutral": 95.3,
    "positive_count": 11,
    "negative_count": 53,
    "neutral_count": 1284
  },
  "emotion_distribution": [
    {"label": "Senang", "value": 3},
    {"label": "Marah", "value": 0},
    {"label": "Sedih", "value": 2},
    {"label": "Neutral", "value": 1343}
  ],
  "keywords": [
    {"word": "bang", "freq": 297, "type": "Neutral"},
    {"word": "aku", "freq": 167, "type": "Neutral"},
    ...7 items total...
  ],
  "raw_feedback": [
    {
      "time": "2026-03-24 14:44:14",
      "elapsed": "0:00:00",
      "author": "@m0ndazee2",
      "message": "L thumbnail",
      "sentiment": "Neutral",
      "emotion": "Neutral",
      "confidence": "65%"
    },
    ...12 items total...
  ]
}
```

## 🎯 Key Features

✅ **Real YouTube Data** - Uses actual YouTube comment data
✅ **Multilingual Support** - Indonesian & English keywords
✅ **Emotion Detection** - Detects Marah, Senang, Sedih
✅ **Keyword Extraction** - Top keywords with frequency
✅ **AI Summary** - Generates descriptive summaries
✅ **Live Analysis** - Real-time manual sentiment testing
✅ **Complete Frontend** - 8 components displaying data
✅ **Consistent Data** - All messages have sentiment & emotion

## 📝 Notes

- Sentiment values are from YouTube CSV (pre-labeled)
- Emotions are inferred from message content using keyword matching
- Percentages are calculated at backend for accuracy
- All text is processed with Indonesian/English stopwords
- Confidence scores: 85% for Positive/Negative, 65% for Neutral
