import React from 'react';
import { Cpu, RefreshCw, Zap, AlertTriangle, CheckCircle2 } from 'lucide-react';

// Data cadangan sementara saat Backend belum merespons
export const summaryStats = [
  { id: 'risk', label: 'Customers at Risk', value: '0', chartData: [], color: 'indigo' },
  { id: 'revenue', label: 'Revenue at Risk', value: '$0', chartData: [], color: 'indigo' },
  { id: 'nps', label: 'Average NPS', value: '0.0', chartData: [], highlight: 5, color: 'indigo' }
];

export const customerChurnData = [];
export const feedbackData = [];

export const dashboardHighRiskAlerts = [
  { time: '05:48AM', id: 'C-0992', type: 'Enterprise', desc: 'Kendala probabilitas churn naik ke 85%. Segera tawarkan diskon.', riskLevel: 'high' },
  { time: '10:28AM', id: 'C-0112', type: 'Professional', desc: 'Sistem lambat saat memuat dataset. Pantau penggunaan API-nya.', riskLevel: 'warning' },
  { time: '07:58PM', id: 'C-0091', type: 'Starter', desc: 'Aktivitas normal dan feedback positif. Terpantau sangat aman.', riskLevel: 'safe' },
];

export const predictionLogs = [
  { time: '10m ago', title: 'Model Retrained', desc: 'XGBoost churn model accuracy updated to 92.4%.', icon: <Cpu size={14} className="text-indigo-500" /> },
  { time: '30m ago', title: 'Data Sync', desc: 'Synced 2,480 rows from CRM & Billing Database.', icon: <RefreshCw size={14} className="text-blue-500" /> },
];

export const predictionHighRiskAlerts = [
  { time: '05:48AM', id: 'C-0992', type: 'Enterprise', desc: 'Kendala probabilitas churn naik ke 85%. Segera tawarkan diskon.', riskLevel: 'high' },
  { time: '10:28AM', id: 'C-0112', type: 'Professional', desc: 'Memiliki 3 tiket komplain teknis yang belum terselesaikan.', riskLevel: 'warning' },
];

export const sentimentLogs = [
  { time: 'Just now', title: 'Model Retrained', desc: 'IndoBERT model accuracy increased to 94.2%.', icon: <Cpu size={14} className="text-indigo-500" /> },
  { time: '2m ago', title: 'Data Sync', desc: 'Fetched 5,000 new rows from YouTube API.', icon: <RefreshCw size={14} className="text-blue-500" /> },
];

export const sentimentHighRiskAlerts = [
  { time: '14:44PM', id: '@dellyapingg', type: 'Negative Spike', desc: 'Sentimen negatif massal terkait "Opening kebesaran".', riskLevel: 'high' },
  { time: '14:49PM', id: '@sabrnarsy', type: 'Annoyance', desc: 'Audiens jenuh dengan spam nama "Ilham".', riskLevel: 'warning' },
];

export const customersByPlan = {
  Enterprise: ['C-0992', 'C-0544', 'C-1021'],
  Professional: ['C-0112', 'C-0201', 'C-0773'],
  Starter: ['C-0091', 'C-0812', 'C-0056']
};

export const featureDominance = [];
export const top15Customers = [];