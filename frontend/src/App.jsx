import React, { useState } from 'react'
import LoginPage from './components/LoginPage'
import DashboardView from './components/DashboardView'
import PredictionView from './components/PredictionView'
import SentimentView from './components/SentimentView'
import { BarChart3, Settings, LayoutDashboard, Bell, MessageSquare, HelpCircle, LogOut, Search, Target, ChevronDown } from 'lucide-react'
import { summaryStats, customerChurnData, feedbackData, systemLogs } from './components/MockData.jsx'

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [activeTab, setActiveTab] = useState('sentiment')

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />
  }

  return (
    <div className="flex h-screen bg-[#F8FAFC] font-sans overflow-hidden">
      
      {/* 1. Thin Sidebar (Navigasi Global) */}
      <aside className="w-16 bg-white border-r border-slate-200 h-screen flex flex-col items-center py-5 z-20 flex-shrink-0">
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-md shadow-indigo-200 mb-8 cursor-pointer">
          <LayoutDashboard size={20} className="text-white" />
        </div>
        
        <nav className="flex flex-col gap-4 w-full px-2">
          
          {/* DASHBOARD */}
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full aspect-square rounded-xl flex items-center justify-center transition-all ${activeTab === 'dashboard' ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-indigo-500'}`}
            title="Dashboard"
          >
            <BarChart3 size={20} strokeWidth={activeTab === 'dashboard' ? 2.5 : 2} />
          </button>

          {/* PREDICTION ENGINE */}
          <button 
            onClick={() => setActiveTab('prediction')}
            className={`w-full aspect-square rounded-xl flex items-center justify-center transition-all ${activeTab === 'prediction' ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-indigo-500'}`}
            title="Prediction Engine"
          >
            <Target size={20} strokeWidth={activeTab === 'prediction' ? 2.5 : 2} />
          </button>

          {/* SENTIMENT */}
          <button 
            onClick={() => setActiveTab('sentiment')}
            className={`w-full aspect-square rounded-xl flex items-center justify-center transition-all ${activeTab === 'sentiment' ? 'bg-indigo-50 text-indigo-600 shadow-sm' : 'text-slate-400 hover:bg-slate-50 hover:text-indigo-500'}`}
            title="Feedback & Sentiment"
          >
            <MessageSquare size={20} strokeWidth={activeTab === 'sentiment' ? 2.5 : 2} />
          </button>

          <button className={`w-full aspect-square rounded-xl flex items-center justify-center transition-all text-slate-400 hover:bg-slate-50 hover:text-indigo-500`} title="Settings">
            <Settings size={20} />
          </button>
        </nav>

        <div className="mt-auto flex flex-col gap-4 w-full px-2 items-center">
          <button className="w-full aspect-square rounded-xl flex items-center justify-center text-slate-400 hover:bg-slate-50 hover:text-slate-600 transition-all">
            <HelpCircle size={20} />
          </button>
          <div className="w-10 h-10 rounded-full border-2 border-indigo-100 overflow-hidden cursor-pointer mt-2 hover:border-indigo-400 transition-colors">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Admin" alt="User" className="w-full h-full object-cover bg-indigo-50" />
          </div>
        </div>
      </aside>

      {/* 2. Left Panel (Context/Logs/Alerts) */}
      <aside className="w-[300px] bg-white border-r border-slate-200 h-screen overflow-y-auto flex flex-col z-10 flex-shrink-0 hidden md:flex">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-8">
            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Lapis<span className="text-indigo-600">AI</span></h1>
          </div>

          <div className="mb-10">
            <p className="text-[13px] text-slate-400 font-medium">Welcome,</p>
            <h2 className="text-2xl font-black text-slate-800 tracking-tight">Admin</h2>
          </div>

          <div className="mb-10">
            <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-wider mb-4 text-center">System Log</h3>
            <div className="space-y-3">
              {systemLogs.map((log, i) => (
                <div key={i} className="bg-slate-50 rounded-xl p-3 flex gap-3 border border-slate-100 hover:border-slate-200 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center flex-shrink-0 border border-slate-100">
                    {log.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-0.5">
                      <h4 className="text-[11px] font-bold text-slate-800">{log.title}</h4>
                      <span className="text-[9px] font-semibold text-slate-400 whitespace-nowrap ml-2">{log.time}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 leading-snug">{log.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* 3. Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <header className="bg-transparent px-8 py-5 flex items-center justify-end z-20 sticky top-0">
          <div className="flex items-center gap-4">
            <div className="relative mr-2">
              <input 
                type="text" placeholder="Search..." 
                className="bg-white text-sm border border-slate-200 rounded-full pl-4 pr-10 py-2 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none w-56 shadow-sm"
              />
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            </div>
            <button className="relative text-slate-400 hover:text-indigo-600 transition-colors p-2 rounded-full hover:bg-slate-200 bg-white shadow-sm border border-slate-200">
              <Bell size={18} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border border-white"></span>
            </button>
            <button 
              onClick={() => setIsAuthenticated(false)}
              className="text-slate-400 hover:text-rose-600 transition-colors p-2 rounded-full hover:bg-slate-200 bg-white shadow-sm border border-slate-200" title="Logout"
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-8">
          {activeTab === 'dashboard' && <DashboardView />}
          {activeTab === 'prediction' && <PredictionView />}
          {activeTab === 'sentiment' && <SentimentView />}
        </div>
      </main>

    </div>
  )
}
