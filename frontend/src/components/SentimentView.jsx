import React, { useEffect, useState } from 'react'
import { MessageSquare, BrainCircuit, MessageCircle, PieChart, Sparkles } from 'lucide-react'
import { Sparkline } from './Sparkline'
import { popupDataStore, youtubeChatData } from './MockData.jsx'
import { apiGet } from '../lib/api'

export default function SentimentView() {
  const [activeModal, setActiveModal] = React.useState(null)
  const [analysis, setAnalysis] = useState(null)

  useEffect(() => {
    let alive = true
    apiGet('/api/sentiment/analysis')
      .then((data) => {
        if (alive) setAnalysis(data)
      })
      .catch(() => {
        if (alive) setAnalysis(null)
      })
    return () => {
      alive = false
    }
  }, [])

  const summary = analysis || {
    executive_summary:
      'Berdasarkan analisis NLP pada 5 menit pertama sesi Live Stream, sentimen didominasi oleh respons Netral (60%) dan Antusias (20%).',
    total_feedback: 12450,
    sentiment_distribution: { positive: 20, negative: 20, neutral: 60 },
    keywords: [
      { word: 'Ilham', freq: 412, type: 'Netral' },
      { word: 'Opening', freq: 289, type: 'Negative' },
      { word: 'Lesss Goooo', freq: 205, type: 'Positive' },
      { word: 'Bang', freq: 189, type: 'Netral' },
    ],
    raw_feedback: youtubeChatData,
  }

  const TableModal = ({ modalKey, onClose }) => {
    if (!modalKey) return null
    const info = popupDataStore[modalKey]
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity" onClick={onClose}></div>
        <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
          <div className="bg-rose-400 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MessageCircle size={24} className="text-white drop-shadow-sm" />
              <h2 className="text-base font-black tracking-wide">{info.title}</h2>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-lg transition-colors"><span className="text-xl">×</span></button>
          </div>
          <div className="p-6 pb-4">
            <p className="text-[13px] font-bold text-slate-800 mb-4">{info.subtitle}</p>
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-left text-[13px]">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-800 font-black">
                  <tr>
                    <th className="px-4 py-3 border-r border-slate-200 text-center">Customer ID</th>
                    <th className="px-4 py-3 border-r border-slate-200 text-center">{info.col2Label || 'Plan Type'}</th>
                    <th className="px-4 py-3 border-r border-slate-200 text-center">{info.col3Label}</th>
                    {info.hasCol4 && <th className="px-4 py-3 border-r border-slate-200 text-center">{info.col4Label}</th>}
                    <th className="px-4 py-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {info.data.map((row, i) => (
                    <tr key={i} className="border-b border-slate-100 hover:bg-slate-50/50 font-bold text-slate-700">
                      <td className="px-4 py-2.5 border-r border-slate-100 text-center">{row.id}</td>
                      <td className="px-4 py-2.5 border-r border-slate-100 text-center">{row.plan}</td>
                      <td className="px-4 py-2.5 border-r border-slate-100 text-center">
                        <span className={`px-4 py-1 rounded shadow-sm text-[11px] uppercase tracking-wider ${row.color}`}>{row.value}</span>
                      </td>
                      {info.hasCol4 && <td className="px-4 py-2.5 border-r border-slate-100 text-center">{row.loss}</td>}
                      <td className="px-4 py-2.5 text-center">
                        <button className="bg-indigo-500 hover:bg-indigo-600 text-white text-[11px] font-black px-4 py-1.5 rounded-lg shadow-sm transition-colors">{info.actionLabel}</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20 relative">
      <TableModal modalKey={activeModal} onClose={() => setActiveModal(null)} />

      <div className="flex items-center gap-3 mb-6">
        <div className="p-1.5 bg-white border border-slate-200 text-slate-500 rounded-md shadow-sm">
          <MessageSquare size={18} />
        </div>
        <h1 className="text-xl font-black text-slate-800 tracking-tight">Feedback & Sentiment Intelligence</h1>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        <div className="bg-slate-50 border-b border-slate-100 p-4">
          <div className="flex items-center gap-2">
            <BrainCircuit size={18} className="text-indigo-500" />
            <h3 className="text-[13px] font-black text-slate-800 tracking-wider">NLP SENTIMENT OVERVIEW</h3>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          <div className="p-6 flex flex-col justify-center">
            <p className="text-[11px] font-bold text-slate-400 uppercase mb-2">Total Feedback Analyzed</p>
            <h2 className="text-4xl font-black text-slate-800 tracking-tight mb-4">{summary.total_feedback.toLocaleString('id-ID')}</h2>
            <div className="w-full h-3 bg-slate-100 rounded-full flex overflow-hidden mb-3">
              <div className="h-full bg-emerald-400" style={{ width: `${summary.sentiment_distribution.positive}%` }}></div>
              <div className="h-full bg-amber-300" style={{ width: `${summary.sentiment_distribution.neutral}%` }}></div>
              <div className="h-full bg-rose-400" style={{ width: `${summary.sentiment_distribution.negative}%` }}></div>
            </div>
            <div className="flex justify-between text-[11px] font-bold">
              <span className="flex items-center gap-1.5 text-slate-600"><div className="w-2 h-2 rounded-full bg-emerald-400"></div> Positive ({summary.sentiment_distribution.positive}%)</span>
              <span className="flex items-center gap-1.5 text-slate-600"><div className="w-2 h-2 rounded-full bg-amber-300"></div> Neutral ({summary.sentiment_distribution.neutral}%)</span>
              <span className="flex items-center gap-1.5 text-slate-600"><div className="w-2 h-2 rounded-full bg-rose-400"></div> Negative ({summary.sentiment_distribution.negative}%)</span>
            </div>
          </div>
          <div className="p-6 flex flex-col justify-center items-center text-center">
            <p className="text-[11px] font-bold text-slate-400 uppercase mb-2">Average Sentiment Score</p>
            <div className="flex items-end gap-1 mb-2">
              <h2 className="text-4xl font-black text-indigo-600 tracking-tight">6.8</h2>
              <span className="text-sm font-bold text-slate-400 mb-1">/ 10</span>
            </div>
            <p className="text-[11px] font-semibold text-slate-500 mb-4 bg-slate-50 px-3 py-1 rounded-full border border-slate-100">Cenderung Netral</p>
            <div className="w-full max-w-[150px] opacity-60">
              <Sparkline data={[5, 6, 7, 6, 5, 4, 6]} colorClass="indigo" />
            </div>
          </div>
          <div className="p-6 flex flex-col justify-center">
            <p className="text-[11px] font-bold text-slate-400 uppercase mb-4">Top Keyword Extraction</p>
            <div className="flex flex-wrap gap-2">
              {summary.keywords.map((row, i) => (
                <span key={i} className={`text-[11px] font-bold px-3 py-1.5 rounded-lg shadow-sm border ${row.type === 'Positive' ? 'bg-emerald-50 border-emerald-100 text-emerald-600' : row.type === 'Negative' ? 'bg-rose-50 border-rose-100 text-rose-600' : 'bg-slate-50 border-slate-200 text-slate-600'}`}>
                  {row.word} ({row.freq})
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col h-[300px]">
          <h4 className="text-[12px] font-black text-slate-800 mb-2">Sentiment Trend (Session Timeline)</h4>
          <div className="flex-1 w-full relative border-l border-b border-slate-200 px-2 pt-4">
            <div className="absolute left-[-20px] bottom-0 text-[8px] font-bold text-slate-400">0</div>
            <div className="absolute left-[-24px] top-4 text-[8px] font-bold text-slate-400">100</div>
            <svg viewBox="0 0 400 150" className="w-full h-full overflow-visible drop-shadow-md">
              <path d="M0,80 Q80,70 160,85 T320,60 T400,75" fill="none" stroke="#fcd34d" strokeWidth="3" strokeLinecap="round" />
              <circle cx="80" cy="74" r="4" fill="#fcd34d" className="shadow-sm" />
              <circle cx="160" cy="85" r="4" fill="#fcd34d" className="shadow-sm" />
              <circle cx="320" cy="60" r="4" fill="#fcd34d" className="shadow-sm" />
              <circle cx="400" cy="75" r="4" fill="#fcd34d" className="shadow-sm" />
              <path d="M0,120 Q80,90 160,110 T320,130 T400,100" fill="none" stroke="#fb7185" strokeWidth="3" strokeLinecap="round" strokeDasharray="5,5" />
            </svg>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col h-[300px]">
          <div className="flex items-center gap-2 mb-2">
            <PieChart size={16} className="text-slate-700" />
            <h4 className="text-[12px] font-black text-slate-800">EMOTION DISTRIBUTION ANALYSIS</h4>
          </div>
          <div className="flex-1 space-y-5 flex flex-col justify-center">
            <div>
              <div className="flex justify-between text-[11px] font-bold mb-1.5 text-slate-700">
                <span>Neutral / Calm</span><span className="text-slate-500">60%</span>
              </div>
              <div className="w-full h-4 bg-slate-100 rounded-full flex items-center relative overflow-hidden"><div className="h-full bg-slate-400 w-[60%]"></div></div>
            </div>
            <div>
              <div className="flex justify-between text-[11px] font-bold mb-1.5 text-slate-700">
                <span>Excitement / Anticipation</span><span className="text-emerald-500">20%</span>
              </div>
              <div className="w-full h-4 bg-slate-100 rounded-full flex items-center relative overflow-hidden"><div className="h-full bg-emerald-400 w-[20%]"></div></div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-indigo-50 to-white border border-indigo-100 rounded-2xl p-6 shadow-sm flex flex-col sm:flex-row gap-5 items-start relative overflow-hidden">
        <div className="w-12 h-12 bg-indigo-500 rounded-full flex items-center justify-center shrink-0 shadow-md shadow-indigo-200 z-10">
          <Sparkles className="text-white" size={20} />
        </div>
        <div className="z-10">
          <h4 className="text-[13px] font-black text-indigo-900 mb-2 uppercase tracking-wider">SUMMARY SESSION</h4>
          <p className="text-[13px] text-slate-700 leading-relaxed font-medium">
            {summary.executive_summary}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col">
        <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
          <div className="flex items-center gap-2">
            <MessageCircle size={16} className="text-slate-600" />
            <h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">RAW CUSTOMER FEEDBACK (LIVE NLP)</h2>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead className="bg-white border-b border-slate-100 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-5 py-4 whitespace-nowrap">Time / Elapsed</th>
                <th className="px-5 py-4 whitespace-nowrap">Author</th>
                <th className="px-5 py-4 w-1/3">Message</th>
                <th className="px-5 py-4 whitespace-nowrap text-center">Sentiment</th>
                <th className="px-5 py-4 whitespace-nowrap text-center">Detected Emotion</th>
              </tr>
            </thead>
            <tbody>
              {summary.raw_feedback.map((row, i) => {
                let badgeColor = 'bg-slate-100 text-slate-600 border-slate-200'
                if (row.sentiment === 'Positive') badgeColor = 'bg-emerald-50 text-emerald-600 border-emerald-100'
                if (row.sentiment === 'Negative') badgeColor = 'bg-rose-50 text-rose-600 border-rose-100'
                if (row.sentiment === 'Netral') badgeColor = 'bg-amber-50 text-amber-600 border-amber-100'

                return (
                  <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-5 py-4 font-bold text-slate-500 whitespace-nowrap">
                      <span className="text-slate-800 mr-2">{row.time}</span>
                    </td>
                    <td className="px-5 py-4 font-bold text-indigo-600 whitespace-nowrap">{row.author}</td>
                    <td className="px-5 py-4 font-medium text-slate-700 leading-relaxed pr-8">{row.message}</td>
                    <td className="px-5 py-4 text-center whitespace-nowrap">
                      <span className={`px-3 py-1 rounded-md text-[10px] font-bold border shadow-sm ${badgeColor}`}>
                        {row.sentiment}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-center whitespace-nowrap">
                      <span className="text-[11px] font-bold text-slate-600 bg-slate-50 px-2 py-1 rounded border border-slate-100">
                        {row.emotion}
                      </span>
                    </td>
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
