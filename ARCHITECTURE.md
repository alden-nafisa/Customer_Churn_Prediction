# 🏗️ System Architecture - Customer Churn Prediction Dashboard

## Overview

This document describes the complete architecture of the Customer Churn Prediction Dashboard with integrated NLP Sentiment Analysis visualizations.

---

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STREAMLIT DASHBOARD (app_lapisai.py)              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐         ┌──────────────────┐                  │
│  │   Login System   │         │ Sidebar Controls │                  │
│  │ (Authentication) │         │  - Page selector │                  │
│  └──────────────────┘         │  - Model chooser │                  │
│                               │  - Threshold     │                  │
│                               └──────────────────┘                  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  PAGE ROUTER                                 │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │  Predict         Analysis         About        Advanced      │   │
│  │  ┌─────────┐    ┌─────────┐     ┌─────────┐   ┌─────────┐   │   │
│  │  │ Manual  │    │ Model   │     │Project  │   │ Full    │   │   │
│  │  │ Input   │    │ Perf    │     │ Info    │   │ NLP     │   │   │
│  │  │ Form    │    │ Metrics │     │         │   │ + SHAP  │   │   │
│  │  │ + SHAP  │    │         │     │         │   │         │   │   │
│  │  └─────────┘    └─────────┘     └─────────┘   └─────────┘   │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │  NLP SENTIMENT ANALYSIS SECTION (render_nlp_section) │   │   │
│  │  ├──────────────────────────────────────────────────────┤   │   │
│  │  │                                                        │   │   │
│  │  │  Model Performance    │    Session Summary            │   │   │
│  │  │  ┌─────────────────┐  │    ┌──────────────────┐       │   │   │
│  │  │  │ Accuracy Card   │  │    │ Comments Count   │       │   │   │
│  │  │  │ Precision Card  │  │    │ Unique Users     │       │   │   │
│  │  │  │ Recall Card     │  │    │ Sentiment Dist   │       │   │   │
│  │  │  │ F1-Score Card   │  │    │ Extractive Summ  │       │   │   │
│  │  │  └─────────────────┘  │    └──────────────────┘       │   │   │
│  │  │                                                        │   │   │
│  │  │  Test Predictions     │    Top Keywords               │   │   │
│  │  │  ┌─────────────────┐  │    ┌──────────────────┐       │   │   │
│  │  │  │ 15-row Preview  │  │    │ Bar Chart        │       │   │   │
│  │  │  │ (expandable)    │  │    │ Frequency Data   │       │   │   │
│  │  │  └─────────────────┘  │    └──────────────────┘       │   │   │
│  │  │                                                        │   │   │
│  │  │  Representative Comments (by Sentiment)               │   │   │
│  │  │  ┌─────────────────────────────────────────────┐      │   │   │
│  │  │  │ Positive │ Neutral │ Negative │ ...         │      │   │   │
│  │  │  └─────────────────────────────────────────────┘      │   │   │
│  │  │                                                        │   │   │
│  │  └────────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. Initialization Flow

```
START
  │
  ├─→ load_assets()
  │   ├─→ Load XGBoost model (artifacts/xgb_model_calibrated.pkl)
  │   ├─→ Load CatBoost model (artifacts/catboost_model_calibrated.pkl)
  │   ├─→ Load SHAP explainer (artifacts/shap_explainer.pkl)
  │   └─→ Load feature names (artifacts/feature_names.pkl)
  │
  ├─→ load_nlp_assets() [CACHED]
  │   ├─→ Load sentiment_metrics.json
  │   ├─→ Load sentiment_test_predictions.csv
  │   ├─→ Load session_summary.json
  │   └─→ Return NLPAssets dictionary
  │
  ├─→ Render UI Components
  │   ├─→ Sidebar with controls
  │   └─→ Main page based on selection
  │
  └─→ Ready for interaction
```

### 2. NLP Artifact Generation Flow

```
generate_nlp_visualizations.py
  │
  ├─→ load_youtube_data()
  │   └─→ Read youtube_chat_5_menit_cleaned.csv
  │
  ├─→ build_labeled_dataset()
  │   └─→ infer_sentiment_label() for each message
  │       └─→ Apply POSITIVE_LEXICON / NEGATIVE_LEXICON
  │
  ├─→ train_sentiment_model()
  │   ├─→ Train/Test Split (80/20, stratified)
  │   ├─→ Build TF-IDF Vectorizer
  │   │   └─→ Bigrams (1,2)
  │   │   └─→ Min DF: 2
  │   │   └─→ Max Features: 10,000
  │   ├─→ Train Naive Bayes classifier
  │   └─→ Evaluate metrics (Accuracy, Precision, Recall, F1)
  │
  ├─→ build_session_summary()
  │   ├─→ Calculate session statistics
  │   ├─→ Extract top keywords
  │   ├─→ Get representative comments
  │   └─→ Build sentiment timeline
  │
  ├─→ create_sentiment_visualizations()
  │   ├─→ Sentiment distribution pie chart
  │   ├─→ Message length scatter plot
  │   └─→ Model performance bar chart
  │
  ├─→ save_nlp_artifacts()
  │   ├─→ Save pipeline.pkl
  │   ├─→ Save metrics.json
  │   ├─→ Save test_predictions.csv
  │   └─→ Save session_summary.json
  │
  └─→ Complete
```

### 3. Prediction Flow

```
User Input
  │
  ├─→ collect_form_values()
  │   └─→ Get all feature inputs
  │
  ├─→ build_single_prediction_output()
  │   ├─→ Get XGBoost prediction
  │   ├─→ Get CatBoost prediction
  │   ├─→ Select main model
  │   ├─→ Generate SHAP explanation
  │   └─→ Return comparison + local SHAP
  │
  ├─→ render_single_prediction_result()
  │   ├─→ Display prediction cards
  │   ├─→ Show model comparison
  │   ├─→ Plot SHAP values
  │   └─→ Provide action recommendation
  │
  └─→ Display results + downloads
```

---

## 📦 Component Breakdown

### A. Core Dashboard (app_lapisai.py)

**Main Functions:**
- `main()` - Entry point, authentication, page routing
- `load_assets()` - Load pre-trained models [CACHED]
- `load_nlp_assets()` - Load NLP artifacts [CACHED]
- `render_login_page()` - Authentication UI
- `render_predict_page()` - Manual prediction interface
- `render_analysis_page()` - Model diagnostics
- `render_nlp_section()` - **NEW** NLP visualizations

**Utility Functions:**
- `score_frame()` - Apply model to dataframe
- `kpi_cards()` - Display KPI metrics
- `explain_with_shap()` - SHAP visualizations
- `render_customer_navigator()` - Customer selection UI

**Lines of Code:** ~2,100 lines

---

### B. NLP Pipeline (generate_nlp_visualizations.py)

**Main Functions:**
- `load_youtube_data()` - Read CSV
- `build_labeled_dataset()` - Apply sentiment labels
- `infer_sentiment_label()` - Lexicon-based labeling
- `train_sentiment_model()` - Train Naive Bayes
- `build_session_summary()` - Extract statistics
- `create_sentiment_visualizations()` - Create charts
- `save_nlp_artifacts()` - Persist outputs
- `load_nlp_assets()` - Load for dashboard

**Key Features:**
- Weak supervision with dual lexicons
- TF-IDF vectorization
- Naive Bayes classifier
- Keyword extraction + representative comments

**Lines of Code:** ~550 lines

---

### C. Setup Script (setup_dashboard.py)

**Main Functions:**
- `main()` - Orchestrate entire setup
- System checks
- NLP artifact generation
- Package verification
- Instructions

**Lines of Code:** ~180 lines

---

## 🗂️ Data Structures

### NLPAssets TypedDict
```python
{
    "sentiment_metrics": {
        "naive_bayes": {
            "accuracy": 0.72,
            "precision_macro": 0.70,
            "recall_macro": 0.71,
            "f1_macro": 0.70,
            "confusion_matrix": [...],
            "classification_report": {...},
        },
        "label_strategy": {...},
        "training_strategy": {...},
    },
    "sentiment_test_predictions": DataFrame(
        columns=["message", "true_sentiment", "predicted_sentiment"]
    ),
    "session_summary": {
        "total_comments": 823,
        "unique_commenters": 156,
        "sentiment_distribution": {"Positive": 450, ...},
        "top_keywords": [{"keyword": "...", "frequency": 12}, ...],
        "representative_comments": [...],
    },
    "session_summary_text": "..."
}
```

### Model Metrics TypedDict
```python
{
    "xgboost": {
        "accuracy": 0.903,
        "precision": 0.9218,
        "recall": 0.9674,
        "f1": 0.944,
        "roc_auc": 0.9304,
        "pr_auc": 0.986,
    },
    "catboost": {...}
}
```

---

## 🔒 Security Architecture

```
┌─────────────────────────────────────────────────┐
│           STREAMLIT APPLICATION                  │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │        AUTHENTICATION LAYER               │   │
│  │  (Username/Password verification)         │   │
│  │  - Auth state in session_state            │   │
│  │  - Hardcoded for demo (update for prod)   │   │
│  └──────────────────────────────────────────┘   │
│                │                                 │
│                ├─→ AUTHENTICATED                │
│                │   - Access to all pages        │
│                │   - Can download data          │
│                │                                 │
│                └─→ NOT AUTHENTICATED             │
│                    - Show login page only       │
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │        SESSION MANAGEMENT                 │   │
│  │  - Cache models in st.cache_resource      │   │
│  │  - Cache data in st.cache_data            │   │
│  │  - Use session_state for UI state         │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │        DATA ACCESS CONTROL                │   │
│  │  - Models stored in /artifacts/           │   │
│  │  - CSV exports on download request        │   │
│  │  - No persistent file uploads             │   │
│  └──────────────────────────────────────────┘   │
│                                                   │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Considerations

### Local Development
```bash
streamlit run app_lapisai.py
```
- Single-user dev environment
- No authentication needed for testing
- Models loaded from local /artifacts/

### Production Deployment Options

#### 1. Streamlit Cloud
```yaml
# streamlit/config.toml
[server]
port = 8501
runOnSave = false
enableXsrfProtection = true

[client]
showErrorDetails = false
```

#### 2. Docker Container
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app_lapisai.py"]
```

#### 3. Enterprise (Streamlit Teams)
- Multi-user support
- SSO integration
- Audit logging
- Advanced security

---

## 📊 Performance Metrics

### Load Times
- Streamlit startup: ~3-5 seconds
- Model loading: ~1 second (cached)
- NLP assets loading: ~500ms (cached)
- Prediction inference: ~10ms per customer

### Memory Usage
- Base application: ~200-300 MB
- Loaded models: ~50-100 MB
- Session state: ~10-20 MB per user

### Scalability
- Single-threaded Streamlit app
- Good for <100 concurrent users
- For >100 users, consider load balancing

---

## 🔧 Extension Points

### 1. Add New Models
```python
# In load_assets()
# Add more models to the comparison
new_model = joblib.load("path/to/model.pkl")
```

### 2. Add NLP Visualizations
```python
# In render_nlp_section()
# Add new chart types
fig_custom = px.scatter(data, ...)
st.plotly_chart(fig_custom)
```

### 3. Add Custom Metrics
```python
# In render_model_metrics_and_calibration()
# Add new evaluation plots
plot_custom_metric(scored, threshold)
```

### 4. Connect to External Data
```python
# In load_source_data()
# Query from database instead of CSV
df = query_database("SELECT * FROM customers")
```

---

## 🎯 Future Enhancements

- [ ] Real-time streaming updates
- [ ] Multi-language NLP support
- [ ] Custom lexicon builder UI
- [ ] Model retraining pipeline
- [ ] A/B testing framework
- [ ] Advanced SHAP visualizations
- [ ] Export to PowerBI/Tableau
- [ ] REST API for model inference
- [ ] Mobile app version
- [ ] CI/CD integration

---

## 📋 Checklist for Deployment

- [ ] Update credentials (AUTH_USERNAME, AUTH_PASSWORD)
- [ ] Review NLTK data downloads
- [ ] Test all dashboard pages
- [ ] Verify NLP artifacts generated
- [ ] Check performance under load
- [ ] Set up logging/monitoring
- [ ] Create deployment documentation
- [ ] Run security audit
- [ ] Set up backup strategy
- [ ] Define SLAs

---

## 🔗 Dependencies Graph

```
Streamlit (UI Framework)
├── Pandas (Data manipulation)
├── NumPy (Numerical computing)
├── Plotly (Visualizations)
├── Scikit-learn (ML pipelines)
│   ├── TF-IDF Vectorizer
│   ├── Naive Bayes
│   └── Metrics
├── XGBoost (Gradient boosting)
├── CatBoost (Categorical boosting)
├── SHAP (Model explanations)
├── Joblib (Model serialization)
├── NLTK (NLP preprocessing)
│   ├── Punkt (Tokenization)
│   └── Stopwords
├── JSON (Config/serialization)
└── Pathlib (File operations)
```

---

## 🎓 Architecture Principles

1. **Separation of Concerns** - NLP pipeline separate from dashboard
2. **Caching** - Expensive operations cached (models, data)
3. **Modularity** - Reusable components and functions
4. **Type Safety** - TypedDict for data structures
5. **Error Handling** - Graceful degradation on missing artifacts
6. **Security** - Authentication and session management
7. **Scalability** - Stateless design where possible
8. **Maintainability** - Clear naming and documentation

---

**Version:** 1.0  
**Last Updated:** 2026-05  
**Architecture Pattern:** MVC (Model-View-Controller) adapted for Streamlit
