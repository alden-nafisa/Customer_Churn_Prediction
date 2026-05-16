# 📊 Customer Churn Prediction Dashboard with NLP Sentiment Analysis

## Overview

This dashboard provides an integrated solution for:
1. **Customer Churn Prediction** - XGBoost/CatBoost ensemble models with >80% ROC-AUC
2. **NLP Sentiment Analysis** - YouTube chat analysis with weak supervision
3. **Session Summarization** - Automated keyword extraction and representative comment selection

---

## 📁 Project Structure

```
Customer_Churn_Prediction/
├── app_lapisai.py                        # Main Streamlit dashboard
├── generate_nlp_visualizations.py        # NLP artifact generation
├── setup_dashboard.py                    # Setup and initialization script
├── train_sentiment_model.py              # Sentiment model training (alternative)
├── youtube_chat_5_menit_cleaned.csv      # YouTube data source
│
├── artifacts/
│   ├── nlp/                             # NLP artifacts (generated)
│   │   ├── naive_bayes_sentiment_pipeline.pkl
│   │   ├── sentiment_metrics.json
│   │   ├── sentiment_test_predictions.csv
│   │   └── session_summary.json
│   └── [other model artifacts...]
│
└── [other project files]
```

---

## 🚀 Quick Start

### Step 1: Setup Environment
```bash
cd C:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction

# Install dependencies (if needed)
pip install streamlit pandas plotly scikit-learn joblib nltk numpy

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Step 2: Generate NLP Artifacts
```bash
python setup_dashboard.py
```

This script will:
- ✅ Load YouTube chat data
- ✅ Infer sentiment labels using lexicon-based weak supervision
- ✅ Train Naive Bayes sentiment classifier (TF-IDF features)
- ✅ Generate session summary and keywords
- ✅ Save all artifacts to `artifacts/nlp/`

### Step 3: Run the Dashboard
```bash
streamlit run app_lapisai.py
```

### Step 4: Login
- **Username:** `Admin123`
- **Password:** `12345678`

---

## 📊 Dashboard Features

### 1. Churn Prediction Module (`🔮 Predict`)
- **Input:** Customer behavioral features
- **Output:** Churn probability with risk classification
- **Model Options:** XGBoost (recommended) or CatBoost
- **Features:** SHAP explanations for feature importance

### 2. Model Analysis (`📈 Analysis`)
- Performance metrics (ROC-AUC, Accuracy, F1)
- Model diagnostics and calibration curves
- Feature importance analysis
- Confusion matrix visualization

### 3. Advanced Analysis (`Advanced Dashboard`)
- Comprehensive risk assessment
- Customer ranking by churn probability
- SHAP-based local explanations
- Action recommendations

### 4. NLP Sentiment Analysis (`📊 NLP Tab`)

#### Sentiment Model Performance
- **Algorithm:** Naive Bayes with TF-IDF vectorization
- **Data Split:** 80/20 (stratified)
- **Sentiments:** Positive, Neutral, Negative
- **Metrics Displayed:**
  - Accuracy: Overall correct predictions
  - Precision (macro): Per-class precision average
  - Recall (macro): Per-class recall average
  - F1-Score (macro): Harmonic mean of precision/recall

#### Key Visualizations
1. **Model Performance Cards** - Four KPI metrics at a glance
2. **Performance Bar Chart** - Visual comparison of metrics
3. **Test Predictions Preview** - Sample model outputs with actual/predicted sentiments
4. **Sentiment Distribution** - Breakdown of Positive/Neutral/Negative comments
5. **Top Keywords** - Frequency analysis with interactive visualization
6. **Representative Comments** - Examples for each sentiment class

#### Session Summary Components
- **Total Comments:** Count of all messages analyzed
- **Unique Users:** Number of distinct commenters
- **Sentiment Distribution:** Percentage breakdown
- **Extractive Summary:** Automated key sentences
- **Top Keywords:** Most frequent meaningful terms (filtered stopwords)
- **Representative Comments:** One example per sentiment class

---

## 🎯 NLP Implementation Details

### Weak Supervision Strategy
The sentiment labels are inferred automatically using **lexicon-based weak supervision**:

```python
POSITIVE_LEXICON = {
    "good", "great", "amazing", "mantap", "keren", "bagus", ...
}

NEGATIVE_LEXICON = {
    "bad", "jelek", "buruk", "gagal", "sedih", "marah", ...
}
```

**Process:**
1. Clean text (lowercase, remove URLs, special characters)
2. Tokenize into words
3. Count positive and negative word hits
4. Assign label based on dominant sentiment

### Feature Engineering (Text → Numbers)
- **TF-IDF Vectorization:** Term frequency-inverse document frequency
- **N-grams:** Unigrams and bigrams (1-2 word combinations)
- **Min Document Frequency:** 2 (must appear in at least 2 documents)
- **Max Features:** 10,000 (top features selected)

### Model Architecture
```
Raw Text
  ↓
[TF-IDF Vectorizer] → (10,000 features)
  ↓
[Naive Bayes Classifier] → (3 classes: Positive/Neutral/Negative)
  ↓
Sentiment Prediction + Probability
```

---

## 📥 Download Options

The dashboard provides downloadable artifacts:

1. **Sentiment Test Predictions** (CSV)
   - Message, True Sentiment, Predicted Sentiment
   - Use for further analysis or validation

2. **Session Summary** (JSON)
   - Structured data: keywords, comments, stats
   - Programmatic access to summary data

3. **NLP Visualizations** (JSON/CSV)
   - Raw data for custom analysis
   - Integration with external tools

---

## 🔧 Configuration & Customization

### Modify Sentiment Lexicons
Edit `generate_nlp_visualizations.py`:
```python
POSITIVE_LEXICON = {
    "your_positive_word",  # Add more words
    "another_positive_word",
}

NEGATIVE_LEXICON = {
    "your_negative_word",  # Add more words
    "another_negative_word",
}
```

### Adjust Model Parameters
In `generate_nlp_visualizations.py`:
```python
POSITIVE_LEXICON = { ... }      # Change positive words
NEGATIVE_LEXICON = { ... }      # Change negative words
TEST_SIZE = 0.2                 # Change train/test split
MAX_FEATURES = 10000            # Change feature count
```

### Change Data Source
Update `DATA_PATH` and column names:
```python
DATA_PATH = PROJECT_ROOT / "your_data.csv"
TEXT_COLUMN = "message"         # Your message column
AUTHOR_COLUMN = "author"        # Your author column
TIME_COLUMN = "time"            # Your timestamp column
```

---

## 📈 Interpretation Guide

### Sentiment Metrics Explained
- **Accuracy:** (TP + TN) / Total - Overall correctness
- **Precision:** TP / (TP + FP) - Reliability of positive predictions
- **Recall:** TP / (TP + FN) - Ability to find all positives
- **F1-Score:** 2 × (Precision × Recall) / (Precision + Recall) - Balance of both

### Good Performance Indicators
- ✅ Accuracy > 0.80
- ✅ F1-Score > 0.75
- ✅ Balanced Precision and Recall (no huge gaps)
- ✅ Keywords make intuitive sense
- ✅ Representative comments match their sentiment

### Potential Issues
- ❌ Low recall (missing positive sentiments)
- ❌ Low precision (false positives)
- ❌ Irrelevant keywords
- ❌ Misclassified representative comments

---

## 🐛 Troubleshooting

### Issue: "Artifact sentiment belum ditemukan"
**Solution:** Run `python setup_dashboard.py` to generate artifacts

### Issue: NLTK stopwords not found
**Solution:** Run in Python shell:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

### Issue: ModuleNotFoundError
**Solution:** Install missing package:
```bash
pip install [package_name]
```

### Issue: YouTube data file not found
**Solution:** Ensure `youtube_chat_5_menit_cleaned.csv` is in the project root

### Issue: Dashboard won't start
**Solution:** Check port conflicts:
```bash
# Run on different port
streamlit run app_lapisai.py --server.port 8502
```

---

## 📊 Performance Benchmarks

### Churn Prediction Models
| Model | ROC-AUC | Accuracy | Precision | Recall | F1-Score |
|-------|---------|----------|-----------|--------|----------|
| XGBoost | 0.9304 | 0.903 | 0.9218 | 0.9674 | 0.944 |
| CatBoost | 0.9292 | 0.908 | 0.9241 | 0.9702 | 0.947 |

### NLP Sentiment Model
| Metric | Value |
|--------|-------|
| Accuracy | ~0.70-0.75* |
| Precision (macro) | ~0.68-0.72* |
| Recall (macro) | ~0.67-0.71* |
| F1-Score (macro) | ~0.67-0.71* |

*Values depend on YouTube data quality and lexicon coverage

---

## 🔐 Security Notes

- **Credentials:** Default credentials (Admin123/12345678) are for demo only
- **Production:** Update credentials in `AUTH_USERNAME` and `AUTH_PASSWORD`
- **API Keys:** Keep environment variables secure (SUPABASE_URL, SUPABASE_KEY)
- **Data:** YouTube data is treated as public (no sensitive personal information)

---

## 📚 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Dashboard UI** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn, XGBoost, CatBoost |
| **NLP** | NLTK, TF-IDF, Naive Bayes |
| **Visualizations** | Plotly, Matplotlib |
| **Model Explanation** | SHAP |
| **Serialization** | Joblib, JSON |

---

## 📖 File Reference

### Key Files
- `app_lapisai.py` - Main Streamlit application
- `generate_nlp_visualizations.py` - NLP pipeline
- `setup_dashboard.py` - Initialization script

### Generated Artifacts
- `artifacts/nlp/sentiment_metrics.json` - Model performance metrics
- `artifacts/nlp/sentiment_test_predictions.csv` - Test set predictions
- `artifacts/nlp/session_summary.json` - Session statistics
- `artifacts/nlp/naive_bayes_sentiment_pipeline.pkl` - Trained model

---

## 🎓 Learning Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Scikit-learn NLP Guide](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction)
- [NLTK Book - Text Processing](https://www.nltk.org/book/)
- [Weak Supervision Concepts](https://en.wikipedia.org/wiki/Weak_supervision)
- [SHAP Model Explainability](https://shap.readthedocs.io/)

---

## 📝 License & Attribution

This project demonstrates ML best practices for churn prediction and NLP sentiment analysis.
Adapt and extend for your use case!

---

## ✉️ Support

For issues or questions:
1. Check troubleshooting section above
2. Review generated artifacts in `artifacts/nlp/`
3. Examine console output for error messages
4. Verify all dependencies are installed

---

**Last Updated:** 2026-05  
**Version:** 1.0  
**Status:** ✅ Production Ready
