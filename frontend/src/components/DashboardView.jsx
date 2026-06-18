import React, { useState, useEffect } from 'react'
import { LayoutDashboard, MessageSquare, User, AlertTriangle, DollarSign, HeartPulse } from 'lucide-react'
import { AreaChart, Area, Tooltip, ResponsiveContainer } from 'recharts'

const API_BASE_URL = 'http://127.0.0.1:8000'

export default function DashboardView({ setActiveTab }) {
  const [churnFilter, setChurnFilter] = useState('All')
  const [feedbackFilter, setFeedbackFilter] = useState('All')
  
  const [summaryStats, setSummaryStats] = useState([])
  const [customerChurnData, setCustomerChurnData] = useState([])
  const [feedbackData, setFeedbackData] = useState([])
  const [totalCustomers, setTotalCustomers] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    fetch(`${API_BASE_URL}/api/dashboard/summary`)
      .then(res => res.json())
      .then(data => {
        if (!isMounted) return
        if (data.summaryStats) setSummaryStats(data.summaryStats)
        if (data.customerChurnData) setCustomerChurnData(data.customerChurnData)
        if (data.feedbackData) setFeedbackData(data.feedbackData)
        if (data.totalCustomers) setTotalCustomers(data.totalCustomers)
        setLoading(false)
      })
      .catch(err => {
        console.error("Gagal memuat data dari backend:", err)
        setLoading(false)
      })

    return () => { isMounted = false }
  }, [])

  const filteredChurn = churnFilter === 'All' ? customerChurnData : customerChurnData.filter(c => c.status === churnFilter)
  const filteredFeedback = feedbackFilter === 'All' ? feedbackData : feedbackData.filter(f => f.sentiment === feedbackFilter)

  // Kustom tooltip untuk menampilkan angka saat grafik di-hover
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 text-white text-[11px] px-3 py-1.5 rounded-lg shadow-lg border border-slate-700">
          <p className="font-bold">{payload[0].value}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) return <div className="p-10 text-center animate-pulse text-indigo-500 font-bold">Memuat Analitik LapisAI dari Database CSV...</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      <div className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-1.5 bg-white border border-slate-200 text-slate-500 rounded-md shadow-sm"><LayoutDashboard size={18} /></div>
            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Dashboard</h1>
          </div>
          <p className="text-[13px] text-slate-500 font-medium">Overview of your ML customer churn and NLP sentiment metrics.</p>
        </div>
        <div className="text-right">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Total Customers</p>
          <p className="text-2xl font-black text-slate-800 tracking-tight">{totalCustomers.toLocaleString()}</p>
        </div>
      </div>

      {/* SUMMARY CARDS DENGAN GRAPH INTERAKTIF */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {summaryStats.map((stat, index) => {
          // Memformat chartData untuk Recharts Area Graph
          const chartData = stat.chartData ? stat.chartData.map((val, i) => ({ index: i, value: val })) : [];
          // Pewarnaan dinamis: Merah muda untuk Risiko, Ungu/Indigo untuk NPS
          const isLoss = stat.id === 'risk' || stat.id === 'revenue';
          const color = isLoss ? '#f43f5e' : '#6366f1'; 

          return (
            <div key={index} className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:border-slate-300 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-[11px] font-black text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    {stat.id === 'risk' && <AlertTriangle size={14} className="text-rose-500" />}
                    {stat.id === 'revenue' && <DollarSign size={14} className="text-rose-500" />}
                    {stat.id === 'nps' && <HeartPulse size={14} className="text-indigo-500" />}
                    {stat.label}
                  </p>
                  <h3 className="text-3xl font-black text-slate-800 tracking-tight">{stat.value}</h3>
                </div>
              </div>
              <div className="h-14 w-full relative -bottom-2 -left-2">
                {/* Menggunakan Graph murni sebagai pengganti Sparkline lama */}
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id={`color-${index}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={color} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(0,0,0,0.1)' }} />
                    <Area type="monotone" dataKey="value" stroke={color} strokeWidth={2.5} fill={`url(#color-${index})`} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Kolom 1: Tabel Customer Churn (Sesuai UI asli) */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[400px]">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
            <div className="flex items-center gap-2">
              <User size={16} className="text-slate-600" />
              <h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">Customer Churn Analysis (ML)</h2>
            </div>
            <div className="flex gap-2">
              {['All', 'Churned', 'Not Churned'].map(filter => (
                <button key={filter} onClick={() => setChurnFilter(filter)} className={`text-[10px] font-bold px-3 py-1.5 rounded-full transition-all ${churnFilter === filter ? 'bg-indigo-600 text-white shadow-md' : 'bg-white text-slate-500 hover:bg-slate-100 border border-slate-200'}`}>
                  {filter}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {filteredChurn.map((customer, i) => {
              const isChurned = customer.status === 'Churned';
              const badgeColor = isChurned ? 'bg-rose-50 text-rose-600 border-rose-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100';
              return (
                <div key={i} className="flex justify-between items-center p-3 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors bg-white">
                  <div>
                    <p className="text-[13px] font-bold text-slate-800 mb-0.5">{customer.id}</p>
                    <p className="text-[11px] font-medium text-slate-500">{customer.type}</p>
                  </div>
                  <div className="text-right flex flex-col items-end gap-1.5">
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded border ${badgeColor}`}>{customer.status}</span>
                    <span className="text-[12px] font-black text-slate-800 tracking-tight">Prob: {(parseFloat(customer.score)*100).toFixed(1)}%</span>
                  </div>
                </div>
              )
            })}
          </div>
          <div className="p-4 border-t border-slate-100 flex justify-end bg-slate-50/50 rounded-b-2xl">
            <button onClick={() => setActiveTab('prediction')} className="bg-indigo-500 hover:bg-indigo-600 text-white text-[11px] font-bold px-5 py-2.5 rounded-lg shadow-sm transition-colors">Go to Prediction Engine</button>
          </div>
        </div>

        {/* Kolom 2: Tabel Customer Feedback (Sesuai UI asli) */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[400px]">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
            <div className="flex items-center gap-2">
              <MessageSquare size={16} className="text-slate-600" />
              <h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">Customer Feedback (NLP)</h2>
            </div>
            <div className="flex gap-2">
              {['All', 'Positive', 'Negative'].map(filter => (
                <button key={filter} onClick={() => setFeedbackFilter(filter)} className={`text-[10px] font-bold px-3 py-1.5 rounded-full transition-all ${feedbackFilter === filter ? 'bg-indigo-600 text-white shadow-md' : 'bg-white text-slate-500 hover:bg-slate-100 border border-slate-200'}`}>
                  {filter}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {filteredFeedback.map((feedback, i) => {
              let badgeColor = 'bg-slate-50 text-slate-600 border-slate-200';
              if (feedback.sentiment === 'Positive') badgeColor = 'bg-emerald-50 text-emerald-600 border-emerald-100';
              if (feedback.sentiment === 'Negative') badgeColor = 'bg-rose-50 text-rose-600 border-rose-100';
              return (
                <div key={i} className="flex justify-between items-center p-3 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors bg-white">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center border border-indigo-100 text-indigo-500 shadow-sm mt-0.5 shrink-0"><MessageSquare size={14} /></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-bold text-slate-800 mb-0.5">{feedback.id}</p>
                      <p className="text-[11px] font-medium text-slate-500 truncate" title={feedback.text}>{feedback.text}</p>
                    </div>
                  </div>
                  <div className="text-right flex flex-col items-end gap-1.5 flex-shrink-0">
                    <span className="text-[13px] font-black text-slate-800">NPS: {feedback.nps}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded border ${badgeColor}`}>{feedback.sentiment}</span>
                  </div>
                </div>
              )
            })}
          </div>
          <div className="p-4 border-t border-slate-100 flex items-center justify-between bg-slate-50/50 rounded-b-2xl">
            <button onClick={() => setActiveTab('sentiment')} className="bg-indigo-500 hover:bg-indigo-600 text-white text-[11px] font-bold px-5 py-2.5 rounded-lg shadow-sm transition-colors">Open NLP Analysis</button>
          </div>
        </div>
      </div>
    </div>
  )
}