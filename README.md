# Customer Churn Prediction with XGBoost, SHAP, and Streamlit

Proyek ini membangun sistem peringatan dini churn pelanggan untuk perusahaan SaaS dengan arsitektur yang sekarang difokuskan ke Supabase dan dataset `churn_analysis_datasets` sebagai sumber utama.

- **Main model:** XGBoost
- **Comparator model:** CatBoost
- **Explainability:** SHAP
- **Dashboard:** Streamlit
- **Primary cloud database:** Supabase
- **Backend API:** FastAPI
- **Frontend terpisah:** Next.js

## Metode yang dipakai

### Machine learning untuk churn prediction
- XGBoost
- CatBoost

### Data preparation
- Prapemrosesan data dilakukan melalui imputasi, encoding kategorikal, scaling fitur numerik, dan SMOTE pada data training churn yang imbalance.
- Schema model mengikuti fitur kanonik hasil agregasi dari `churn_analysis_datasets`.

### NLP
- Sentiment analysis memakai komentar sebagai input dan label sentimen dibentuk otomatis dari teks.
- Session summary dibuat sebagai ringkasan extractive berbasis komentar.
- Dataset live chat YouTube yang sudah dirapikan dipakai untuk eksperimen NLP.

### Imbalance handling dan explainability
- SMOTE dipakai pada data training churn yang imbalance.
- SHAP/XAI dipakai untuk menjelaskan kenapa pelanggan diprediksi churn.

## Struktur

- `churn_analysis_datasets/` — sumber utama data churn SaaS untuk training/testing dan simulasi prediksi
- `youtube_chat_5_menit_cleaned.csv` — dataset komentar live chat yang sudah dirapikan untuk eksperimen NLP
- `train_model.py` — melatih XGBoost dan CatBoost serta menyimpan artefak
- `train_sentiment_model.py` — melatih model sentiment analysis untuk komentar live chat
- `app.py` — dashboard interaktif
- `backend/` — FastAPI service untuk prediction API dan metadata plan
- `frontend/` — aplikasi Next.js yang memanggil API FastAPI
- `src/churn_pipeline.py` — utilitas pemodelan
- `src/supabase_config.py` — loader konfigurasi Supabase dari environment
- `.env.example` — template variabel environment Supabase
- `artifacts/` — model, metrik, dan output evaluasi

## Arsitektur data baru

Sistem sekarang memakai satu schema fitur kanonik yang dibentuk dari `churn_analysis_datasets` agar training, testing, dan input prediksi tetap konsisten:

| Fitur kanonik | Sumber di churn_analysis_datasets | Alasan dipilih |
|---|---|---|
| `plan_type` | `customer_accounts.plan_type` | Segmentasi paket sangat kuat memengaruhi churn. |
| `contract_type` | `customer_accounts.contract_type` | Kontrak bulanan vs tahunan berkaitan langsung dengan retensi. |
| `tenure_months` | turunan dari `subscription_date` dan `unsubscribed_date` | Lama berlangganan adalah indikator loyalitas. |
| `total_users` | `customer_accounts.total_users` | Ukuran akun memengaruhi switching cost. |
| `monthly_usage_hrs` | `monthly_usage_metrics.monthly_usage_hrs` | Menangkap intensitas penggunaan. |
| `feature_adoption_pct` | `monthly_usage_metrics.feature_adoption_pct` | Mengukur kedalaman adopsi produk. |
| `last_login_days_ago` | turunan dari `monthly_usage_metrics.last_login_date` | Aktivitas terakhir adalah sinyal churn yang kuat. |
| `support_tickets_last_90d` | agregasi `support_tickets` 90 hari | Friksi support sering mendahului churn. |

Fitur tambahan yang boleh dipakai bila tersedia:

| Fitur tambahan | Sumber di churn_analysis_datasets | Catatan |
|---|---|---|
| `nps_score` | `nps_surveys.nps_score` | Mirip konsepnya, tetapi tidak identik. |
| `payment_delay_count` | agregasi `billing_data.record_type = dunning` | Tidak wajib, tapi berguna untuk menangkap friksi pembayaran. |

## Flow sistem yang disarankan

1. `churn_analysis_datasets` masuk ke Supabase sebagai raw tables.
2. Dari raw tables dibuat feature view / feature table kanonik.
3. Model training dan testing memakai feature table kanonik itu.
4. Aplikasi menampilkan form input berdasarkan fitur kanonik, bukan berdasarkan tabel mentah.
5. Nilai tidak harus sama dengan data mentah, yang harus sama adalah makna fiturnya.

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
- Filter lanjutan: tenure, total users, monthly usage, feature adoption, last login, dan support tickets.
- Fitur tambahan seperti NPS dan payment delay dapat dipakai bila memang disiapkan di feature view.

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

## Menjalankan backend FastAPI

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoint utama:

- `GET /health`
- `GET /api/plans`
- `POST /api/predict`

## Menjalankan frontend Next.js

Masuk ke folder `frontend/`, lalu install dependency dan jalankan dev server:

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` ke URL backend FastAPI, misalnya `http://127.0.0.1:8000` untuk lokal.

## Deployment

### Backend di Render

- Gunakan [render.yaml](render.yaml) sebagai blueprint service.
- Set `FRONTEND_ORIGINS` ke origin frontend Vercel Anda, misalnya `https://your-app.vercel.app`.

### Frontend di Vercel

- Deploy folder `frontend/` sebagai project Next.js.
- Set environment variable `NEXT_PUBLIC_API_BASE_URL` ke URL backend Render, misalnya `https://customer-churn-api.onrender.com`.

### Catatan integrasi

- Frontend hanya memanggil `GET /api/plans` dan `POST /api/predict`.
- Backend tetap memakai artefak model yang sudah ada di `artifacts/plan_models/`.

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

## Catatan implementasi Supabase

- Data utama sekarang diarahkan ke Supabase, bukan ke database lokal.
- Tabel dan view yang diekspos ke client sebaiknya diberi RLS.
- Schema fitur untuk training/testing harus tetap sama dari raw tables ke feature view.
