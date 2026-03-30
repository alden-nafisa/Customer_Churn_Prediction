# Customer Churn Prediction with XGBoost, SHAP, and Streamlit

Proyek ini membangun sistem peringatan dini churn pelanggan untuk perusahaan SaaS dengan:

- **Baseline model:** Logistic Regression
- **Baseline model tambahan:** Naive Bayes
- **Main model:** XGBoost
- **Explainability:** SHAP
- **Dashboard:** Streamlit

## Struktur

- `customers_dataset.csv` — data pelanggan historis
- `train_model.py` — melatih model dan menyimpan artefak
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

## Bagaimana proses klasifikasi bekerja

1. Data historis dibagi menjadi fitur dan label.
2. Kolom `churned` dipakai sebagai **ground truth**:
	- `1` = pelanggan benar-benar churn
	- `0` = pelanggan tidak churn
3. Model hanya melihat fitur pelanggan, bukan kolom `churned`.
4. Data dibagi menjadi **80% training** dan **20% testing** secara stratified.
5. Logistic Regression dan Naive Bayes dipakai sebagai baseline, lalu XGBoost sebagai model utama.
6. Hasil prediksi berupa probabilitas churn dan label prediksi berdasarkan threshold.

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
