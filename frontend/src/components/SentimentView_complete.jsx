import React, { useState } from 'react'
import { MessageSquare, Sparkles, Quote, Database, TrendingUp, BrainCircuit, MessageCircle, Info } from 'lucide-react'
import { sentimentKeywords, youtubeChatData } from './MockData.jsx'

export default function SentimentView() {
  const [manualText, setManualText] = useState('')
  const [manualSentiment, setManualSentiment] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const analyzeManualSentiment = () => {
    setIsAnalyzing(true)
    setTimeout(() => {
      const text = manualText.toLowerCase()
      if (text.includes('bagus') || text.includes('suka') || text.includes('puas')) setManualSentiment('Positif')
      else if (text.includes('buruk') || text.includes('kecewa') || text.includes('lambat')) setManualSentiment('Negatif')
      else setManualSentiment('Netral')
      setIsAnalyzing(false)
    }, 1000)
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20 relative">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-1.5 bg-white border border-slate-200 text-slate-500 rounded-md shadow-sm"><MessageSquare size={18} /></div>
        <h1 className="text-xl font-black text-slate-800 tracking-tight">Feedback & Sentiment Intelligence</h1>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4 pb-4 border-b border-slate-100"><Sparkles size={18} className="text-indigo-500" /><h2 className="text-[14px] font-black text-slate-800 tracking-wider uppercase">AI Executive Summary</h2></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <p className="text-sm text-slate-600 leading-relaxed font-medium">Berdasarkan pemrosesan <strong>12.450</strong> komentar masuk, audiens menunjukkan tingkat interaksi yang sangat tinggi. Mayoritas obrolan bersifat <span className="text-slate-800 font-bold bg-slate-100 px-1 rounded">Netral (65%)</span> yang didominasi oleh kata sapaan atau percakapan ringan. Namun, terdapat lonjakan sentimen <span className="text-rose-600 font-bold bg-rose-50 px-1 rounded">Negatif (20%)</span> dan emosi <strong>Marah</strong> yang signifikan terkait <em>"Volume Opening Video"</em> dan keluhan terhadap <em>"Ilham"</em>. Sangat disarankan untuk mengevaluasi elemen audio pada streaming berikutnya untuk mencegah ketidaknyamanan audiens (Friction Point).</p>
          </div>
          <div className="space-y-3">
            <h3 className="text-[11px] font-bold text-slate-400 uppercase mb-2">Raw Voice Quotes</h3>
            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3 flex gap-3 relative overflow-hidden"><div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-400"></div><Quote size={14} className="text-emerald-400 shrink-0 mt-0.5" /><div><p className="text-[12px] font-medium text-slate-700">"lesss goooo akhirnya live juga, semangat bang!"</p><span className="text-[9px] font-bold text-emerald-600 mt-1 block">Positive • @hostfytalhcpunk</span></div></div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex gap-3 relative overflow-hidden"><div className="absolute left-0 top-0 bottom-0 w-1 bg-slate-400"></div><Quote size={14} className="text-slate-400 shrink-0 mt-0.5" /><div><p className="text-[12px] font-medium text-slate-700">"gcc makanan gw hampir habis"</p><span className="text-[9px] font-bold text-slate-500 mt-1 block">Netral • @ranzehandsome</span></div></div>
            <div className="bg-rose-50 border border-rose-100 rounded-xl p-3 flex gap-3 relative overflow-hidden"><div className="absolute left-0 top-0 bottom-0 w-1 bg-rose-400"></div><Quote size={14} className="text-rose-400 shrink-0 mt-0.5" /><div><p className="text-[12px] font-medium text-slate-700">"BANG KATA ILHAM KENAPA ITU OPENING NYA terlalu di besar besar kan"</p><span className="text-[9px] font-bold text-rose-600 mt-1 block">Negative • @dellyapingg</span></div></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-center">
          <h2 className="text-[13px] font-black text-slate-800 tracking-wider uppercase mb-1">Emotion Distribution Analysis</h2>
          <p className="text-[10px] text-slate-500 mb-6">Kategorisasi emosi dominan dari audiens (Top 3)</p>
          <div className="space-y-5">
            <div><div className="flex justify-between text-[11px] font-bold mb-2 text-slate-700"><span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-rose-500"></div> Marah</span><span className="text-rose-500">25%</span></div><div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-rose-500 w-[25%] rounded-full"></div></div></div>
            <div><div className="flex justify-between text-[11px] font-bold mb-2 text-slate-700"><span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-amber-400"></div> Senang</span><span className="text-amber-500">60%</span></div><div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-amber-400 w-[60%] rounded-full"></div></div></div>
            <div><div className="flex justify-between text-[11px] font-bold mb-2 text-slate-700"><span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-blue-500"></div> Sedih</span><span className="text-blue-500">15%</span></div><div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-blue-500 w-[15%] rounded-full"></div></div></div>
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-center items-center text-center">
          <h2 className="text-[13px] font-black text-slate-800 tracking-wider uppercase mb-1">Total Feedback Analyzed</h2>
          <p className="text-[10px] text-slate-500 mb-4">Volume pesan YouTube yang diproses oleh NLP</p>
          <h3 className="text-5xl font-black text-slate-800 mb-6 tracking-tight">12,450</h3>
          <div className="w-full max-w-md">
            <div className="w-full h-4 bg-slate-100 rounded-full flex overflow-hidden mb-4 shadow-inner">
              <div className="h-full bg-slate-400" style={{ width: '65%' }}></div><div className="h-full bg-rose-500" style={{ width: '20%' }}></div><div className="h-full bg-emerald-500" style={{ width: '15%' }}></div>
            </div>
            <div className="flex justify-between items-center px-2">
              <div className="text-center"><span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Netral</span><span className="text-[14px] font-black text-slate-700">65% <span className="text-[10px] font-medium text-slate-400 font-normal">(8.092)</span></span></div>
              <div className="text-center"><span className="text-[10px] font-bold text-rose-400 uppercase block mb-1">Negative</span><span className="text-[14px] font-black text-rose-600">20% <span className="text-[10px] font-medium text-rose-400 font-normal">(2.490)</span></span></div>
              <div className="text-center"><span className="text-[10px] font-bold text-emerald-400 uppercase block mb-1">Positive</span><span className="text-[14px] font-black text-emerald-600">15% <span className="text-[10px] font-medium text-emerald-400 font-normal">(1.868)</span></span></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[350px]">
          <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
            <div><h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">Sentiment & Keyword Analysis</h2><p className="text-[10px] text-slate-500 mt-1">Frekuensi kata terbanyak</p></div><Database size={16} className="text-slate-400" />
          </div>
          <div className="flex-1 overflow-y-auto">
            <table className="w-full text-left text-[12px]">
              <thead className="bg-white border-b border-slate-100 text-slate-400 font-bold uppercase tracking-wider text-[10px] sticky top-0"><tr><th className="px-5 py-3">Kata (Keyword)</th><th className="px-5 py-3 text-center">Frekuensi</th><th className="px-5 py-3 text-center">Jenis Sentimen</th></tr></thead>
              <tbody>
                {sentimentKeywords.map((row, i) => {
                  let badgeColor = 'bg-slate-100 text-slate-600 border-slate-200'
                  if (row.type === 'Positive') badgeColor = 'bg-emerald-50 text-emerald-600 border-emerald-100'
                  if (row.type === 'Negative') badgeColor = 'bg-rose-50 text-rose-600 border-rose-100'
                  return (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3 font-bold text-slate-700">{row.word}</td><td className="px-5 py-3 font-black text-slate-800 text-center">{row.freq}</td>
                      <td className="px-5 py-3 text-center"><span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border shadow-sm ${badgeColor}`}>{row.type}</span></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col h-[350px]">
          <div className="flex justify-between items-start mb-4">
            <div><h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">Sentiment Trend & Drift</h2><p className="text-[10px] text-slate-500 mt-1">Volume berdasarkan waktu (menit)</p></div><TrendingUp size={16} className="text-slate-400" />
          </div>
          <div className="flex-1 w-full relative border-l border-b border-slate-200 px-2 pt-8 pb-4">
            <div className="absolute left-[-24px] bottom-4 text-[9px] font-bold text-slate-400">0</div><div className="absolute left-[-32px] top-8 text-[9px] font-bold text-slate-400">1000</div>
            <svg viewBox="0 0 400 150" className="w-full h-full overflow-visible drop-shadow-sm">
              <path d="M0,130 Q80,120 160,90 T320,110 T400,100" fill="none" stroke="#10b981" strokeWidth="2" strokeLinecap="round" />
              <circle cx="80" cy="125" r="4" fill="#10b981" className="shadow-sm" />
              <path d="M0,40 Q80,20 160,50 T320,30 T400,60" fill="none" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" />
              <path d="M0,140 Q80,135 160,130 T320,70 T400,110" fill="none" stroke="#f43f5e" strokeWidth="2" strokeLinecap="round" strokeDasharray="4,4" />
            </svg>
            <div className="absolute w-full flex justify-between bottom-[-20px] text-[9px] font-bold text-slate-400"><span>0m</span><span>1m</span><span>2m</span><span>3m</span><span>4m</span><span>5m</span></div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-sm font-black text-slate-800 mb-4 flex items-center gap-2"><BrainCircuit size={16} className="text-indigo-600" /> Uji Sentimen Manual</h3>
        <div className="flex gap-4">
          <textarea className="w-full h-24 p-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="Masukkan komentar atau opini pelanggan di sini..." value={manualText} onChange={(e) => setManualText(e.target.value)} />
          <button onClick={analyzeManualSentiment} disabled={isAnalyzing || !manualText} className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50">{isAnalyzing ? 'Analisis...' : 'Analisis'}</button>
        </div>
        {manualSentiment && (
          <div className={`mt-4 p-3 rounded-lg flex items-center gap-3 font-bold text-sm border ${manualSentiment === 'Positif' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : manualSentiment === 'Negatif' ? 'bg-rose-50 text-rose-700 border-rose-100' : 'bg-slate-100 text-slate-700 border-slate-200'}`}>
            <Info size={18} /> Hasil Analisis: Sentimen terdeteksi sebagai <span className="uppercase tracking-widest px-2 py-0.5 bg-white/50 rounded">{manualSentiment}</span>
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col">
        <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
          <div className="flex items-center gap-2"><MessageCircle size={16} className="text-slate-600" /><h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">RAW CUSTOMER FEEDBACK (LIVE NLP)</h2></div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead className="bg-white border-b border-slate-100 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <tr><th className="px-5 py-4 whitespace-nowrap">Time</th><th className="px-5 py-4 whitespace-nowrap">Author</th><th className="px-5 py-4 w-1/2">Message</th><th className="px-5 py-4 whitespace-nowrap text-center">Sentiment</th><th className="px-5 py-4 whitespace-nowrap text-center">Detected Emotion</th></tr>
            </thead>
            <tbody>
              {youtubeChatData.map((row, i) => {
                let badgeColor = 'bg-slate-100 text-slate-600 border-slate-200'
                if (row.sentiment === 'Positive') badgeColor = 'bg-emerald-50 text-emerald-600 border-emerald-100'
                if (row.sentiment === 'Negative') badgeColor = 'bg-rose-50 text-rose-600 border-rose-100'
                let emotionColor = 'bg-slate-50 text-slate-600 border-slate-200'
                if (row.emotion === 'Marah') emotionColor = 'bg-rose-50 text-rose-600 border-rose-100'
                if (row.emotion === 'Senang') emotionColor = 'bg-amber-50 text-amber-600 border-amber-100'
                if (row.emotion === 'Sedih') emotionColor = 'bg-blue-50 text-blue-600 border-blue-100'

                return (
                  <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-5 py-4 font-bold text-slate-500 whitespace-nowrap"><span className="text-slate-800">{row.time}</span></td>
                    <td className="px-5 py-4 font-bold text-indigo-600 whitespace-nowrap">{row.author}</td>
                    <td className="px-5 py-4 font-medium text-slate-700 leading-relaxed pr-8">{row.message}</td>
                    <td className="px-5 py-4 text-center whitespace-nowrap"><span className={`px-3 py-1 rounded-md text-[10px] font-bold border shadow-sm ${badgeColor}`}>{row.sentiment}</span></td>
                    <td className="px-5 py-4 text-center whitespace-nowrap"><span className={`text-[11px] font-bold px-2.5 py-1 rounded border ${emotionColor}`}>{row.emotion}</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
