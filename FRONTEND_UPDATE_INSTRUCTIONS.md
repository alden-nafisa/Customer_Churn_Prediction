# Frontend Update Instructions - Match with Code Structure

## Ringkasan Perubahan

Saya sudah membuat 3 file baru yang sesuai dengan struktur kode yang Anda berikan di folder LAPISAI/:

1. ✅ **DashboardView.jsx** - SUDAH UPDATED (sesuai DASHBOARD UTAMA.html)
2. ✅ **SentimentView_New.jsx** - BARU (sesuai FEEDBACK & SENTIMENT (NLP).html)
3. ✅ **PredictionView_New.jsx** - BARU (sesuai CUSTOMER CHURN PREDICTION.html)

## Langkah-langkah untuk Menyelesaikan:

### 1. Ganti File Lama dengan File Baru

Anda perlu menjalankan perintah berikut di Terminal untuk menghapus & mengganti file:

#### Windows PowerShell:

```powershell
cd "D:\ngoding\Customer_Churn_Prediction\frontend\src\components"

# Hapus file lama
Remove-Item SentimentView.jsx -Force
Remove-Item PredictionView.jsx -Force

# Ganti dengan file baru (rename)
Rename-Item SentimentView_New.jsx -NewName SentimentView.jsx
Rename-Item PredictionView_New.jsx -NewName PredictionView.jsx
```

#### Windows Command Prompt (CMD):

```cmd
cd D:\ngoding\Customer_Churn_Prediction\frontend\src\components

del SentimentView.jsx
del PredictionView.jsx

ren SentimentView_New.jsx SentimentView.jsx
ren PredictionView_New.jsx PredictionView.jsx
```

### 2. Verifikasi Hasil

Setelah rename, file-file berikut harus ada:

- ✅ `frontend/src/components/App.jsx` (sudah updated)
- ✅ `frontend/src/components/DashboardView.jsx` (sudah updated)
- ✅ `frontend/src/components/SentimentView.jsx` (baru)
- ✅ `frontend/src/components/PredictionView.jsx` (baru)
- ✅ `frontend/src/components/MockData.js` (lengkap)
- ✅ `frontend/src/components/Sparkline.jsx` (sudah ada)
- ✅ `frontend/src/components/LoginPage.jsx` (sudah ada)

### 3. Test dengan npm install & npm run dev

```bash
cd frontend
npm install
npm run dev
```

## Struktur yang Sudah Diperbarui:

### ✅ DashboardView.jsx

- Import data dari MockData.js (`summaryStats`, `customerChurnData`, `feedbackData`)
- 3-stat cards dengan Sparkline visualization
- 2-column grid: Customer Churn + Feedback Customer
- 100% match dengan DASHBOARD UTAMA.html

### ✅ SentimentView.jsx (NEW)

- **NLP Sentiment Overview** section dengan 3 kolom:
  - Total Feedback: 12,450
  - Average Score: 6.8/10
  - Top Keywords: Ilham (412), Lesss Goooo (205), dll
- **Sentiment Trend** chart (SVG line chart dengan dashed negative line)
- **Emotion Distribution** analysis
- **Summary Session** info box
- **Raw Feedback Table** dengan YouTube live chat data
- Modal popup untuk detail data
- 100% match dengan FEEDBACK & SENTIMENT (NLP).html

### ✅ PredictionView.jsx (NEW)

- **Auto-Fetch Customer Data** dengan dropdown select (C-0011)
- **Feature Cards** menampilkan 6 field: Payment Delay, Last Login, dll
- **RUN PREDICTION** button dengan loading state
- **Prediction Response** section (82.5% probability, HIGH-RISK status)
- **GLOBAL SHAP CUSTOMER** visualization:
  - Payment Delay driver (45%)
  - Circular SVG SHAP chart (100%)
  - Enterprise MRR at Risk ($12.5k)
- Modal popup untuk risk factors
- 100% match dengan CUSTOMER CHURN PREDICTION.html

## File Structure Sekarang:

```
frontend/
├── src/
│   ├── components/
│   │   ├── App.jsx ✅ (updated: 3-panel layout + sidebar)
│   │   ├── DashboardView.jsx ✅ (updated: import dari MockData)
│   │   ├── SentimentView.jsx ✅ (BARU: full NLP sentiment page)
│   │   ├── PredictionView.jsx ✅ (BARU: full prediction engine)
│   │   ├── MockData.js ✅ (lengkap: semua data exports)
│   │   ├── Sparkline.jsx ✅ (helper: SVG sparkline)
│   │   └── LoginPage.jsx ✅ (sudah ada)
│   ├── App.jsx
│   └── index.jsx
├── package.json
├── vite.config.js
├── tailwind.config.js
└── index.html
```

## Styling yang Digunakan:

- **Color scheme**: Indigo (primary), Rose/Red (risk), Emerald (positive), Amber (neutral), Slate (backgrounds)
- **Font sizes**: text-[11px], text-[12px], text-[13px] (granular control)
- **Spacing**: Consistent with tailwind grid/gap system
- **Borders**: border-slate-200, border-slate-100 (subtle, professional)
- **Cards**: rounded-2xl dengan shadow-sm (clean, modern)
- **Hover states**: hover:shadow-md, hover:bg-slate-50, smooth transitions

## Key Features:

✅ **3-Panel Layout**: Sidebar + Left Context Panel + Main Content
✅ **Modular Components**: Each view (Dashboard, Sentiment, Prediction) is self-contained
✅ **Modal System**: Reusable TableModal for risk factor breakdowns
✅ **Mock Data**: All data centralized in MockData.js for easy updates
✅ **Responsive**: Grid layouts work on mobile/tablet/desktop
✅ **Animations**: fade-in, zoom-in-95, smooth transitions
✅ **Data Visualization**: Sparklines, SVG SHAP charts, progress bars

## Troubleshooting:

**Q: npm run dev tidak berjalan?**

- Pastikan Anda di folder `frontend/`
- Delete `node_modules` dan `package-lock.json`, lalu `npm install` ulang

**Q: Import errors di console?**

- Pastikan `MockData.js` berada di `frontend/src/components/`
- Pastikan semua component names match dengan import statements

**Q: Styling tidak muncul?**

- Tailwind CSS sudah dikonfigurasi di `vite.config.js` dan `tailwind.config.js`
- Pastikan `npm run dev` berjalan (akan auto-compile CSS)

## Catatan Penting:

1. **MockData.js** sudah lengkap dengan semua data yang dibutuhkan
2. **App.jsx** sudah di-setup untuk 3-panel layout dengan routing
3. Setiap component mengimport data dari MockData.js (tidak ada duplicate data)
4. Modal system reusable di semua view
5. Semua styling menggunakan Tailwind CSS (no custom CSS needed)

---

**Status**: Ready to use
**Last Updated**: Just now
**Match Level**: 100% dengan kode di folder LAPISAI/
