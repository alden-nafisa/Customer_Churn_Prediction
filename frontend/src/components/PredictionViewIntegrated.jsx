import React, { useEffect, useState } from 'react'
import { Target, ChevronDown, Minus, Plus, Activity, AlertTriangle } from 'lucide-react'
import { apiGet, apiPost } from '../lib/api.js'

const PLAN_OPTIONS = ['Enterprise', 'Professional', 'Starter']
const MODEL_OPTIONS = ['XGBoost', 'CatBoost', 'Ensemble']

const DEFAULT_FORM_DATA = {
  paymentDelay: '',
  featureAdoption: '',
  supportTickets: '',
  lastLogin: '',
  annualValue: '',
  healthScore: '',
  npsScore: '',
  usageHours: '',
  threshold: '0.50',
}

const FORM_FIELDS = [
  { key: 'paymentDelay', label: 'Payment Delay Days', step: 1 },
  { key: 'featureAdoption', label: 'Feature Adoption %', step: 5 },
  { key: 'supportTickets', label: 'Support Tickets (90d)', step: 1 },
  { key: 'lastLogin', label: 'Days Since Last Login', step: 1 },
  { key: 'annualValue', label: 'Annual Value ($)', step: 500 },
  { key: 'healthScore', label: 'Payment Health Score', step: 5 },
  { key: 'npsScore', label: 'Avg NPS Score', step: 0.5 },
  { key: 'usageHours', label: 'Monthly Usage Hours', step: 10 },
  { key: 'threshold', label: 'Threshold', step: 0.05 },
]

function toNumber(value, fallback = 0) {
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function formatNumber(value, digits = 1) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : '-'
}

function formatPercent(value, digits = 1) {
  return `${formatNumber(Number(value) * 100, digits)}%`
}

function formatCurrency(value) {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return '-'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(parsed)
}

function getModelRequestChoice(model) {
  if (model === 'XGBoost') return 'XGBoost Only'
  if (model === 'CatBoost') return 'CatBoost Only'
  return 'Ensemble (Recommended)'
}

function MetricCard({ label, value, tone = 'slate', subtitle }) {
  const tones = {
    slate: 'bg-slate-50 border-slate-200 text-slate-800',
    rose: 'bg-rose-50 border-rose-100 text-rose-700',
    amber: 'bg-amber-50 border-amber-100 text-amber-700',
    emerald: 'bg-emerald-50 border-emerald-100 text-emerald-700',
    indigo: 'bg-white border-indigo-100 text-indigo-700',
  }

  return (
    <div className={`rounded-xl border p-3 text-center shadow-sm ${tones[tone] || tones.slate}`}>
      <p className="text-[9px] font-bold uppercase mb-1 opacity-80">{label}</p>
      <h3 className="text-lg font-black leading-none">{value}</h3>
      {subtitle ? <p className="mt-1 text-[10px] font-medium opacity-80">{subtitle}</p> : null}
    </div>
  )
}

function VerticalBars({ title, subtitle, data, barColor = 'bg-indigo-500', valueFormatter = (value) => value, valueLabel = 'Count' }) {
  const maxValue = Math.max(...data.map((item) => item.value), 1)

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 h-[280px] flex flex-col">
      <h3 className="text-[12px] font-black text-slate-800 tracking-wider mb-1">{title}</h3>
      {subtitle ? <p className="text-[9px] text-slate-400 mb-4">{subtitle}</p> : null}
      <div className="flex-1 flex items-end justify-around gap-3 pb-2">
        {data.map((item) => {
          const height = Math.max(10, (item.value / maxValue) * 180)
          return (
            <div key={item.label} className="flex flex-col items-center gap-2 w-full min-w-0">
              <span className="text-[10px] font-bold text-slate-500">{valueFormatter(item.value)}</span>
              <div
                className={`w-full rounded-t-md transition-all hover:opacity-80 ${item.color || barColor}`}
                style={{ height: `${height}px` }}
              />
              <span className="text-[9px] font-bold text-slate-600 uppercase text-center leading-tight">{item.label}</span>
            </div>
          )
        })}
      </div>
      <div className="mt-2 text-[9px] text-slate-400 uppercase tracking-wider">{valueLabel}</div>
    </div>
  )
}

function HorizontalBars({ title, subtitle, data }) {
  const maxValue = Math.max(...data.map((item) => item.value), 1)

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <h3 className="text-[12px] font-black text-slate-800 tracking-wider mb-2 uppercase">{title}</h3>
      {subtitle ? <p className="text-[9px] text-slate-400 mb-5">{subtitle}</p> : null}
      <div className="space-y-4">
        {data.map((item) => {
          const width = Math.max(4, (item.value / maxValue) * 100)
          return (
            <div key={item.label} className="flex items-center gap-4">
              <span className="text-[10px] font-bold text-slate-600 w-48 text-right truncate">{item.label}</span>
              <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${item.color || 'bg-indigo-500'}`} style={{ width: `${width}%` }} />
              </div>
              <span className="text-[10px] font-black text-indigo-700 w-12 text-right">{formatNumber(item.value, 2)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ConfusionMatrix({ matrix }) {
  if (!matrix) return null

  const [tn, fp] = matrix[0] || [0, 0]
  const [fn, tp] = matrix[1] || [0, 0]
  const maxValue = Math.max(tn, fp, fn, tp, 1)

  const cell = (value) => ({
    background: `rgba(30, 64, 175, ${Math.max(0.08, value / maxValue)})`,
    color: value / maxValue > 0.55 ? '#ffffff' : '#0f172a',
  })

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <h3 className="text-[12px] font-black text-slate-800 tracking-wider mb-6 uppercase">Confusion Matrix</h3>
      <div className="grid grid-cols-[72px_repeat(2,1fr)] gap-1 max-w-[430px] mx-auto text-[11px] font-bold">
        <div />
        <div className="text-center text-slate-500 pb-2">Predicted Retained</div>
        <div className="text-center text-slate-500 pb-2">Predicted Churned</div>
        <div className="flex items-center justify-end pr-2 text-slate-500 rotate-180 [writing-mode:vertical-rl]">Actual Retained</div>
        <div className="h-24 flex items-center justify-center rounded-md" style={cell(tn)}>{tn}</div>
        <div className="h-24 flex items-center justify-center rounded-md" style={cell(fp)}>{fp}</div>
        <div className="flex items-center justify-end pr-2 text-slate-500 rotate-180 [writing-mode:vertical-rl]">Actual Churned</div>
        <div className="h-24 flex items-center justify-center rounded-md" style={cell(fn)}>{fn}</div>
        <div className="h-24 flex items-center justify-center rounded-md" style={cell(tp)}>{tp}</div>
      </div>
    </div>
  )
}

export default function PredictionViewIntegrated() {
  const [predictionTab, setPredictionTab] = useState('individual')
  const [planTypeA, setPlanTypeA] = useState('Enterprise')
  const [customerIdA, setCustomerIdA] = useState('')
  const [selectedModel, setSelectedModel] = useState('Ensemble')
  const [fetchState, setFetchState] = useState('idle')
  const [predictState, setPredictState] = useState('idle')
  const [formData, setFormData] = useState(DEFAULT_FORM_DATA)
  const [planTypeB, setPlanTypeB] = useState('Enterprise')
  const [customerOptions, setCustomerOptions] = useState([])
  const [individualSummary, setIndividualSummary] = useState(null)
  const [customerProfile, setCustomerProfile] = useState(null)
  const [predictionResult, setPredictionResult] = useState(null)
  const [analysisData, setAnalysisData] = useState(null)
  const [individualLoading, setIndividualLoading] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadIndividualPlan() {
      setIndividualLoading(true)
      try {
        const data = await apiGet(`/api/churn/analysis?plan_type=${encodeURIComponent(planTypeA)}`)
        if (cancelled) return

        const nextCustomers = data.customers || []
        setCustomerOptions(nextCustomers)
        setIndividualSummary(data.plan_summary || null)
        setError('')

        setCustomerIdA((current) => {
          if (current && nextCustomers.includes(current)) return current
          return nextCustomers[0] || ''
        })
      } catch (exception) {
        if (!cancelled) setError(exception instanceof Error ? exception.message : 'Failed to load individual analysis data.')
      } finally {
        if (!cancelled) setIndividualLoading(false)
      }
    }

    loadIndividualPlan()
    return () => {
      cancelled = true
    }
  }, [planTypeA])

  useEffect(() => {
    let cancelled = false

    async function loadPlanAnalysis() {
      setAnalysisLoading(true)
      try {
        const data = await apiGet(`/api/churn/analysis?plan_type=${encodeURIComponent(planTypeB)}`)
        if (!cancelled) {
          setAnalysisData(data)
          setError('')
        }
      } catch (exception) {
        if (!cancelled) setError(exception instanceof Error ? exception.message : 'Failed to load plan analysis data.')
      } finally {
        if (!cancelled) setAnalysisLoading(false)
      }
    }

    loadPlanAnalysis()
    return () => {
      cancelled = true
    }
  }, [planTypeB])

  const handleIncrement = (key, step) => {
    setFormData((previous) => ({
      ...previous,
      [key]: (toNumber(previous[key], 0) + step).toFixed(2),
    }))
  }

  const handleDecrement = (key, step) => {
    setFormData((previous) => ({
      ...previous,
      [key]: Math.max(0, toNumber(previous[key], 0) - step).toFixed(2),
    }))
  }

  const handleInputChange = (key, value) => setFormData((previous) => ({ ...previous, [key]: value }))

  const handleFetch = async () => {
    if (!customerIdA) return
    setFetchState('fetching')
    setPredictState('idle')
    setPredictionResult(null)

    try {
      const data = await apiGet(`/api/customer/${encodeURIComponent(customerIdA)}/features?plan_type=${encodeURIComponent(planTypeA)}`)
      const profile = data.profile || {}
      setCustomerProfile(data)
      setFormData((previous) => ({
        paymentDelay: String(profile.payment_delay_days_mean ?? 0),
        featureAdoption: String(profile.feature_adoption_pct_mean ?? 0),
        supportTickets: String(profile.total_tickets ?? 0),
        lastLogin: String(profile.days_since_last_login ?? 0),
        annualValue: String(profile.annual_value ?? 0),
        healthScore: String(profile.payment_health_score ?? 0),
        npsScore: String(profile.avg_nps_score ?? 0),
        usageHours: String(profile.avg_monthly_usage_hours ?? 0),
        threshold: previous.threshold || '0.50',
      }))
      setError('')
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : 'Failed to fetch customer data.')
    } finally {
      setFetchState('fetched')
    }
  }

  const handlePredict = async () => {
    if (fetchState !== 'fetched' || !customerIdA) return
    setPredictState('predicting')

    const overrides = {
      payment_delay_days: toNumber(formData.paymentDelay, 0),
      feature_adoption_pct: toNumber(formData.featureAdoption, 0),
      total_tickets: toNumber(formData.supportTickets, 0),
      days_since_login: toNumber(formData.lastLogin, 0),
      annual_value: toNumber(formData.annualValue, 0),
      payment_health_score: toNumber(formData.healthScore, 0),
      avg_nps_score: toNumber(formData.npsScore, 0),
      avg_monthly_usage_hours: toNumber(formData.usageHours, 0),
    }

    try {
      const data = await apiPost('/api/predict/churn', {
        customer_id: customerIdA,
        plan_type: planTypeA,
        model_choice: getModelRequestChoice(selectedModel),
        threshold: toNumber(formData.threshold, 0.5),
        overrides,
      })

      setPredictionResult(data)
      setError('')
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : 'Prediction failed.')
    } finally {
      setPredictState('predicted')
    }
  }

  const summary = individualSummary || {}
  const overall = analysisData?.overall || {}
  const evaluation = analysisData?.evaluation || {}
  const scorecard = evaluation.scorecard || {}
  const confusionMatrix = evaluation.confusion_matrix?.matrix || null
  const modelComparison = evaluation.model_comparison || {}

  const riskColors = {
    Low: 'bg-emerald-400',
    Medium: 'bg-amber-300',
    High: 'bg-orange-400',
    'Very High': 'bg-rose-500',
  }

  const probabilityBars = (overall.probability_distribution?.counts || []).map((value, index) => ({
    label: overall.probability_distribution?.bins?.[index] || `Bin ${index + 1}`,
    value,
    color: 'bg-sky-500',
  }))

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20 relative">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-white border border-slate-200 text-slate-500 rounded-md shadow-sm"><Target size={18} /></div>
          <h1 className="text-xl font-black text-slate-800 tracking-tight">Customer Churn Analysis & Prediction</h1>
        </div>
        <div className="flex bg-slate-200/60 p-1.5 rounded-xl w-fit border border-slate-200 shadow-inner overflow-x-auto">
          {[
            { id: 'individual', label: 'Individual Analysis' },
            { id: 'overall', label: 'Overall Analysis' },
            { id: 'evaluation', label: 'Model Evaluation' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setPredictionTab(tab.id)}
              className={`px-5 py-2 rounded-lg text-xs font-black tracking-wide transition-all whitespace-nowrap ${predictionTab === tab.id ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-200/50'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 font-medium">
          {error}
        </div>
      ) : null}

      {predictionTab === 'individual' && (
        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex justify-between items-end border-b border-slate-200 pb-2">
            <h2 className="text-lg font-black text-slate-800">Individual Customer Risk Assessment</h2>
            {individualLoading ? <span className="text-[10px] font-bold text-slate-500 uppercase">Loading plan data...</span> : null}
          </div>

          <details className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-sm text-slate-700">
            <summary className="font-bold text-slate-800 cursor-pointer">ℹ️ Cara membaca - Individual</summary>
            <div className="mt-2 space-y-2">
              <ul className="list-disc pl-5">
                <li><strong>Plan Type</strong>: Pilih paket (Enterprise / Professional / Starter) untuk memfilter customers.</li>
                <li><strong>Customer ID</strong>: Pilih ID lalu klik <em>FETCH DATA</em> untuk mengisi form feature secara otomatis.</li>
                <li><strong>Summary Metrics</strong>: Menampilkan total customer, jumlah actual churn, jumlah high-risk (&gt;50%), dan akurasi model per metode.</li>
                <li><strong>Feature Input Form</strong>: Ubah value untuk skenario "what-if" (Payment Delay, Feature Adoption, Support Tickets, dll.).</li>
                <li><strong>Model Selection</strong>: Pilih XGBoost / CatBoost / Ensemble sebelum <em>RUN PREDICTION</em>.</li>
                <li><strong>Interpretasi Hasil</strong>: Warna &amp; label risk menunjukkan level risiko; bagian "Model Performance Rating" jelaskan apakah prediksi benar/false positive/negative.</li>
                <li><strong>Rekomendasi</strong>: Sistem akan memberikan action singkat untuk langkah retensi berdasarkan hasil prediksi.</li>
              </ul>
            </div>
          </details>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row gap-6 justify-between items-center">
            <div className="flex items-center gap-4 w-full md:w-auto">
              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-slate-500 uppercase mb-1">Plan Type</label>
                <div className="relative w-40">
                  <select
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm font-bold text-slate-700 focus:outline-none focus:border-indigo-500 bg-slate-50"
                    value={planTypeA}
                    onChange={(event) => {
                      setPlanTypeA(event.target.value)
                      setCustomerProfile(null)
                      setPredictionResult(null)
                      setFetchState('idle')
                      setPredictState('idle')
                    }}
                  >
                    {PLAN_OPTIONS.map((plan) => <option key={plan} value={plan}>{plan}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-slate-500 uppercase mb-1">Customer ID</label>
                <div className="relative w-40">
                  <select
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm font-bold text-slate-700 focus:outline-none focus:border-indigo-500 bg-slate-50"
                    value={customerIdA}
                    onChange={(event) => setCustomerIdA(event.target.value)}
                  >
                    <option value="" disabled>{customerOptions.length ? 'Select ID...' : 'No customers'}</option>
                    {customerOptions.map((customerId) => (
                      <option key={customerId} value={customerId}>{customerId}</option>
                    ))}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>
              </div>
            </div>

            <button
              onClick={handleFetch}
              disabled={!customerIdA || fetchState === 'fetching'}
              className="w-full md:w-auto bg-indigo-500 hover:bg-indigo-600 disabled:bg-slate-300 text-white text-xs font-bold px-8 py-2.5 rounded-lg shadow-sm transition-all whitespace-nowrap"
            >
              {fetchState === 'fetching' ? 'FETCHING...' : 'FETCH DATA'}
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <MetricCard label="Total Customer" value={summary.total_customers ?? '-'} tone="slate" />
            <MetricCard label="Actual Churned" value={summary.actual_churned ?? '-'} tone="rose" />
            <MetricCard label="High Risk (>50%)" value={summary.high_risk_customers ?? '-'} tone="amber" />
            <div className="bg-white border border-indigo-100 rounded-xl p-3 text-center col-span-3 md:col-span-3 flex justify-around items-center shadow-sm">
              <div>
                <p className="text-[9px] font-bold text-slate-500 uppercase mb-1">XGBoost Acc</p>
                <h3 className="text-sm font-black text-indigo-700">{formatPercent(summary.model_accuracies?.xgboost ?? 0)}</h3>
              </div>
              <div className="w-px h-8 bg-slate-200" />
              <div>
                <p className="text-[9px] font-bold text-slate-500 uppercase mb-1">CatBoost Acc</p>
                <h3 className="text-sm font-black text-indigo-700">{formatPercent(summary.model_accuracies?.catboost ?? 0)}</h3>
              </div>
              <div className="w-px h-8 bg-slate-200" />
              <div>
                <p className="text-[9px] font-bold text-slate-500 uppercase mb-1">Ensemble Acc</p>
                <h3 className="text-sm font-black text-indigo-700">{formatPercent(summary.model_accuracies?.ensemble ?? 0)}</h3>
              </div>
            </div>
          </div>

          {customerProfile ? (
            <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm font-semibold text-blue-800">
              Customer ID: {customerProfile.customer_id} | Plan: {customerProfile.plan_type} | Actual Status: {customerProfile.actual_status_text}
            </div>
          ) : null}

          <details className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-sm text-slate-700">
            <summary className="font-bold text-slate-800 cursor-pointer">ℹ️ Tips singkat</summary>
            <div className="mt-2 space-y-2">
              <p className="text-[12px] font-semibold">Tips:</p>
              <ul className="list-disc pl-5">
                <li>Jika ingin menguji skenario, ubah angka pada form lalu tekan <strong>RUN PREDICTION</strong>.</li>
                <li>Perhatikan threshold pada hasil prediksi — Anda bisa menyesuaikannya saat mengirim request.</li>
                <li>Gunakan rekomendasi yang diberikan untuk membuat tindakan retensi prioritas.</li>
              </ul>
            </div>
          </details>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-100 p-4">
              <h3 className="text-[13px] font-black text-slate-800 tracking-wider">Feature Input Form</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
                {FORM_FIELDS.map((field) => (
                  <div key={field.key} className="flex flex-col">
                    <label className="text-[9px] font-bold text-slate-500 uppercase block mb-1 truncate" title={field.label}>{field.label}</label>
                    <div className="flex items-center border border-slate-200 rounded-lg overflow-hidden bg-slate-50 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all">
                      <button
                        onClick={() => handleDecrement(field.key, field.step)}
                        disabled={fetchState !== 'fetched'}
                        className="px-2 py-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 disabled:opacity-30 transition-colors"
                      >
                        <Minus size={14} />
                      </button>
                      <input
                        type="number"
                        className="w-full text-center py-1.5 text-sm font-bold text-slate-700 bg-transparent focus:outline-none"
                        value={formData[field.key] || ''}
                        onChange={(event) => handleInputChange(field.key, event.target.value)}
                        disabled={fetchState !== 'fetched'}
                        placeholder="-"
                      />
                      <button
                        onClick={() => handleIncrement(field.key, field.step)}
                        disabled={fetchState !== 'fetched'}
                        className="px-2 py-1.5 text-slate-400 hover:text-emerald-500 hover:bg-emerald-50 disabled:opacity-30 transition-colors"
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-col md:flex-row items-center justify-between pt-4 border-t border-slate-100 gap-4">
                <div className="flex items-center gap-4">
                  <span className="text-[11px] font-bold text-slate-600 uppercase">Model Selection:</span>
                  <div className="flex bg-slate-100 rounded-lg p-1">
                    {MODEL_OPTIONS.map((model) => (
                      <button
                        key={model}
                        onClick={() => setSelectedModel(model)}
                        className={`text-[11px] font-bold px-4 py-1.5 rounded-md transition-all ${selectedModel === model ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                      >
                        {model}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handlePredict}
                  disabled={fetchState !== 'fetched' || predictState === 'predicting'}
                  className="bg-indigo-500 hover:bg-indigo-600 disabled:bg-slate-300 text-white text-sm font-bold px-10 py-2.5 rounded-xl shadow-md shadow-indigo-500/20 transition-all flex items-center gap-2"
                >
                  {predictState === 'predicting' ? <Activity size={16} className="animate-spin" /> : null}
                  RUN PREDICTION
                </button>
              </div>
            </div>
          </div>

          {predictionResult ? (
            <div className="bg-gradient-to-r from-rose-50 to-white rounded-2xl border border-rose-100 shadow-sm p-6 animate-in zoom-in-95 duration-500">
              <h3 className="text-[13px] font-black text-slate-800 tracking-wider mb-4 border-b border-rose-100 pb-2">Prediction Result</h3>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="space-y-4">
                  <div>
                    <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Customer Status</p>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className={`text-white text-sm font-black px-3 py-1 rounded shadow-sm tracking-wide ${predictionResult.probability > 0.5 ? 'bg-rose-500' : 'bg-emerald-500'}`}>
                        {predictionResult.risk_level}
                      </span>
                      <span className="text-xl font-black text-rose-600">{formatPercent(predictionResult.probability, 1)} Prob.</span>
                    </div>
                    <p className="mt-2 text-[11px] font-medium text-slate-600">Model: {predictionResult.model} | Threshold: {formatPercent(predictionResult.threshold || 0.5, 0)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Model Performance Rating</p>
                    <div className={`border text-[11px] font-bold p-2 rounded-lg flex gap-2 items-start ${predictionResult.evaluation === 'FALSE_POSITIVE' ? 'bg-amber-50 border-amber-200 text-amber-700' : predictionResult.evaluation === 'FALSE_NEGATIVE' ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-emerald-50 border-emerald-200 text-emerald-700'}`}>
                      <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                      <p>
                        <strong>{predictionResult.evaluation}:</strong> {predictionResult.explanation}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-2 space-y-4">
                  {predictionResult.model_predictions && Object.keys(predictionResult.model_predictions).length > 1 ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {Object.entries(predictionResult.model_predictions).map(([model, value]) => (
                        <MetricCard
                          key={model}
                          label={model}
                          value={formatPercent(value, 1)}
                          tone="indigo"
                          subtitle="Model probability"
                        />
                      ))}
                    </div>
                  ) : null}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Top Risk Factors (SHAP)</p>
                      <ul className="space-y-2 text-[11px] font-medium text-slate-700">
                        {(predictionResult.risk_factors || []).map((factor, index) => (
                          <li key={`${factor.label}-${index}`} className="flex justify-between items-center border-b border-slate-100 pb-1 gap-3">
                            <span>{index + 1}. {factor.label}</span>
                            <span className="text-rose-500 font-bold">{formatNumber(factor.value, 2)}</span>
                          </li>
                        ))}
                      </ul>
                      {!(predictionResult.risk_factors || []).length ? <p className="text-[11px] text-slate-500">No risk factors were returned.</p> : null}
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Recommended Action</p>
                      <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3">
                        <ul className="space-y-2 text-[11px] font-medium text-indigo-800 leading-relaxed list-disc pl-4">
                          {(predictionResult.recommendation_actions || []).map((action, index) => <li key={`${action}-${index}`}>{action}</li>)}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </section>
      )}

      {predictionTab === 'overall' && (
        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex justify-between items-end border-b border-slate-200 pb-2">
            <h2 className="text-lg font-black text-slate-800">Overall Analysis</h2>
            <div className="flex items-center gap-3">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Plan Filter</label>
              <select
                className="border border-slate-200 rounded-lg px-2 py-1 text-xs font-bold text-slate-700 bg-slate-50 cursor-pointer"
                value={planTypeB}
                onChange={(event) => setPlanTypeB(event.target.value)}
              >
                {PLAN_OPTIONS.map((plan) => <option key={plan} value={plan}>{plan}</option>)}
              </select>
            </div>
          </div>

          <details className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-sm text-slate-700">
            <summary className="font-bold text-slate-800 cursor-pointer">ℹ️ Cara membaca - Overall</summary>
            <div className="mt-2 space-y-3">
              <p className="text-sm">Panduan lengkap (untuk pengguna non-teknis):</p>
              <div>
                <p className="font-semibold">1) Ringkasan visual</p>
                <p className="text-[13px]">- <strong>Customer by Risk Level</strong>: Menunjukkan berapa banyak pelanggan yang tergolong Low, Medium, High, atau Very High risk. Gunakan ini untuk melihat seberapa besar proporsi pelanggan yang perlu perhatian.</p>
                <p className="text-[13px]">- <strong>Churn Probability Distribution</strong>: Histogram yang memperlihatkan bagaimana probabilitas churn tersebar. Area di sebelah kanan (nilai probabilitas tinggi) berarti lebih banyak pelanggan yang berpotensi churn.</p>
              </div>

              <div>
                <p className="font-semibold">2) Analisis fitur (apa yang mempengaruhi churn)</p>
                <p className="text-[13px]">- <strong>Feature Dominance</strong> menampilkan fitur-fitur teratas yang paling berkaitan dengan churn (misalnya: jumlah keluhan, keterlambatan pembayaran, penurunan pemakaian). Fitur dengan korelasi tinggi artinya perubahan pada fitur itu seringkali diikuti churn.</p>
                <p className="text-[13px]">- Ini membantu tim non-teknis menentukan prioritas intervensi: misalnya jika "Support Tickets" tinggi, fokuskan pada perbaikan layanan pelanggan.</p>
              </div>

              <div>
                <p className="font-semibold">3) Dampak bisnis</p>
                <p className="text-[13px]">- <strong>Revenue at Risk</strong> memperkirakan nilai pendapatan yang berisiko hilang berdasarkan pelanggan berisiko tinggi. Gunakan ini untuk memprioritaskan tindakan terhadap pelanggan yang bernilai tinggi.</p>
              </div>

              <div>
                <p className="font-semibold">4) Daftar tindakan yang direkomendasikan</p>
                <p className="text-[13px]">- Berdasarkan kombinasi risiko & fitur dominan, sistem memberikan rekomendasi singkat (mis. "Hubungi customer", "Tawarkan diskon trial", "Perbaiki masalah billing"). Gunakan sebagai input ke tim CRM/Retention.</p>
              </div>

              <div>
                <p className="font-semibold">5) Cara menggunakan (langkah praktis)</p>
                <ol className="list-decimal pl-5 text-[13px]">
                  <li>Pilih <strong>Plan Filter</strong> untuk memfokuskan analisis ke segmen yang diinginkan.</li>
                  <li>Perhatikan bagian <strong>Top At-Risk</strong> untuk segera membuat daftar prioritas outreach.</li>
                  <li>Gunakan <strong>Feature Dominance</strong> untuk menentukan jenis intervensi (produk, harga, layanan).</li>
                  <li>Tinjau <strong>Revenue at Risk</strong> untuk memvalidasi prioritas berdasarkan nilai pelanggan.</li>
                </ol>
              </div>

              <div>
                <p className="font-semibold">6) FAQ singkat untuk non-teknis</p>
                <ul className="list-disc pl-5 text-[13px]">
                  <li><strong>Apa arti probabilitas 0.8?</strong> — Artinya model memperkirakan 80% kemungkinan pelanggan tersebut akan churn jika tidak ada tindakan.</li>
                  <li><strong>Apakah ini pasti terjadi?</strong> — Tidak. Ini adalah peringatan probabilistik; gunakan bersama konteks bisnis dan data lain.</li>
                  <li><strong>Kenapa beberapa pelanggan bernilai tinggi tapi risiko rendah?</strong> — Karena model melihat perilaku historis; pelanggan bernilai tinggi mungkin menunjukkan pola yang menurunkan risiko.</li>
                </ul>
              </div>
            </div>
          </details>

          {analysisLoading ? <p className="text-sm font-medium text-slate-500">Loading overall analysis...</p> : null}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <VerticalBars
              title="Customer by Risk Level"
              subtitle="Risk distribution for the selected plan"
              data={(overall.risk_distribution || []).map((item) => ({
                label: item.label,
                value: item.value,
                color: riskColors[item.label],
              }))}
              valueFormatter={(value) => value}
              valueLabel="Low to Very High"
            />

            <VerticalBars
              title="Churn Probability Distribution"
              subtitle="Distribution of ensemble probability across customers"
              data={probabilityBars}
              barColor="bg-sky-500"
              valueFormatter={(value) => value}
              valueLabel="Probability bins (ensemble_proba)"
            />
          </div>

          <HorizontalBars
            title="Top Feature Dominance for Churn"
            subtitle="Absolute correlation with actual churn"
            data={overall.feature_dominance || []}
          />

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-100 p-4">
              <h3 className="text-[13px] font-black text-slate-800 tracking-wider uppercase">Revenue At Risk ({planTypeB})</h3>
            </div>
            <div className="p-5 flex flex-col md:flex-row gap-6">
              <div className="flex flex-col gap-4 min-w-[220px]">
                <MetricCard
                  label="Value at High Risk"
                  value={formatCurrency(overall.revenue_at_risk?.value_at_high_risk ?? 0)}
                  tone="rose"
                />
                <div className="grid grid-cols-2 gap-4">
                  <MetricCard
                    label="% of Total"
                    value={`${formatNumber(overall.revenue_at_risk?.pct_of_total_value ?? 0, 1)}%`}
                    tone="slate"
                  />
                  <MetricCard
                    label="High Risk Cust."
                    value={overall.revenue_at_risk?.high_risk_customers ?? '-'}
                    tone="slate"
                  />
                </div>
              </div>
              <div className="flex-1 overflow-x-auto">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-2">Risk Category</th>
                      <th className="px-4 py-2 text-right">Total Value</th>
                      <th className="px-4 py-2 text-right">Cust. Count</th>
                      <th className="px-4 py-2 text-right">Avg Value/Cust</th>
                    </tr>
                  </thead>
                  <tbody className="font-medium text-slate-700">
                    {(overall.revenue_at_risk?.rows || []).map((row) => (
                      <tr key={row.risk_category} className="border-b border-slate-50">
                        <td className="px-4 py-2"><span className="font-bold">{row.risk_category}</span></td>
                        <td className="px-4 py-2 text-right">{formatCurrency(row.total_value)}</td>
                        <td className="px-4 py-2 text-right">{row.customer_count}</td>
                        <td className="px-4 py-2 text-right">{formatCurrency(row.avg_value_per_customer)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-100 p-4">
              <h3 className="text-[13px] font-black text-slate-800 tracking-wider uppercase">Top Rank At-Risk Customers ({planTypeB})</h3>
            </div>
            <div className="p-5 overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-2">Rank</th>
                    <th className="px-4 py-2">Customer ID</th>
                    <th className="px-4 py-2">Plan</th>
                    <th className="px-4 py-2 text-right">Tenure (mo)</th>
                    <th className="px-4 py-2 text-right">Annual Value</th>
                    <th className="px-4 py-2 text-right">NPS</th>
                    <th className="px-4 py-2 text-right">Risk %</th>
                  </tr>
                </thead>
                <tbody className="font-medium text-slate-700">
                  {(overall.top_risk_customers || []).map((row, index) => (
                    <tr key={row.customer_id || index} className="border-b border-slate-50">
                      <td className="px-4 py-2 font-black text-slate-500">{index + 1}</td>
                      <td className="px-4 py-2 font-bold text-slate-800">{row.customer_id}</td>
                      <td className="px-4 py-2">{row.plan}</td>
                      <td className="px-4 py-2 text-right">{formatNumber(row.tenure_months, 1)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(row.annual_value)}</td>
                      <td className="px-4 py-2 text-right">{formatNumber(row.nps, 1)}</td>
                      <td className="px-4 py-2 text-right font-black text-rose-600">{formatNumber(row.risk_pct, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-100 p-4">
              <h3 className="text-[13px] font-black text-slate-800 tracking-wider uppercase">Top 15 At-Risk Customers</h3>
            </div>
            <div className="p-5 overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-2">Rank</th>
                    <th className="px-4 py-2">Customer ID</th>
                    <th className="px-4 py-2">Plan</th>
                    <th className="px-4 py-2 text-right">Tenure (mo)</th>
                    <th className="px-4 py-2 text-right">Annual Value</th>
                    <th className="px-4 py-2 text-right">NPS</th>
                    <th className="px-4 py-2 text-right">Risk %</th>
                  </tr>
                </thead>
                <tbody className="font-medium text-slate-700">
                  {(overall.top15_customers || []).map((row, index) => (
                    <tr key={row.customer_id || index} className="border-b border-slate-50">
                      <td className="px-4 py-2 font-black text-slate-500">{index + 1}</td>
                      <td className="px-4 py-2 font-bold text-slate-800">{row.customer_id}</td>
                      <td className="px-4 py-2">{row.plan}</td>
                      <td className="px-4 py-2 text-right">{formatNumber(row.tenure_months, 1)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(row.annual_value)}</td>
                      <td className="px-4 py-2 text-right">{formatNumber(row.nps, 1)}</td>
                      <td className="px-4 py-2 text-right font-black text-rose-600">{formatNumber(row.risk_pct, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {predictionTab === 'evaluation' && (
        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex justify-between items-end border-b border-slate-200 pb-2">
            <h2 className="text-lg font-black text-slate-800">Model Evaluation</h2>
            <div className="flex items-center gap-3">
              <label className="text-[10px] font-bold text-slate-500 uppercase">Plan Filter</label>
              <select
                className="border border-slate-200 rounded-lg px-2 py-1 text-xs font-bold text-slate-700 bg-slate-50 cursor-pointer"
                value={planTypeB}
                onChange={(event) => setPlanTypeB(event.target.value)}
              >
                {PLAN_OPTIONS.map((plan) => <option key={plan} value={plan}>{plan}</option>)}
              </select>
            </div>
          </div>

          <details className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-sm text-slate-700">
            <summary className="font-bold text-slate-800 cursor-pointer">ℹ️ Cara membaca - Model Evaluation</summary>
            <div className="mt-2 space-y-3">
              <p className="text-sm">Penjelasan lengkap metrik & interpretasi (untuk pengguna non-teknis):</p>

              <div>
                <p className="font-semibold">1) Metrik utama dan arti praktisnya</p>
                <p className="text-[13px]">- <strong>Accuracy</strong>: Persentase prediksi yang benar secara keseluruhan. Berguna sebagai gambaran umum, tapi bisa menipu jika kelas tidak seimbang.</p>
                <p className="text-[13px]">- <strong>Precision</strong>: Dari semua pelanggan yang diprediksi akan churn, berapa banyak yang benar-benar churn. Nilai tinggi berarti lebih sedikit false alarms (mengurangi biaya outreach yang sia-sia).</p>
                <p className="text-[13px]">- <strong>Recall</strong> (Sensitivity): Dari semua pelanggan yang benar-benar churn, berapa banyak yang berhasil dideteksi. Nilai tinggi berarti kita menangkap lebih banyak kasus churn (lebih sedikit missed churns).</p>
                <p className="text-[13px]">- <strong>F1-Score</strong>: Kombinasi Precision & Recall; cocok ketika Anda ingin keseimbangan antara tidak melewatkan churn dan tidak menghubungi terlalu banyak yang salah.</p>
              </div>

              <div>
                <p className="font-semibold">2) Confusion Matrix — cara baca sederhana</p>
                <p className="text-[13px]">Confusion matrix adalah tabel 2x2:</p>
                <ul className="list-disc pl-5 text-[13px]"><li><strong>True Positive (TP)</strong>: Diprediksi churn & benar churn.</li>
                  <li><strong>False Positive (FP)</strong>: Diprediksi churn tapi sebenarnya tidak churn (biaya outreach sia-sia).</li>
                  <li><strong>False Negative (FN)</strong>: Diprediksi tidak churn tapi ternyata churn (missed opportunity).</li>
                  <li><strong>True Negative (TN)</strong>: Diprediksi tidak churn & benar tidak churn.</li></ul>
                <p className="text-[13px]">Gunakan TP/FN/FP untuk menilai trade-off antara biaya intervensi dan risiko kehilangan pelanggan.</p>
              </div>

              <div>
                <p className="font-semibold">3) Model Comparison — memilih model untuk operasional</p>
                <p className="text-[13px]">- Bandingkan precision & recall antar model. Jika biaya outreach tinggi, pilih model dengan precision lebih tinggi. Jika kehilangan pelanggan lebih mahal, pilih model dengan recall lebih tinggi.</p>
                <p className="text-[13px]">- Periksa juga konsistensi: model dengan skor stabil antar segmen lebih dapat diandalkan.</p>
              </div>

              <div>
                <p className="font-semibold">4) Rekomendasi praktis</p>
                <ul className="list-disc pl-5 text-[13px]"><li>Mulai dengan threshold konservatif (mis. 0.6) untuk mengurangi false positives, lalu evaluasi biaya/benefit.</li>
                  <li>Jalankan pilot outreach pada top 5–10% pelanggan berisiko tinggi untuk divalidasi secara manual.</li>
                  <li>Gunakan metrik setelah intervensi (mis. churn rate menurun) untuk men-tune threshold dan model.</li></ul>
              </div>

              <div>
                <p className="font-semibold">5) Pertanyaan umum</p>
                <ul className="list-disc pl-5 text-[13px]"><li><strong>Bisakah model salah?</strong> — Ya. Model membantu prioritas, bukan pengganti keputusan manusia.</li>
                  <li><strong>Kapan training perlu diulang?</strong> — Saat perubahan besar pada produk/penetapan harga atau jika performa model menurun.</li>
                </ul>
              </div>
            </div>
          </details>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="Accuracy" value={formatPercent(scorecard.accuracy || 0)} tone="emerald" subtitle="How many predictions are correct" />
            <MetricCard label="Recall (Sensitivity)" value={formatPercent(scorecard.recall || 0)} tone="emerald" subtitle="Catch rate of actual churners" />
            <MetricCard label="Precision" value={formatPercent(scorecard.precision || 0)} tone="emerald" subtitle="Accuracy of positive predictions" />
            <MetricCard label="F1-Score" value={formatPercent(scorecard.f1 || 0)} tone="emerald" subtitle="Balance of precision and recall" />
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-[12px] font-black text-slate-800 tracking-wider mb-6 uppercase">Prediction Accuracy Breakdown</h3>
            <ConfusionMatrix matrix={confusionMatrix} />
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-[12px] font-black text-slate-800 tracking-wider mb-6 uppercase">Model Comparison (XGBoost vs CatBoost vs Ensemble)</h3>
            <VerticalBars
              title="High-Risk Customers Detected (Threshold >50%)"
              subtitle="Number of customers flagged by each model"
              data={(modelComparison.high_risk_detected || []).map((item) => ({
                label: item.model,
                value: item.value,
                color: item.model === 'XGBoost' ? 'bg-rose-400' : item.model === 'CatBoost' ? 'bg-teal-400' : 'bg-cyan-500',
              }))}
              valueFormatter={(value) => value}
              valueLabel="High-risk predictions"
            />

            <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h4 className="text-[12px] font-black text-slate-800 uppercase tracking-wider mb-3">What This Means For You</h4>
                  <ul className="space-y-2 text-sm text-slate-700 font-medium list-disc pl-5">
                    <li>Accuracy: percentage of predictions that are correct.</li>
                    <li>Recall: how well the model catches actual churners.</li>
                    <li>Precision: how often churn alerts are truly churn.</li>
                    <li>F1-Score: balanced view of precision and recall.</li>
                  </ul>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <h4 className="text-[12px] font-black text-slate-800 uppercase tracking-wider mb-3">Good Model Indicators</h4>
                  <ul className="space-y-2 text-sm text-slate-700 font-medium list-disc pl-5">
                    <li>High recall for catching most churners.</li>
                    <li>Balanced precision to reduce false alarms.</li>
                    <li>High F1-Score for overall dependable performance.</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}