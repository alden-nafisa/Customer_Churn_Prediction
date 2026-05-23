import React, { useState } from 'react'
import LoginPage from './components/LoginPage'
import DashboardView from './components/DashboardView'
import PredictionView from './components/PredictionViewIntegrated'
import SentimentView from './components/SentimentView'
import { BarChart3, LayoutDashboard, MessageSquare, HelpCircle, Target } from 'lucide-react'
import {
  dashboardHighRiskAlerts,
  predictionLogs,
  predictionHighRiskAlerts,
  sentimentLogs,
  sentimentHighRiskAlerts,
} from './components/MockData.jsx'

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [activeTab, setActiveTab] = useState('prediction')
  const [isHelpOpen, setIsHelpOpen] = useState(false)

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => {
      setIsAuthenticated(true)
      setActiveTab('dashboard')
    }} />
  }

  const renderSidebarContent = () => {
    if (activeTab === 'sentiment') {
      return (
        <>
          <div className="mb-10">
            <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-wider mb-4 text-center">Log System & ML</h3>
            <div className="space-y-3">
              {sentimentLogs.map((log, i) => (
                <div key={i} className="bg-slate-50 rounded-xl p-3 flex gap-3 border border-slate-100 hover:border-slate-200 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center flex-shrink-0 border border-slate-100">{log.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-0.5"><h4 className="text-[11px] font-bold text-slate-800">{log.title}</h4><span className="text-[9px] font-semibold text-slate-400 whitespace-nowrap ml-2">{log.time}</span></div>
                    <p className="text-[10px] text-slate-500 leading-snug">{log.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-wider">HIGH-RISK ALERT</h3>
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            </div>
            <div className="space-y-3">
              {sentimentHighRiskAlerts.map((alert, idx) => {
                let colors = { border: 'bg-rose-500', text: 'text-rose-500', badgeBg: 'bg-rose-500', badgeText: 'HIGH RISK' }
                if (alert.riskLevel === 'warning') colors = { border: 'bg-amber-500', text: 'text-amber-500', badgeBg: 'bg-amber-500', badgeText: 'WARNING' }

                return (
                  <div key={idx} className="bg-white rounded-xl p-3 border border-slate-100 shadow-sm relative overflow-hidden group">
                    <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${colors.border}`}></div>
                    <div className="flex justify-between items-center mb-1 pl-2">
                      <span className={`text-[9px] font-bold ${colors.text} tracking-wider uppercase`}>{alert.time}</span>
                      <span className={`text-[8px] font-black text-white ${colors.badgeBg} px-1.5 py-0.5 rounded shadow-sm`}>{colors.badgeText}</span>
                    </div>
                    <div className="pl-2"><h4 className="text-[11px] font-bold text-slate-800">{alert.id}</h4><p className="text-[10px] text-slate-500 mt-1 leading-snug">{alert.desc}</p></div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )
    }

    if (activeTab === 'prediction') {
      return (
        <>
          <div className="mb-10">
            <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-wider mb-4 text-center">Log System & ML</h3>
            <div className="space-y-3">
              {predictionLogs.map((log, i) => (
                <div key={i} className="bg-slate-50 rounded-xl p-3 flex gap-3 border border-slate-100 hover:border-slate-200 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center flex-shrink-0 border border-slate-100">{log.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-0.5"><h4 className="text-[11px] font-bold text-slate-800">{log.title}</h4><span className="text-[9px] font-semibold text-slate-400 whitespace-nowrap ml-2">{log.time}</span></div>
                    <p className="text-[10px] text-slate-500 leading-snug">{log.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-wider">HIGH-RISK ALERT</h3>
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            </div>
            <div className="space-y-3">
              {predictionHighRiskAlerts.map((alert, idx) => {
                let colors = { border: 'bg-rose-500', text: 'text-rose-500', badgeBg: 'bg-rose-500', badgeText: 'HIGH RISK' }
                if (alert.riskLevel === 'warning') colors = { border: 'bg-amber-500', text: 'text-amber-500', badgeBg: 'bg-amber-500', badgeText: 'WARNING' }
                if (alert.riskLevel === 'safe') colors = { border: 'bg-emerald-500', text: 'text-emerald-500', badgeBg: 'bg-emerald-500', badgeText: 'SAFE' }

                return (
                  <div key={idx} className="bg-white rounded-xl p-3 border border-slate-100 shadow-sm relative overflow-hidden group">
                    <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${colors.border}`}></div>
                    <div className="flex justify-between items-center mb-1 pl-2">
                      <span className={`text-[9px] font-bold ${colors.text} tracking-wider uppercase`}>{alert.time}</span>
                      <span className={`text-[8px] font-black text-white ${colors.badgeBg} px-1.5 py-0.5 rounded shadow-sm`}>{colors.badgeText}</span>
                    </div>
                    <div className="pl-2">
                      <h4 className="text-[11px] font-bold text-slate-800">{alert.id} <span className="text-[9px] font-semibold text-slate-400">({alert.type})</span></h4>
                      <p className="text-[10px] text-slate-500 mt-1 leading-snug">{alert.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )
    }

    return (
      <>
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-wider">HIGH-RISK ALERT</h3>
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
          </div>
          <div className="space-y-3">
            {dashboardHighRiskAlerts.map((alert, idx) => {
              let colors = { border: 'bg-rose-500', text: 'text-rose-500', badgeBg: 'bg-rose-500', badgeText: 'HIGH RISK' }
              if (alert.riskLevel === 'warning') colors = { border: 'bg-amber-500', text: 'text-amber-500', badgeBg: 'bg-amber-500', badgeText: 'WARNING' }
              if (alert.riskLevel === 'safe') colors = { border: 'bg-emerald-500', text: 'text-emerald-500', badgeBg: 'bg-emerald-500', badgeText: 'SAFE' }

              return (
                <div key={idx} className="bg-white rounded-xl p-3 border border-slate-100 shadow-sm relative overflow-hidden group">
                  <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${colors.border}`}></div>
                  <div className="flex justify-between items-center mb-1 pl-2">
                    <span className={`text-[9px] font-bold ${colors.text} tracking-wider uppercase`}>{alert.time}</span>
                    <span className={`text-[8px] font-black text-white ${colors.badgeBg} px-1.5 py-0.5 rounded shadow-sm`}>{colors.badgeText}</span>
                  </div>
                  <div className="pl-2">
                    <h4 className="text-[11px] font-bold text-slate-800">{alert.id} <span className="text-[9px] font-semibold text-slate-400">({alert.type})</span></h4>
                    <p className="text-[10px] text-slate-500 mt-1 leading-snug">{alert.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </>
    )
  }

  return (
    <div className="flex h-screen bg-[#F8FAFC] font-sans overflow-hidden">
      <aside className="w-16 bg-white border-r border-slate-200 h-screen flex flex-col items-center py-5 z-20 flex-shrink-0">
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-md shadow-indigo-200 mb-8 cursor-pointer">
          <LayoutDashboard size={20} className="text-white" />
        </div>
        <nav className="flex flex-col gap-4 w-full px-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`w-full aspect-square rounded-xl flex items-center justify-center transition-all ${activeTab === 'dashboard' ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-indigo-500'}`}
            title="Dashboard"
          >
            <BarChart3 size={20} strokeWidth={activeTab === 'dashboard' ? 2.5 : 2} />
          </button>
          <button
            onClick={() => setActiveTab('prediction')}
            className={`w-full aspect-square rounded-xl flex items-center justify-center transition-all ${activeTab === 'prediction' ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-indigo-500'}`}
            title="Prediction Engine"
          >
            <Target size={20} strokeWidth={activeTab === 'prediction' ? 2.5 : 2} />
          </button>
          <button
            onClick={() => setActiveTab('sentiment')}
            className={`w-full aspect-square rounded-xl flex items-center justify-center transition-all ${activeTab === 'sentiment' ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-indigo-500'}`}
            title="Feedback & Sentiment"
          >
            <MessageSquare size={20} strokeWidth={activeTab === 'sentiment' ? 2.5 : 2} />
          </button>
        </nav>

        <div className="mt-auto flex flex-col gap-4 w-full px-2 items-center">
          <button
            onClick={() => setIsHelpOpen(true)}
            className="w-full aspect-square rounded-xl flex items-center justify-center text-slate-400 hover:bg-slate-50 hover:text-slate-600 transition-all"
            title="Help & Guide"
          >
            <HelpCircle size={20} />
          </button>
          <div className="w-10 h-10 rounded-full border-2 border-indigo-100 overflow-hidden cursor-pointer mt-2 hover:border-indigo-400 transition-colors" onClick={() => setIsAuthenticated(false)} title="Log Out">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Admin" alt="User" className="w-full h-full object-cover bg-indigo-50" />
          </div>
        </div>
      </aside>

      <aside className="w-[300px] bg-white border-r border-slate-200 h-screen overflow-y-auto flex flex-col z-10 flex-shrink-0 hidden md:flex">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-8">
            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Lapis<span className="text-indigo-600">AI</span></h1>
          </div>

          <div className="mb-10">
            <p className="text-[13px] text-slate-400 font-medium">Welcome,</p>
            <h2 className="text-2xl font-black text-slate-800 tracking-tight">Admin</h2>
          </div>
          {renderSidebarContent()}
        </div>
      </aside>

      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <div className="flex-1 overflow-y-auto px-8 pt-8">
          {activeTab === 'dashboard' && <DashboardView setActiveTab={setActiveTab} />}
          {activeTab === 'prediction' && <PredictionView />}
          {activeTab === 'sentiment' && <SentimentView />}
        </div>
      </main>

      {isHelpOpen ? (
        <div className="fixed inset-0 z-50 flex">
          <button
            type="button"
            aria-label="Close help panel"
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
            onClick={() => setIsHelpOpen(false)}
          />
          <aside className="relative ml-auto h-full w-full max-w-[480px] bg-white shadow-2xl border-l border-slate-200 overflow-y-auto">
            <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-white/95 backdrop-blur">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.2em] text-indigo-600">Help & Guide</p>
                <h2 className="text-xl font-black text-slate-900">Panduan Penggunaan</h2>
              </div>
              <button
                onClick={() => setIsHelpOpen(false)}
                className="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                title="Close"
              >
                ×
              </button>
            </div>

            <div className="px-6 py-5 space-y-5 text-slate-700">
              <section className="bg-slate-50 border border-slate-100 rounded-2xl p-4">
                <h3 className="font-black text-slate-900 mb-2">1) Apa yang dilakukan sistem ini?</h3>
                <p className="text-sm leading-6">
                  Sistem ini membantu memprediksi apakah seorang pelanggan berisiko churn, yaitu berhenti menggunakan layanan.
                  Pengguna cukup melihat ringkasan data, hasil prediksi, dan rekomendasi tindakan tanpa perlu memahami detail teknis model.
                </p>
                <ul className="mt-3 list-disc pl-5 text-sm leading-6 space-y-1">
                  <li>Data pelanggan dimasukkan atau dipilih dari daftar yang tersedia.</li>
                  <li>Fitur penting dipakai untuk menghitung peluang churn.</li>
                  <li>Hasilnya ditampilkan sebagai probabilitas, label risiko, dan saran tindakan.</li>
                </ul>
              </section>

              <section className="bg-slate-50 border border-slate-100 rounded-2xl p-4">
                <h3 className="font-black text-slate-900 mb-2">2) Kenapa feature yang banyak disederhanakan?</h3>
                <p className="text-sm leading-6">
                  Dalam data pelanggan, jumlah fitur bisa sangat banyak. Namun, tidak semua fitur perlu dipakai langsung untuk menjelaskan hasil ke pengguna non-teknis.
                  Karena itu, sistem biasanya memilih fitur yang paling relevan, paling stabil, dan paling mudah dipahami.
                </p>
                <ul className="mt-3 list-disc pl-5 text-sm leading-6 space-y-1">
                  <li><strong>Relevan</strong>: fitur yang paling berhubungan dengan churn.</li>
                  <li><strong>Stabil</strong>: pola fitur tidak mudah berubah-ubah tanpa alasan.</li>
                  <li><strong>Mudah dijelaskan</strong>: fitur yang bisa diterjemahkan ke tindakan bisnis.</li>
                </ul>
                <p className="mt-3 text-sm leading-6">
                  Contoh sederhana: jumlah tiket keluhan, keterlambatan pembayaran, penggunaan fitur yang menurun, atau skor kepuasan yang rendah.
                  Fitur seperti ini lebih mudah dipakai untuk menjelaskan risiko dan menentukan tindakan retensi.
                </p>
              </section>

              <section className="bg-slate-50 border border-slate-100 rounded-2xl p-4">
                <h3 className="font-black text-slate-900 mb-2">3) Bagaimana algoritma memprediksi?</h3>
                <p className="text-sm leading-6">
                  Secara sederhana, model belajar dari data pelanggan lama. Ia mencari pola seperti: pelanggan dengan perilaku tertentu lebih sering churn atau tetap bertahan.
                  Saat data baru masuk, model membandingkan pola baru itu dengan pola yang sudah dipelajari, lalu menghasilkan probabilitas churn.
                </p>
                <div className="mt-3 space-y-2 text-sm leading-6">
                  <p><strong>Langkah 1:</strong> Model membaca fitur pelanggan.</p>
                  <p><strong>Langkah 2:</strong> Model memberi bobot pada fitur yang paling berpengaruh.</p>
                  <p><strong>Langkah 3:</strong> Model menghitung skor atau probabilitas churn.</p>
                  <p><strong>Langkah 4:</strong> Probabilitas itu diubah menjadi label risiko seperti Low, Medium, High, atau Very High.</p>
                </div>
                <p className="mt-3 text-sm leading-6">
                  Jadi, model tidak sekadar mengatakan "ya" atau "tidak", tetapi memberi tingkat keyakinan. Itulah sebabnya threshold penting: threshold menentukan kapan sebuah probabilitas dianggap cukup tinggi untuk diperlakukan sebagai risiko.
                </p>
              </section>

              <section className="bg-slate-50 border border-slate-100 rounded-2xl p-4">
                <h3 className="font-black text-slate-900 mb-2">4) Cara membaca hasil prediksi</h3>
                <p className="text-sm leading-6">
                  Untuk pengguna non-teknis, fokus utama bukan angka teknisnya, tetapi arti bisnisnya.
                </p>
                <ul className="mt-3 list-disc pl-5 text-sm leading-6 space-y-1">
                  <li><strong>Probabilitas tinggi</strong> berarti pelanggan lebih mungkin churn.</li>
                  <li><strong>Risk label</strong> membantu melihat prioritas tindakan.</li>
                  <li><strong>Recommendation</strong> menunjukkan langkah yang bisa dilakukan tim retention.</li>
                  <li><strong>Model comparison</strong> membantu memilih model yang paling cocok untuk kebutuhan bisnis.</li>
                </ul>
                <p className="mt-3 text-sm leading-6">
                  Jika probabilitas tinggi muncul pada pelanggan bernilai besar, itu biasanya menjadi prioritas utama karena potensi kerugian bisnis lebih besar.
                </p>
              </section>

              <section className="bg-slate-50 border border-slate-100 rounded-2xl p-4">
                <h3 className="font-black text-slate-900 mb-2">5) Apa yang perlu diperhatikan dari metrik model?</h3>
                <p className="text-sm leading-6">
                  Metrik membantu menilai kualitas model, bukan hanya seberapa sering model benar, tetapi juga jenis kesalahan yang dibuat.
                </p>
                <ul className="mt-3 list-disc pl-5 text-sm leading-6 space-y-1">
                  <li><strong>Accuracy</strong>: gambaran umum jumlah prediksi yang benar.</li>
                  <li><strong>Precision</strong>: seberapa sering prediksi churn benar-benar churn.</li>
                  <li><strong>Recall</strong>: seberapa banyak churn yang berhasil tertangkap model.</li>
                  <li><strong>F1-score</strong>: keseimbangan antara precision dan recall.</li>
                  <li><strong>Confusion matrix</strong>: ringkasan jenis prediksi benar dan salah.</li>
                </ul>
                <p className="mt-3 text-sm leading-6">
                  Untuk tim bisnis, recall penting jika tidak ingin melewatkan pelanggan yang benar-benar akan churn. Precision penting jika biaya follow-up pelanggan terlalu mahal.
                </p>
              </section>

              <section className="bg-slate-50 border border-slate-100 rounded-2xl p-4">
                <h3 className="font-black text-slate-900 mb-2">6) Keterbatasan yang harus dipahami</h3>
                <ul className="list-disc pl-5 text-sm leading-6 space-y-1">
                  <li>Prediksi model adalah estimasi, bukan kepastian.</li>
                  <li>Perubahan perilaku pelanggan atau produk bisa membuat pola lama kurang relevan.</li>
                  <li>Data yang tidak lengkap atau salah input dapat memengaruhi hasil.</li>
                  <li>Keputusan akhir tetap perlu dipadukan dengan konteks bisnis dan review manusia.</li>
                </ul>
              </section>

              <section className="bg-indigo-50 border border-indigo-100 rounded-2xl p-4">
                <h3 className="font-black text-slate-900 mb-2">7) Cara paling sederhana menggunakan panel ini</h3>
                <ol className="list-decimal pl-5 text-sm leading-6 space-y-1">
                  <li>Baca ringkasan dan pilih pelanggan atau segmen yang ingin dilihat.</li>
                  <li>Lihat risiko churn dan alasan utamanya.</li>
                  <li>Perhatikan metrik untuk memahami seberapa dapat dipercaya hasil model.</li>
                  <li>Gunakan rekomendasi untuk menentukan tindakan retensi.</li>
                </ol>
              </section>
            </div>
          </aside>
        </div>
      ) : null}
    </div>
  )
}
