# Customer Churn Prediction with XGBoost, SHAP, and Streamlit

Proyek ini membangun sistem peringatan dini churn pelanggan untuk perusahaan SaaS dengan:

- **Baseline model:** Logistic Regression
- **Baseline model tambahan:** Naive Bayes
- **Main model:** XGBoost
- **Explainability:** SHAP
- **Dashboard:** Streamlit

## Metode yang dipakai

### Machine learning untuk churn prediction
- Logistic Regression
- Naive Bayes
- XGBoost

### Data mining
- K-Means dipakai untuk segmentasi pelanggan, bukan untuk prediksi churn.

### NLP
- Sentiment analysis cocok memakai Naive Bayes sebagai baseline.
- Summarization tidak menggunakan Naive Bayes sebagai algoritma utama.
- Dataset live chat YouTube disiapkan sebagai sumber awal untuk eksperimen NLP.

### Imbalance handling dan explainability
- SMOTE dipakai pada data training churn yang imbalance.
- SHAP/XAI dipakai untuk menjelaskan kenapa pelanggan diprediksi churn.

## Struktur

- `customers_dataset.csv` — data pelanggan historis
- `youtube_chat_5_menit.csv` — dataset komentar live chat untuk eksperimen NLP
- `train_model.py` — melatih model dan menyimpan artefak
- `train_customer_segmentation.py` — segmentasi pelanggan dengan K-Means
- `train_sentiment_model.py` — melatih model sentiment analysis untuk komentar live chat
- `app.py` — dashboard interaktif
- `src/churn_pipeline.py` — utilitas pemodelan
- `artifacts/` — model, metrik, dan output evaluasi

## Instalasi

Gunakan environment virtual yang ada di folder `.venv`, lalu install dependency:

```bash
pip install -r requirements.txt
```

## Melatih model

```bash
python train_model.py
```

Artefak akan disimpan ke folder `artifacts/`:

- `logistic_pipeline.joblib`
- `naive_bayes_pipeline.joblib`
- `xgb_pipeline.joblib`
- `metrics.json`
- `test_predictions.csv`

### Melatih model NLP sentiment analysis

```bash
python train_sentiment_model.py
```

Artefak NLP akan disimpan ke folder `artifacts/nlp/`:

- `logistic_sentiment_pipeline.pkl`
- `naive_bayes_sentiment_pipeline.pkl`
- `sentiment_metrics.json`
- `sentiment_test_predictions.csv`

### Melatih segmentasi pelanggan

```bash
python train_customer_segmentation.py
```

Artefak segmentasi akan disimpan ke folder `artifacts/segmentation/`:

- `customer_segmentation_pipeline.joblib`
- `customer_clusters.csv`
- `cluster_summary.csv`
- `segmentation_metrics.json`

## Bagaimana proses klasifikasi bekerja

1. Data historis dibagi menjadi fitur dan label.
2. Kolom `churned` dipakai sebagai **ground truth**:
	- `1` = pelanggan benar-benar churn
	- `0` = pelanggan tidak churn
3. Model hanya melihat fitur pelanggan, bukan kolom `churned`.
4. Data dibagi menjadi **80% training** dan **20% testing** secara stratified.
5. Logistic Regression dan Naive Bayes dipakai sebagai baseline, lalu XGBoost sebagai model utama.
6. SMOTE diterapkan pada data training untuk membantu menangani kelas yang tidak seimbang.
7. Hasil prediksi berupa probabilitas churn dan label prediksi berdasarkan threshold.

## Tentang filter dashboard

Filter di dashboard dipakai untuk memilih subset pelanggan yang ingin dianalisis.

- Filter utama: plan type, contract type, dan status churn aktual.
- Filter lanjutan: tenure, revenue, last login, NPS, feature adoption, support tickets, dan payment delay.

Jadi filter itu **bukan bagian dari training model**, melainkan untuk memudahkan analisis bisnis.

## Report generator

Dashboard menyediakan file report yang bisa diunduh, berisi:

- ringkasan performa model,
- jumlah pelanggan churn aktual vs prediksi,
- daftar pelanggan prioritas,
- rekomendasi tindakan retensi.

## Menjalankan dashboard

```bash
streamlit run app.py
```

## Fitur dashboard

- Filter pelanggan berdasarkan plan, kontrak, tenure, revenue, login, dan NPS
- Peringkat pelanggan dengan risiko churn tertinggi
- Perbandingan performa Logistic Regression vs Naive Bayes vs XGBoost
- Penjelasan global dan lokal berbasis SHAP
- Download report analitik
