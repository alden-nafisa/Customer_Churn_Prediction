import React, { useState } from 'react'
import LoginPage from './components/LoginPage'
import DashboardView from './components/DashboardView'
import PredictionView from './components/PredictionView'
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

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />
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
          <button className="w-full aspect-square rounded-xl flex items-center justify-center text-slate-400 hover:bg-slate-50 hover:text-slate-600 transition-all">
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
    </div>
  )
}
