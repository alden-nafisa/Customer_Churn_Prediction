import React, { useEffect, useState } from 'react'
import { Target, BarChart2, X, Activity, ChevronDown } from 'lucide-react'
import { popupDataStore } from './MockData.jsx'
import { apiGet, apiPost } from '../lib/api'

export default function PredictionView() {
  const [fetchState, setFetchState] = useState('idle')
  const [predictState, setPredictState] = useState('idle')
  const [customerId, setCustomerId] = useState('')
  const [planType, setPlanType] = useState('Starter')
  const [modelChoice, setModelChoice] = useState('Ensemble (Recommended)')
  const [activeModal, setActiveModal] = useState(null)
  const [customerProfile, setCustomerProfile] = useState(null)
  const [predictionResult, setPredictionResult] = useState(null)
  const [customerOptions, setCustomerOptions] = useState([])

  const [formData, setFormData] = useState({
    paymentDelay: '', lastLogin: '', dunning: '', nps: '', ticketRatio: '', revAtRisk: ''
  })

  useEffect(() => {
    apiGet(`/api/customers?plan_type=${encodeURIComponent(planType)}`)
      .then((data) => {
        setCustomerOptions(data.customers || [])
      })
      .catch(() => {
        setCustomerOptions([
          { customer_id: 'C-0011' },
          { customer_id: 'C-0091' },
          { customer_id: 'C-0201' },
        ])
      })
  }, [planType])

  const handleFetch = () => {
    if (!customerId) return
    setFetchState('fetching')
    setPredictState('idle')
    apiGet(`/api/customer/${customerId}/features?plan_type=${encodeURIComponent(planType)}`)
      .then((data) => {
        setCustomerProfile(data)
        setFormData({
          paymentDelay: String(data.profile?.payment_delay_days_mean ?? 0),
          lastLogin: String(data.profile?.days_since_last_login ?? 0),
          dunning: String(data.profile?.dunning_event_count ?? 0),
          nps: String(data.profile?.avg_nps_score ?? 0),
          ticketRatio: String(data.profile?.critical_ticket_ratio ?? 0),
          revAtRisk: String(data.profile?.revenue_at_risk ?? 0),
        })
        setFetchState('fetched')
      })
      .catch(() => {
        setCustomerProfile({
          customer_id: customerId,
          plan_type: planType,
          actual_status: 1,
        })
        setFormData({
          paymentDelay: '1',
          lastLogin: '30',
          dunning: '5',
          nps: '3',
          ticketRatio: '0.33',
          revAtRisk: '$ 112.58',
        })
        setFetchState('fetched')
      })
  }

  const handlePredict = () => {
    if (fetchState !== 'fetched') return
    setPredictState('predicting')
    apiPost('/api/predict/churn', {
      customer_id: customerId,
      plan_type: customerProfile?.plan_type || planType,
      model_choice: modelChoice,
      overrides: {
        payment_delay_days: Number(formData.paymentDelay || 0),
        days_since_login: Number(formData.lastLogin || 0),
        avg_nps_score: Number(formData.nps || 0),
        dunning_event_count: Number(formData.dunning || 0),
        critical_ticket_ratio: Number(formData.ticketRatio || 0),
        revenue_at_risk: Number(String(formData.revAtRisk).replace(/[^0-9.-]/g, '')) || 0,
      },
    })
      .then((data) => {
        setPredictionResult(data)
        setPredictState('predicted')
      })
      .catch(() => {
        setPredictionResult({
          probability: 0.825,
          risk_level: 'HIGH',
          actual_status: 1,
          evaluation: 'FALSE_NEGATIVE',
        })
        setPredictState('predicted')
      })
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
              <BarChart2 size={24} className="text-white drop-shadow-sm" />
              <h2 className="text-base font-black tracking-wide">{info.title}</h2>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-lg transition-colors"><X size={20} /></button>
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

      <div className="flex items-center gap-3 mb-4">
        <div className="p-1.5 bg-white border border-slate-200 text-slate-500 rounded-md shadow-sm"><Target size={18} /></div>
        <h1 className="text-xl font-black text-slate-800 tracking-tight">Customer Churn Prediction & Analysis</h1>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-100">
          <div className="flex items-center gap-4">
            <span className="text-[11px] font-black text-slate-800 uppercase tracking-wider">AUTO-FETCH CUSTOMER DATA</span>
            <select
              className="border border-slate-200 rounded-lg px-3 py-1.5 text-[11px] font-bold text-slate-700 bg-white"
              value={planType}
              onChange={(e) => setPlanType(e.target.value)}
            >
              <option>Starter</option>
              <option>Professional</option>
              <option>Enterprise</option>
            </select>
            <div className="relative w-40">
              <select 
                className="w-full appearance-none border-b border-slate-200 pb-1 pt-1 text-sm font-bold text-slate-700 focus:outline-none focus:border-indigo-500 transition-colors bg-transparent cursor-pointer"
                value={customerId} onChange={(e) => setCustomerId(e.target.value)}
              >
                <option value="" disabled>Input ID...</option>
                {customerOptions.map((customer) => (
                  <option key={customer.customer_id} value={customer.customer_id}>
                    {customer.customer_id}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-0 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            </div>
          </div>
          <div className="flex items-center gap-4">
            {fetchState === 'fetched' && customerProfile && (
              <div className="flex items-center gap-2 bg-slate-50 px-4 py-1.5 rounded-full border border-slate-100 animate-in fade-in">
                <span className="text-[13px] font-bold text-slate-700">{customerProfile.customer_id} | {customerProfile.plan_type} | </span>
                <span className={`text-white text-[10px] font-black px-2 py-0.5 rounded shadow-sm ${customerProfile.actual_status ? 'bg-rose-400' : 'bg-emerald-500'}`}>{customerProfile.actual_status ? 'CHURNED' : 'NOT CHURNED'}</span>
              </div>
            )}
            <button onClick={handleFetch} disabled={!customerId || fetchState === 'fetching'} className="bg-indigo-500 hover:bg-indigo-600 disabled:bg-slate-300 text-white text-xs font-bold px-6 py-2 rounded-lg shadow-sm transition-all">
              {fetchState === 'fetching' ? 'FETCHING...' : 'FETCH DATA'}
            </button>
          </div>
        </div>

        <div className="bg-slate-100/50 p-5 flex flex-col items-center">
          <div className="flex w-full gap-3 justify-between mb-6">
            {[
              { label: 'Payment Delay Days', val: formData.paymentDelay },
              { label: 'Last Login 90 Days Ago', val: formData.lastLogin },
              { label: 'Dunning Event Count', val: formData.dunning },
              { label: 'Avg. NPS Score', val: formData.nps },
              { label: 'Critical Ticket Ratio', val: formData.ticketRatio },
              { label: 'Revenue at Risk', val: formData.revAtRisk }
            ].map((field, i) => (
              <div key={i} className="flex-1 bg-white border border-slate-200 rounded-lg p-2.5 shadow-sm">
                <p className="text-[9px] font-bold text-slate-500 mb-1 leading-tight h-6">{field.label}</p>
                <div className="flex justify-between items-center border-b border-slate-100 pb-1">
                  <span className="text-sm font-black text-slate-700">{field.val || '-'}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="w-full bg-white rounded-xl border border-slate-200 p-4 mb-4">
            <p className="text-[11px] font-black text-slate-800 uppercase tracking-wider mb-3">Model Selection</p>
            <div className="flex flex-wrap gap-4 text-sm font-semibold text-slate-700">
              {['XGBoost Only', 'CatBoost Only', 'Ensemble (Recommended)'].map((choice) => (
                <label key={choice} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="modelChoice"
                    value={choice}
                    checked={modelChoice === choice}
                    onChange={(e) => setModelChoice(e.target.value)}
                  />
                  {choice}
                </label>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={handlePredict} disabled={fetchState !== 'fetched' || predictState === 'predicting'} className="bg-indigo-500 hover:bg-indigo-600 disabled:bg-slate-300 text-white text-sm font-bold px-16 py-2.5 rounded-xl shadow-lg shadow-indigo-500/30 transition-all flex items-center gap-2">
              {predictState === 'predicting' ? <Activity size={16} className="animate-spin" /> : null}
              RUN PREDICTION
            </button>
          </div>
        </div>
      </div>

      {predictState === 'predicted' && predictionResult && (
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in zoom-in-95 duration-500">
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="bg-slate-50 border-b border-slate-100 p-3"><h3 className="text-[13px] font-black text-slate-800 text-center tracking-wider">PREDICTION RESPONSE</h3></div>
          <div className="p-4 space-y-4 flex-1 flex flex-col overflow-y-auto">
            <div className="border border-slate-200 rounded-xl p-3 flex gap-3 relative overflow-hidden bg-slate-50/50">
              <div className="absolute top-0 left-0 bottom-0 w-1 bg-rose-400"></div>
              <div className="flex-1 space-y-3">
                <p className="text-[10px] font-bold text-slate-600 mb-0.5">RESULT & VALUE</p>
                <div className="flex items-center gap-2"><span className="text-[9px] font-bold text-slate-500 uppercase">Probability</span><span className="bg-rose-400 text-white text-[11px] font-black px-2 py-0.5 rounded shadow-sm">{(predictionResult.probability * 100).toFixed(1)}%</span></div>
                <div className="flex items-center gap-2 mt-1"><span className="text-[9px] font-bold text-slate-500 uppercase">Status</span><span className="bg-rose-400 text-white text-[10px] font-black px-2 py-0.5 rounded shadow-sm">{predictionResult.risk_level} - RISK</span></div>
                <div className="text-[10px] font-semibold text-slate-600">Actual: {predictionResult.actual_status ? 'Churned' : 'Not Churned'}</div>
                <div className="text-[10px] font-semibold text-slate-600">Evaluation: {predictionResult.evaluation}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="bg-slate-50 border-b border-slate-100 p-3"><h3 className="text-[13px] font-black text-slate-800 text-center tracking-wider">GLOBAL SHAP CUSTOMER</h3></div>
          <div className="p-4 grid grid-cols-2 gap-4 flex-1">
            <div className="border border-slate-200 rounded-xl p-4 flex flex-col">
              <h4 className="text-[12px] font-black text-slate-800 mb-4">Global Churn Drivers</h4>
              <div className="space-y-3 flex-1 flex flex-col justify-center">
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 cursor-pointer group" onClick={() => setActiveModal('paymentDelay')}>
                  <span className="group-hover:text-indigo-600 transition-colors">Payment Delay</span>
                  <div className="w-32 h-4 bg-rose-400 flex items-center justify-end pr-2 text-white text-[9px] rounded-sm group-hover:bg-rose-500 shadow-sm transition-all">45%</div>
                </div>
              </div>
            </div>
            <div className="border border-slate-200 rounded-xl p-4 row-span-2 flex flex-col items-center justify-center relative">
              <h4 className="text-[12px] font-black text-slate-800 absolute top-4 left-4">Support Impact on Churn</h4>
              <div className="w-40 h-40 relative mt-6 cursor-pointer group" onClick={() => setActiveModal('technicalIssues')}>
                <svg viewBox="0 0 36 36" className="w-full h-full drop-shadow-md group-hover:scale-105 transition-transform duration-300">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#34d399" strokeWidth="4" strokeDasharray="15, 100" />
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#fbbf24" strokeWidth="4" strokeDasharray="25, 100" strokeDashoffset="-15" />
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#fb7185" strokeWidth="4" strokeDasharray="60, 100" strokeDashoffset="-40" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none"><span className="text-2xl font-black text-slate-800">100%</span></div>
                <div className="absolute right-5 top-3 text-[10px] font-bold text-slate-700 pointer-events-none drop-shadow-sm">15%</div>
              </div>
            </div>
            <div className="border border-slate-200 rounded-xl p-4 flex flex-col relative pb-8">
              <h4 className="text-[12px] font-black text-slate-800 mb-4">At -Risk MRR by Segment</h4>
              <div className="space-y-4 flex-1 flex flex-col justify-center pr-6">
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 cursor-pointer group" onClick={() => setActiveModal('enterpriseMrr')}>
                  <span className="w-20 group-hover:text-indigo-600 transition-colors">Enterprise</span>
                  <div className="w-32 h-4 bg-rose-400 flex items-center justify-end pr-2 text-white text-[9px] rounded-sm group-hover:bg-rose-500 shadow-sm transition-all">$12.5k</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  )
}
