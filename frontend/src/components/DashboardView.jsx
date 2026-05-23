import React, { useEffect, useState } from 'react'
import { LayoutDashboard, MessageSquare } from 'lucide-react'
import { Sparkline } from './Sparkline'
import { summaryStats, customerChurnData, feedbackData } from './MockData.jsx'
import { apiGet } from '../lib/api'

export default function DashboardView() {
  const [remoteData, setRemoteData] = useState(null)

  useEffect(() => {
    let mounted = true
    apiGet('/api/dashboard/summary')
      .then((data) => {
        if (mounted) setRemoteData(data)
      })
      .catch(() => {
        if (mounted) setRemoteData(null)
      })
    return () => {
      mounted = false
    }
  }, [])

  const stats = remoteData?.summaryStats || summaryStats
  const churnData = remoteData?.customerChurnData || customerChurnData
  const feeds = remoteData?.feedbackData || feedbackData

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-1.5 bg-white border border-slate-200 text-slate-500 rounded-md shadow-sm">
          <LayoutDashboard size={18} />
        </div>
        <h1 className="text-2xl font-black text-slate-800 tracking-tight">Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-500 mb-2">{stat.label}</h3>
              <p className="text-3xl font-black text-slate-800 tracking-tight">{stat.value}</p>
            </div>
            <div className="mt-4 flex justify-end opacity-70 group-hover:opacity-100 transition-opacity">
              <Sparkline data={stat.chartData} highlightIndex={stat.highlight} colorClass={stat.color} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[550px]">
          <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
            <h2 className="text-[15px] font-black text-slate-800">Customer Churn</h2>
          </div>
          <div className="px-5 py-3 grid grid-cols-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-50">
            <span>Customer ID</span>
            <span className="text-right">Details</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {churnData.map((customer, idx) => (
              <div key={idx} className="flex items-center justify-between p-3.5 hover:bg-slate-50 rounded-xl transition-colors group cursor-pointer">
                <div className="flex items-center gap-4">
                  <img src={customer.image} alt="avatar" className="w-9 h-9 rounded-lg object-cover border border-slate-200 shadow-sm" />
                  <div>
                    <p className="text-[13px] font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">{customer.id}</p>
                    <p className="text-[11px] font-medium text-slate-500">{customer.type}</p>
                  </div>
                </div>
                <div className="text-right flex flex-col items-end gap-1">
                  <span className="text-[13px] font-black text-slate-800">{customer.score}</span>
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${customer.status === 'Churned' ? 'bg-rose-50 text-rose-600 border-rose-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'}`}>
                    {customer.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[550px]">
          <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
            <h2 className="text-[15px] font-black text-slate-800">Feedback Customer</h2>
          </div>
          <div className="px-5 py-3 grid grid-cols-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-50">
            <span>Customer ID</span>
            <span className="text-right">Details</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {feeds.map((feedback, idx) => {
              let badgeColor = 'bg-slate-100 text-slate-600 border-slate-200'
              if (feedback.sentiment === 'Positive') badgeColor = 'bg-emerald-50 text-emerald-600 border-emerald-100'
              if (feedback.sentiment === 'Negative') badgeColor = 'bg-rose-50 text-rose-600 border-rose-100'
              if (feedback.sentiment === 'Netral') badgeColor = 'bg-amber-50 text-amber-600 border-amber-100'

              return (
                <div key={idx} className="flex items-start justify-between p-3.5 hover:bg-slate-50 rounded-xl transition-colors group cursor-pointer gap-4">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <MessageSquare size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-bold text-slate-800 mb-0.5">{feedback.id}</p>
                      <p className="text-[11px] font-medium text-slate-500 truncate group-hover:text-slate-700 transition-colors line-clamp-1">{feedback.text}</p>
                    </div>
                  </div>
                  <div className="text-right flex flex-col items-end gap-1.5 flex-shrink-0">
                    <span className="text-[13px] font-black text-slate-800">NPS: {feedback.nps}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded border ${badgeColor}`}>
                      {feedback.sentiment}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
