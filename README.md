# Customer Churn Prediction with XGBoost, SHAP, and Streamlit

Proyek ini membangun sistem peringatan dini churn pelanggan untuk perusahaan SaaS dengan:

- **Main model:** XGBoost
- **Comparator model:** CatBoost
- **Explainability:** SHAP
- **Dashboard:** Streamlit

## Metode yang dipakai

### Machine learning untuk churn prediction
- XGBoost
- CatBoost

### Data preparation
- Prapemrosesan data dilakukan melalui imputasi, encoding kategorikal, scaling fitur numerik, dan SMOTE pada data training churn yang imbalance.

### NLP
- Sentiment analysis memakai komentar sebagai input dan label sentimen dibentuk otomatis dari teks.
- Session summary dibuat sebagai ringkasan extractive berbasis komentar.
- Dataset live chat YouTube yang sudah dirapikan dipakai untuk eksperimen NLP.

### Imbalance handling dan explainability
- SMOTE dipakai pada data training churn yang imbalance.
- SHAP/XAI dipakai untuk menjelaskan kenapa pelanggan diprediksi churn.

## Struktur

- `customers_dataset_tidied.xlsx` — data pelanggan historis yang lebih rapi
- `youtube_chat_5_menit_cleaned.csv` — dataset komentar live chat yang sudah dirapikan untuk eksperimen NLP
- `train_model.py` — melatih XGBoost dan CatBoost serta menyimpan artefak
- `train_sentiment_model.py` — melatih model sentiment analysis untuk komentar live chat
- `app.py` — dashboard interaktif
- `src/churn_pipeline.py` — utilitas pemodelan
- `src/supabase_config.py` — loader konfigurasi Supabase dari environment
- `.env.example` — template variabel environment Supabase
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

- `xgb_pipeline.joblib`
- `catboost_pipeline.joblib`
- `metrics.json`
- `test_predictions.csv`

### Melatih model NLP sentiment analysis

```bash
python train_sentiment_model.py
```

Artefak NLP akan disimpan ke folder `artifacts/nlp/`:

- `naive_bayes_sentiment_pipeline.pkl`
- `sentiment_metrics.json`
- `sentiment_test_predictions.csv`

Script ini memakai teks komentar saja dan tidak menjadikan kolom sentiment sebagai input sistem.

### Membuat session summary

```bash
python train_session_summary.py
```

Ringkasan komentar akan disimpan ke `artifacts/nlp/`:

- `session_summary.json`
- `session_summary.txt`

## Bagaimana proses klasifikasi bekerja

1. Data historis dibagi menjadi fitur dan label.
2. Kolom `churned` dipakai sebagai **ground truth**:
	- `1` = pelanggan benar-benar churn
	- `0` = pelanggan tidak churn
3. Model hanya melihat fitur pelanggan, bukan kolom `churned`.
4. Data dibagi menjadi **80% training** dan **20% testing** secara stratified.
5. SMOTE diterapkan pada data training untuk membantu menangani kelas yang tidak seimbang.
6. XGBoost dan CatBoost dilatih pada data training untuk menghasilkan probabilitas churn.
7. Hasil prediksi berupa probabilitas churn dan label prediksi berdasarkan threshold.

## Tentang filter dashboard

Filter di dashboard dipakai untuk memilih subset pelanggan yang ingin dianalisis.

- Filter utama: plan type, contract type, dan status churn aktual.
- Filter lanjutan: tenure, revenue, last login, NPS, feature adoption, support tickets, dan payment delay.

Jadi filter itu **bukan bagian dari training model**, melainkan untuk memudahkan analisis bisnis.

## Penjelasan risiko

Dashboard menyediakan penjelasan ringkas yang bisa diunduh sebagai CSV, berisi:

- skor risiko tiap pelanggan,
- faktor pendorong utama,
- rekomendasi tindakan retensi.

## Menjalankan dashboard

```bash
streamlit run app.py
```

## Struktur halaman dashboard

- `Predict` untuk user umum yang ingin memasukkan data customer secara cepat dan langsung melihat risiko churn.
- `Advanced Analysis` untuk user analitis yang ingin memakai filter sidebar, membandingkan model, dan membaca SHAP per customer.

## Fitur dashboard

- Filter pelanggan berdasarkan plan, kontrak, tenure, revenue, login, dan NPS
- Peringkat pelanggan dengan risiko churn tertinggi
- Perbandingan performa XGBoost vs CatBoost
- Ringkasan SHAP global dan alasan per pelanggan
- Penjelasan global dan lokal berbasis SHAP
- Download explanation CSV
