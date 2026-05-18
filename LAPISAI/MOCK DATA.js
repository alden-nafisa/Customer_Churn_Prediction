import React, { useState } from 'react';
import { 
  BarChart3, 
  Settings, 
  LayoutDashboard, 
  Bell, 
  Menu, 
  Activity, 
  AlertTriangle, 
  MessageSquare,
  HelpCircle,
  MoreHorizontal,
  Mail,
  Lock,
  Twitter,
  Facebook,
  Database,
  Search,
  CheckCircle2,
  Zap,
  BrainCircuit,
  MessageCircle,
  PieChart,
  Sparkles,
  LogOut,
  Users,
  Target,
  ChevronDown,
  RefreshCw,
  Cpu,
  BarChart2,
  X
} from 'lucide-react';

// ==========================================
// MOCK DATA: DASHBOARD & SIDEBAR
// ==========================================
const summaryStats = [
  { id: 'risk', label: 'Customers at Risk', value: '1,569', chartData: [10, 25, 15, 30, 45, 35, 20], color: 'indigo' },
  { id: 'revenue', label: 'Revenue at Risk', value: '$45,200', chartData: [20, 15, 30, 25, 40, 30, 20], color: 'indigo' },
  { id: 'nps', label: 'Average NPS', value: '7.4', chartData: [5, 6, 5, 8, 7, 9, 7], highlight: 5, color: 'indigo' } 
];

const customerChurnData = [
  { id: 'C-0267', type: 'Starter/Monthly', score: '0,567', status: 'Not Churned', image: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=40&h=40&q=80' },
  { id: 'C-0091', type: 'Starter/Monthly', score: '0,867', status: 'Churned', image: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=40&h=40&q=80' },
  { id: 'C-0176', type: 'Starter/Monthly', score: '0,389', status: 'Churned', image: 'https://images.unsplash.com/photo-1481481600673-c6cb160e2f32?auto=format&fit=crop&w=40&h=40&q=80' },
  { id: 'C-0056', type: 'Starter/Monthly', score: '0,567', status: 'Churned', image: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=40&h=40&q=80' },
  { id: 'C-0002', type: 'Starter/Monthly', score: '0,375', status: 'Not Churned', image: 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=40&h=40&q=80' },
];

const feedbackData = [
  { id: 'C-0267', text: 'UI responsif, prediksi sangat akurat.', nps: 9, sentiment: 'Positive' },
  { id: 'C-0091', text: 'Performa lambat saat muat dataset.', nps: 5, sentiment: 'Negative' },
  { id: 'C-0176', text: 'Analisis sentimen NLP luar biasa!', nps: 8, sentiment: 'Positive' },
  { id: 'C-0056', text: 'Bagus, butuh fitur ekspor PDF.', nps: 10, sentiment: 'Positive' },
  { id: 'C-0002', text: 'Dokumentasi API masih kurang lengkap.', nps: 6, sentiment: 'Netral' },
];

const highRiskAlerts = [
  { time: '05:48AM', id: 'C-0992', type: 'Enterprise', desc: 'Probabilitas churn naik ke 85%. Segera tawarkan diskon.' },
  { time: '10:28AM', id: 'C-0112', type: 'Professional', desc: 'Mengirimkan 3 tiket komplain hari ini' },
  { time: '07:58PM', id: 'C-0091', type: 'Starter', desc: 'Probabilitas churn naik ke 85%. Segera dihubungi.' },
];

const systemLogs = [
  { time: 'Just now', title: 'Stream Connected', desc: 'YouTube Live API successfully connected.', icon: <Activity size={14} className="text-emerald-500" /> },
  { time: '2 min ago', title: 'NLP Engine Active', desc: 'Indonesian BERT model loaded for sentiment analysis.', icon: <BrainCircuit size={14} className="text-indigo-500" /> },
  { time: '15 min ago', title: 'Model Retrained', desc: 'XGBoost model accuracy increased to 92.4%', icon: <Activity size={14} className="text-blue-500" /> },
  { time: '1 hrs ago', title: 'Data Sync', desc: '500 new rows synced from Supabase.', icon: <Database size={14} className="text-indigo-500" /> },
];

// ==========================================
// MOCK DATA: PREDICTION POPUPS
// ==========================================
const popupDataStore = {
  paymentDelay: {
    title: "SEGMENT: PAYMENT DELAY DRIVERS (45%)", subtitle: "Ditemukan 124 Pelanggan berisiko karena telat bayar.",
    data: [
      { id: 'C-0201', plan: 'Professional', value: '45 Days', color: 'bg-rose-400 text-white' },
      { id: 'C-0544', plan: 'Enterprise', value: '32 Days', color: 'bg-rose-400 text-white' },
      { id: 'C-0773', plan: 'Professional', value: '28 Days', color: 'bg-indigo-500 text-white' },
      { id: 'C-0812', plan: 'Starter', value: '20 Days', color: 'bg-amber-300 text-slate-800' }
    ],
    col3Label: "Delay Days", actionLabel: "Load Data"
  },
  forecast: {
    title: "FORECAST: PREDICTED CHURN (NOV 2026)", subtitle: "Ditemukan 85 Pelanggan dengan probabilitas churn > 70% bulan depan.",
    data: [
      { id: 'C-0201', plan: 'Professional', value: '98.5%', loss: '$2.500/mo', color: 'bg-rose-400 text-white' },
      { id: 'C-0544', plan: 'Enterprise', value: '91.2%', loss: '$1.200/mo', color: 'bg-rose-400 text-white' },
      { id: 'C-0773', plan: 'Professional', value: '85.0%', loss: '$3.500/mo', color: 'bg-amber-300 text-slate-800' }
    ],
    col3Label: "Churn Prob.", actionLabel: "Load Data", hasCol4: true, col4Label: "Est. Loss"
  },
  enterpriseMrr: {
    title: "SEGMENT: ENTERPRISE AT-RISK MRR ($12.5k)", subtitle: "Ditemukan 12 Pelanggan Enterprise berisiko tinggi bulan ini.",
    data: [
      { id: 'C-0201', plan: 'Enterprise', value: 'Kritis', loss: '$5.000/mo', color: 'bg-rose-400 text-white' },
      { id: 'C-0544', plan: 'Enterprise', value: 'Kritis', loss: '$3.200/mo', color: 'bg-rose-400 text-white' },
      { id: 'C-0773', plan: 'Enterprise', value: 'Waspada', loss: '$2.100/mo', color: 'bg-amber-300 text-slate-800' }
    ],
    col3Label: "Health", actionLabel: "Load Data", hasCol4: true, col4Label: "MRR at Risk"
  },
  technicalIssues: {
    title: "SUPPORT: UNRESOLVED TECHNICAL ISSUES (60%)", subtitle: "Ditemukan 45 Tiket Teknis Terbuka dari pelanggan berisiko tinggi.",
    data: [
      { id: 'C-0201', plan: 'T-8812', value: 'Critical', loss: '14 Days', color: 'bg-rose-400 text-white' },
      { id: 'C-0544', plan: 'T-8904', value: 'Critical', loss: '9 Days', color: 'bg-rose-400 text-white' },
      { id: 'C-0773', plan: 'T-9011', value: 'High', loss: '7 Days', color: 'bg-amber-300 text-slate-800' }
    ],
    col2Label: "Ticket ID", col3Label: "Priority", actionLabel: "View Tkt", hasCol4: true, col4Label: "Days Unresolved"
  }
};

// ==========================================
// MOCK DATA: YOUTUBE CHAT (NLP)
// ==========================================
const youtubeChatData = [
  { time: '14:44:14', elapsed: '0:00:00', author: '@m0ndazee2', message: 'L thumbnail', sentiment: 'Netral', emotion: 'Neutral', conf: '88%' },
  { time: '14:44:14', elapsed: '0:00:00', author: '@ranzehandsomebgt', message: 'gcc makanan gw hampir habis', sentiment: 'Netral', emotion: 'Anticipation', conf: '76%' },
  { time: '14:44:15', elapsed: '0:00:01', author: '@sia2008', message: 'damn', sentiment: 'Negative', emotion: 'Surprise', conf: '82%' },
  { time: '14:44:16', elapsed: '0:00:02', author: '@hostfytalhcpunk', message: 'lesss goooo', sentiment: 'Positive', emotion: 'Excitement', conf: '95%' },
  { time: '14:44:16', elapsed: '0:00:02', author: '@dellyapingg-m8o', message: 'BANG KATA ILHAM KENAPA ITU OPENING NYA terlalu di besar besar kan', sentiment: 'Negative', emotion: 'Annoyance', conf: '91%' },
  { time: '14:44:17', elapsed: '0:00:03', author: '@putra1-s5u', message: 'l nunggu', sentiment: 'Netral', emotion: 'Boredom', conf: '80%' },
  { time: '14:49:10', elapsed: '0:04:56', author: '@calvin-p8r5b', message: 'akuuu', sentiment: 'Netral', emotion: 'Neutral', conf: '90%' },
  { time: '14:49:10', elapsed: '0:04:56', author: '@MuhammadHabibie-j1p', message: 'goib', sentiment: 'Netral', emotion: 'Confusion', conf: '78%' },
  { time: '14:49:10', elapsed: '0:04:56', author: '@gamau-n9i', message: 'BANG', sentiment: 'Netral', emotion: 'Neutral', conf: '99%' },
  { time: '14:49:10', elapsed: '0:04:56', author: '@sabrnarsy', message: 'yaelah ilham ilhamm', sentiment: 'Negative', emotion: 'Annoyance', conf: '85%' },
  { time: '14:49:11', elapsed: '0:04:57', author: '@LaFamme234', message: 'L ilham', sentiment: 'Negative', emotion: 'Dislike', conf: '89%' },
];

// ==========================================
// KOMPONEN HELPER
// ==========================================
const Sparkline = ({ data, highlightIndex, colorClass }) => {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const height = 40;
  const width = 120;
  const padding = 5;
  
  const scaleY = (val) => height - padding - ((val - min) / (max - min)) * (height - 2 * padding);
  const scaleX = (idx) => padding + (idx / (data.length - 1)) * (width - 2 * padding);
  const points = data.map((val, idx) => `${scaleX(idx)},${scaleY(val)}`).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`text-${colorClass}-500`} />
      {highlightIndex !== undefined && data[highlightIndex] !== undefined && (
        <circle cx={scaleX(highlightIndex)} cy={scaleY(data[highlightIndex])} r="4" fill="#f43f5e" className="shadow-sm" />
      )}
    </svg>
  );
};
