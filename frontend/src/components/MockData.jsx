import {
	Cpu,
	RefreshCw,
	Zap,
	AlertTriangle,
	CheckCircle2,
} from 'lucide-react'

export const summaryStats = [
	{ id: 'risk', label: 'Customers at Risk', value: '1,569', chartData: [10, 25, 15, 30, 45, 35, 20], color: 'indigo' },
	{ id: 'revenue', label: 'Revenue at Risk', value: '$45,200', chartData: [20, 15, 30, 25, 40, 30, 20], color: 'indigo' },
	{ id: 'nps', label: 'Average NPS', value: '7.4', chartData: [5, 6, 5, 8, 7, 9, 7], highlight: 5, color: 'indigo' }
]

export const customerChurnData = [
	{ id: 'C-0267', type: 'Starter/Monthly', score: '0,567', status: 'Not Churned' },
	{ id: 'C-0091', type: 'Starter/Monthly', score: '0,867', status: 'Churned' },
	{ id: 'C-0176', type: 'Starter/Monthly', score: '0,389', status: 'Churned' },
	{ id: 'C-0056', type: 'Starter/Monthly', score: '0,567', status: 'Churned' },
	{ id: 'C-0002', type: 'Starter/Monthly', score: '0,375', status: 'Not Churned' },
]

export const feedbackData = [
	{ id: 'C-0267', text: 'UI responsif, prediksi sangat akurat.', nps: 9, sentiment: 'Positive' },
	{ id: 'C-0091', text: 'Performa lambat saat muat dataset.', nps: 5, sentiment: 'Negative' },
	{ id: 'C-0176', text: 'Analisis sentimen NLP luar biasa!', nps: 8, sentiment: 'Positive' },
	{ id: 'C-0056', text: 'Bagus, butuh fitur ekspor PDF.', nps: 10, sentiment: 'Positive' },
	{ id: 'C-0002', text: 'Dokumentasi API masih kurang lengkap.', nps: 6, sentiment: 'Netral' },
]

export const dashboardHighRiskAlerts = [
	{ time: '05:48AM', id: 'C-0992', type: 'Enterprise', desc: 'Kendala probabilitas churn naik ke 85%. Segera tawarkan diskon.', riskLevel: 'high' },
	{ time: '10:28AM', id: 'C-0112', type: 'Professional', desc: 'Sistem lambat saat memuat dataset. Pantau penggunaan API-nya.', riskLevel: 'warning' },
	{ time: '07:58PM', id: 'C-0091', type: 'Starter', desc: 'Aktivitas normal dan feedback positif. Terpantau sangat aman.', riskLevel: 'safe' },
]

export const predictionLogs = [
	{ time: '10m ago', title: 'Model Retrained', desc: 'XGBoost churn model accuracy updated to 92.4%.', icon: <Cpu size={14} className="text-indigo-500" /> },
	{ time: '30m ago', title: 'Data Sync', desc: 'Synced 2,480 rows from CRM & Billing Database.', icon: <RefreshCw size={14} className="text-blue-500" /> },
	{ time: '1h ago', title: 'Auto Action', desc: 'Dispatched 15 retention emails to high-risk users.', icon: <Zap size={14} className="text-emerald-500" /> },
	{ time: '2h ago', title: 'Data Anomaly', desc: 'Spike in payment delays detected in Enterprise tier.', icon: <AlertTriangle size={14} className="text-amber-500" /> },
	{ time: '3h ago', title: 'Pipeline Complete', desc: 'Daily churn batch prediction successfully finished.', icon: <CheckCircle2 size={14} className="text-emerald-500" /> },
]

export const predictionHighRiskAlerts = [
	{ time: '05:48AM', id: 'C-0992', type: 'Enterprise', desc: 'Kendala probabilitas churn naik ke 85%. Segera tawarkan diskon.', riskLevel: 'high' },
	{ time: '10:28AM', id: 'C-0112', type: 'Professional', desc: 'Memiliki 3 tiket komplain teknis yang belum terselesaikan.', riskLevel: 'warning' },
]

export const customersByPlan = {
	Enterprise: ['C-0992', 'C-0544', 'C-1021'],
	Professional: ['C-0112', 'C-0201', 'C-0773'],
	Starter: ['C-0091', 'C-0812', 'C-0056']
}

export const featureDominance = [
	{ label: 'nps_trend', value: 85 }, { label: 'is_on_time_sum', value: 72 }, { label: 'feature_adoption_pct_mean', value: 65 },
	{ label: 'churned', value: 50 }, { label: 'ensemble_prediction', value: 45 }, { label: 'cat_proba', value: 38 },
	{ label: 'xgb_proba', value: 30 }, { label: 'ensemble_proba', value: 25 }, { label: 'actual', value: 15 }
]

export const top15Customers = [
	{ id: 'C-0992', plan: 'Enterprise', tenure: 24, annual: '$50,000', nps: 4, risk: 85 },
	{ id: 'C-0112', plan: 'Professional', tenure: 12, annual: '$12,000', nps: 5, risk: 78 },
	{ id: 'C-0544', plan: 'Enterprise', tenure: 36, annual: '$45,000', nps: 6, risk: 72 },
	{ id: 'C-0201', plan: 'Professional', tenure: 8, annual: '$10,500', nps: 3, risk: 68 },
	{ id: 'C-0091', plan: 'Starter', tenure: 3, annual: '$2,400', nps: 2, risk: 65 },
]

export const sentimentLogs = [
	{ time: 'Just now', title: 'Model Retrained', desc: 'IndoBERT model accuracy increased to 94.2%.', icon: <Cpu size={14} className="text-indigo-500" /> },
	{ time: '2m ago', title: 'Data Sync', desc: 'Fetched 5,000 new rows from YouTube API.', icon: <RefreshCw size={14} className="text-blue-500" /> },
	{ time: '5m ago', title: 'Auto Action', desc: 'Filtered 250 spam and repetitive emote messages.', icon: <Zap size={14} className="text-amber-500" /> },
	{ time: '12m ago', title: 'Data Anomaly', desc: 'Sudden spike in "Marah" emotion detected.', icon: <AlertTriangle size={14} className="text-rose-500" /> },
]

export const sentimentHighRiskAlerts = [
	{ time: '14:44PM', id: '@dellyapingg', type: 'Negative Spike', desc: 'Sentimen negatif massal terkait "Opening kebesaran".', riskLevel: 'high' },
	{ time: '14:49PM', id: '@sabrnarsy', type: 'Annoyance', desc: 'Audiens jenuh dengan spam nama "Ilham".', riskLevel: 'warning' },
]

export const sentimentKeywords = [
	{ word: 'Ilham', freq: 412, type: 'Netral' },
	{ word: 'Opening', freq: 289, type: 'Negative' },
	{ word: 'Lesss Goooo', freq: 205, type: 'Positive' },
	{ word: 'Nunggu', freq: 154, type: 'Negative' },
	{ word: 'Bang', freq: 142, type: 'Netral' },
]

export const youtubeChatData = [
	{ time: '14:44:14', author: '@m0ndazee2', message: 'L thumbnail', sentiment: 'Netral', emotion: 'Biasa' },
	{ time: '14:44:14', author: '@ranzehandsome', message: 'gcc makanan gw hampir habis', sentiment: 'Netral', emotion: 'Biasa' },
	{ time: '14:44:15', author: '@sia2008', message: 'damn', sentiment: 'Negative', emotion: 'Marah' },
	{ time: '14:44:16', author: '@hostfytalh', message: 'lesss goooo', sentiment: 'Positive', emotion: 'Senang' },
	{ time: '14:44:16', author: '@dellyapingg', message: 'BANG KATA ILHAM KENAPA ITU OPENING NYA terlalu di besar besar kan', sentiment: 'Negative', emotion: 'Marah' },
	{ time: '14:44:17', author: '@putra1-s5u', message: 'l nunggu', sentiment: 'Negative', emotion: 'Sedih' },
]

export const systemLogs = predictionLogs
