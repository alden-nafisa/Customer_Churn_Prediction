# 🚀 QUICK START GUIDE - Customer Churn Prediction with NLP Visualizations

## ⚡ 5-Minute Setup

### 1. Open Terminal/Command Prompt
```bash
cd C:\Users\HP14\Downloads\pbl6\Customer_Churn_Prediction
```

### 2. Initialize (One Time)
```bash
python setup_dashboard.py
```
This generates all NLP artifacts needed.

### 3. Start Dashboard
```bash
streamlit run app_lapisai.py
```

### 4. Open Browser
Navigate to: `http://localhost:8501`

### 5. Login
```
Username: Admin123
Password: 12345678
```

---

## 📊 What You Get

### Churn Prediction
- 🎯 Predict customer churn with 93% ROC-AUC
- 📈 View model performance metrics
- 🔍 Understand predictions with SHAP explainability

### NLP Sentiment Analysis (NEW!)
- 😊 Classify YouTube chat sentiment (Positive/Neutral/Negative)
- 📊 See model performance cards and charts
- 🏷️ Discover top keywords and themes
- 💭 Read representative comments
- 📋 Download predictions and summaries

---

## 🎨 Dashboard Navigation

```
Sidebar Controls:
├── 📊 Dashboard (Predict/Analysis/About)
├── 🤖 Model (XGBoost/CatBoost)
└── ⚠️ Risk threshold (0.10-0.90)
```

### Main Pages
1. **🔮 Predict** - Input customer data → Get churn risk
2. **📈 Analysis** - View model performance
3. **ℹ️ About** - Project information
4. *Advanced* - Full analysis with NLP

---

## 📁 Generated Files

After setup, you'll have:
```
artifacts/nlp/
├── naive_bayes_sentiment_pipeline.pkl    (Trained model)
├── sentiment_metrics.json                (Performance: 70%+ accuracy)
├── sentiment_test_predictions.csv        (100+ predictions)
└── session_summary.json                  (Keywords, comments, stats)
```

---

## 🎯 NLP Features at a Glance

| Feature | Description |
|---------|-------------|
| **Sentiment Classification** | Positive/Neutral/Negative labels for ~800 comments |
| **Model Performance** | Accuracy, Precision, Recall, F1-Score metrics |
| **Visualization** | Interactive Plotly charts and metrics cards |
| **Keywords** | Top 15 most frequent meaningful words |
| **Comments** | Representative examples for each sentiment |
| **Downloadable** | CSV predictions, JSON summary |

---

## 💡 Key Files

| File | Purpose |
|------|---------|
| `app_lapisai.py` | Main dashboard (1,400+ lines of Streamlit code) |
| `generate_nlp_visualizations.py` | NLP artifact generation |
| `setup_dashboard.py` | One-click initialization |
| `youtube_chat_5_menit_cleaned.csv` | Input data (800+ comments) |
| `NLP_VISUALIZATION_GUIDE.md` | Detailed documentation |

---

## 🔧 Customize (Optional)

### Change Sentiment Words
Edit `generate_nlp_visualizations.py`:
```python
POSITIVE_LEXICON = {"good", "great", "awesome", ...}
NEGATIVE_LEXICON = {"bad", "terrible", "awful", ...}
```

### Change Data Source
```python
DATA_PATH = "your_data.csv"
TEXT_COLUMN = "your_message_col"
```

### Adjust Model Parameters
```python
TEST_SIZE = 0.2                 # Train/test split
MAX_FEATURES = 10000            # TF-IDF features
```

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Artifacts not found" | Run `python setup_dashboard.py` |
| Module not found | `pip install streamlit pandas plotly scikit-learn nltk` |
| Port already in use | `streamlit run app_lapisai.py --server.port 8502` |
| NLTK errors | `python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"` |

---

## 📊 Performance Summary

### Churn Model
- **Algorithm:** XGBoost (Recommended)
- **ROC-AUC:** 0.9304 (93%)
- **Accuracy:** 90.3%
- **Inference:** ~10ms per customer

### Sentiment Model  
- **Algorithm:** Naive Bayes + TF-IDF
- **Accuracy:** ~70-75%
- **Training Data:** 800 YouTube comments
- **Classes:** Positive, Neutral, Negative

---

## ✅ Verification Checklist

After setup, verify:
- [ ] No errors in `python setup_dashboard.py` output
- [ ] All files created in `artifacts/nlp/`
- [ ] Dashboard starts with `streamlit run app_lapisai.py`
- [ ] Login works with Admin123 / 12345678
- [ ] NLP section shows metrics and visualizations
- [ ] Can download CSV and JSON files

---

## 📖 Full Documentation

For detailed guide, see: `NLP_VISUALIZATION_GUIDE.md`

---

## 🎓 What You Learned

- ✅ Building ML pipelines with Streamlit
- ✅ Sentiment analysis with weak supervision
- ✅ NLP feature engineering (TF-IDF)
- ✅ Model evaluation and metrics
- ✅ Interactive dashboard development
- ✅ SHAP model explainability

---

## 🚀 Next Steps

1. ✅ Run setup and start dashboard
2. 📊 Explore the visualizations
3. 🔍 Make predictions and view SHAP explanations
4. 💾 Download results
5. 🎨 Customize lexicons/parameters
6. 🌐 Deploy to production (Streamlit Cloud, Docker)

---

**Status:** ✅ Ready to Run  
**Last Updated:** 2026-05  
**Questions?** Check `NLP_VISUALIZATION_GUIDE.md`
