import React, { useState, useEffect } from 'react';
import { Search, Sparkles, Quote, Database, TrendingUp, BrainCircuit, MessageCircle, Info, MessageSquare, Download } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function SentimentView() {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [manualText, setManualText] = useState('');
  const [manualResult, setManualResult] = useState(null);
  const [manualLoading, setManualLoading] = useState(false);

  useEffect(() => {
    // Mengecek apakah ada data yang tersimpan di memori browser (Local Storage)
    const cachedData = localStorage.getItem('lapisai_sentiment_data');
    if (cachedData) {
      setAnalysisData(JSON.parse(cachedData));
      setLoading(false); // Langsung tampilkan tanpa loading ulang
    } else {
      fetchData(); // Jika kosong, baru fetch dari backend
    }
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/sentiment/analysis');
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Gagal mengambil data dari backend Python.');
      }
      
      const data = await res.json();
      setAnalysisData(data);
      // Simpan hasil sukses ke dalam memori browser agar bertahan saat pindah halaman
      localStorage.setItem('lapisai_sentiment_data', JSON.stringify(data));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    window.open('/api/sentiment/export', '_blank');
  };

  const handleManualTest = async () => {
    if (!manualText.trim()) return;
    setManualLoading(true);
    setManualResult(null);
    try {
      const res = await fetch('/api/sentiment/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: manualText }),
      });
      if (!res.ok) throw new Error('Gagal menguji sentimen');
      const data = await res.json();
      setManualResult(data);
    } catch (err) {
      console.error(err);
      alert('Error saat menguji sentimen manual. Cek koneksi backend.');
    } finally {
      setManualLoading(false);
    }
  };

  const renderMarkdown = (text) => {
    if (!text) return { __html: "" };
    let html = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-slate-800">$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');
    return { __html: html };
  };

  const emotionTranslation = {
    'Excitement': { name: 'Senang', color: 'bg-emerald-500' },
    'Annoyance': { name: 'Marah', color: 'bg-rose-500' },
    'Sadness': { name: 'Sedih', color: 'bg-blue-500' },
    'Neutral': { name: 'Netral', color: 'bg-slate-400' }
  };

  // Safe percentage calculation math (Mencegah error 684%)
  const total = analysisData?.total_feedback || 1;
  const neuCount = analysisData?.sentiment_distribution?.neutral ?? 0;
  const negCount = analysisData?.sentiment_distribution?.negative ?? 0;
  const posCount = analysisData?.sentiment_distribution?.positive ?? 0;

  const neuPct = Math.round((neuCount / total) * 100);
  const negPct = Math.round((negCount / total) * 100);
  const posPct = Math.round((posCount / total) * 100);

  // Custom Hover Tooltip untuk Grafik Trend Recharts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-slate-200 shadow-xl rounded-xl text-xs z-50">
          <p className="font-bold text-slate-700 mb-2 border-b border-slate-100 pb-1">Periode: {label}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></div>
              <span className="text-slate-600 font-medium">{entry.name}:</span>
              <span className="font-bold text-slate-800">{entry.value} Pesan</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20 relative">
      
      {/* HEADER */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-1.5 bg-white border border-slate-200 text-slate-500 rounded-md shadow-sm">
          <MessageSquare size={18} />
        </div>
        <h1 className="text-xl font-black text-slate-800 tracking-tight">Feedback & Sentiment Intelligence</h1>
      </div>

      {/* YOUTUBE TRIGGER & EXPORT */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Search size={18} className="text-indigo-500" />
          <h2 className="text-[14px] font-black text-slate-800 tracking-wider uppercase">Live YouTube Scraper (Target: 1500 Komentar)</h2>
        </div>
        <p className="text-sm text-slate-500 mb-4">Sistem akan melakukan <strong>scraping</strong> pada komentar terbaru dari video <strong>"Laptop murah bagus justru dari Apple - Macbook Neo" (GadgetIn)</strong>, menganalisis dengan IndoBERT, dan mengekspor hasilnya ke format CSV di backend.</p>
        
        <div className="flex flex-col md:flex-row gap-4">
          <button 
            onClick={() => {
              localStorage.removeItem('lapisai_sentiment_data'); // Hapus cache lama
              fetchData(); // Paksa fetch data baru
            }}
            disabled={loading}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-xl transition-colors whitespace-nowrap disabled:opacity-70 flex items-center justify-center gap-2"
          >
            {loading ? "Scraping & Memproses 1500 Data (Bisa memakan waktu 1-3 Menit)..." : "🚀 Mulai Scrape & Analisis 2000 Komentar"}
          </button>

          {!loading && analysisData && (
             <button 
               onClick={handleExport}
               className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-xl transition-colors whitespace-nowrap flex items-center justify-center gap-2"
             >
               <Download size={18} /> Export CSV Hasil Analisis
             </button>
          )}
        </div>
      </div>

      {/* ERROR HANDLER */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-6 py-4 rounded-xl flex items-start gap-3 mb-6">
          <Info size={20} className="shrink-0 mt-0.5" />
          <div>
            <h3 className="font-bold">Gagal Menganalisis Sentimen</h3>
            <p className="text-sm opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* LOADING STATE */}
      {loading && !analysisData && (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <h2 className="text-xl font-bold text-slate-700">Menganalisis dengan IndoBERT...</h2>
          <p className="text-slate-500 mt-2">Memproses ribuan baris teks mungkin memakan waktu 1-3 menit.</p>
        </div>
      )}

      {/* MAIN CONTENT RENDERING */}
      {(!loading || analysisData) && analysisData && (
        <div className="space-y-6">
          
          {/* SECTION 1: AI SUMMARY & QUOTES */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4 pb-4 border-b border-slate-100">
              <Sparkles size={18} className="text-indigo-500" />
              <h2 className="text-[14px] font-black text-slate-800 tracking-wider uppercase">Local Executive Summary</h2>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <div 
                  className="text-sm text-slate-600 leading-relaxed font-medium whitespace-pre-wrap"
                  dangerouslySetInnerHTML={renderMarkdown(analysisData.executive_summary)}
                />
              </div>
              
              <div className="space-y-3">
                <h3 className="text-[11px] font-bold text-slate-400 uppercase mb-2">Raw Voice Quotes</h3>
                {analysisData.raw_feedback && analysisData.raw_feedback.slice(0, 3).map((item, idx) => {
                  const sentimentColor = item.sentiment === 'Positive' ? 'emerald' : item.sentiment === 'Negative' ? 'rose' : 'slate';
                  const colors = {
                    emerald: { bg: 'bg-emerald-50', border: 'border-emerald-100', ring: 'bg-emerald-400', text: 'text-emerald-600' },
                    rose: { bg: 'bg-rose-50', border: 'border-rose-100', ring: 'bg-rose-400', text: 'text-rose-600' },
                    slate: { bg: 'bg-slate-50', border: 'border-slate-200', ring: 'bg-slate-400', text: 'text-slate-500' },
                  }[sentimentColor];

                  return (
                    <div key={idx} className={`${colors.bg} ${colors.border} rounded-xl p-3 flex gap-3 relative overflow-hidden border`}>
                      <div className={`absolute left-0 top-0 bottom-0 w-1 ${colors.ring}`}></div>
                      <Quote size={14} className={`${colors.ring} shrink-0 mt-0.5`} />
                      <div>
                        <p className="text-[12px] font-medium text-slate-700">"{item.message}"</p>
                        <span className={`text-[9px] font-bold ${colors.text} mt-1 block`}>
                          {item.sentiment === 'Neutral' ? 'Netral' : item.sentiment} • {emotionTranslation[item.emotion]?.name || item.emotion} • {item.author}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-center">
              <h2 className="text-[13px] font-black text-slate-800 tracking-wider uppercase mb-1">Emotion Distribution Analysis</h2>
              <p className="text-[10px] text-slate-500 mb-6">Kategorisasi emosi dominan dari audiens (Top 3)</p>
              
              <div className="space-y-5">
                {analysisData.emotion_distribution && [...analysisData.emotion_distribution].sort((a,b) => b.value - a.value).slice(0, 3).map((item, idx) => {
                  const info = emotionTranslation[item.label] || emotionTranslation['Neutral'];
                  const percentage = analysisData.total_feedback > 0 ? Math.round((item.value / analysisData.total_feedback) * 100) : 0;
                  
                  return (
                    <div key={idx}>
                      <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${info.color}`}></div>
                          <span className="text-sm font-bold text-slate-700">{info.name}</span>
                        </div>
                        <span className={`text-sm font-bold ${info.color.replace('bg-', 'text-')}`}>{percentage}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-3">
                        <div className={`${info.color} h-3 rounded-full transition-all duration-1000`} style={{ width: `${percentage}%` }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-center items-center text-center">
              <h2 className="text-[13px] font-black text-slate-800 tracking-wider uppercase mb-1">Total Feedback Analyzed</h2>
              <p className="text-[10px] text-slate-500 mb-4">Volume komentar yang berhasil disedot & diproses NLP</p>
              <div className="text-6xl font-black text-slate-800 mb-6 tracking-tight">{analysisData.total_feedback}</div>
              
              <div className="w-full max-w-md">
                <div className="w-full h-4 bg-slate-100 rounded-full flex overflow-hidden mb-4 shadow-inner">
                  <div className="h-full bg-slate-400" style={{ width: `${neuPct}%` }}></div>
                  <div className="h-full bg-rose-500" style={{ width: `${negPct}%` }}></div>
                  <div className="h-full bg-emerald-500" style={{ width: `${posPct}%` }}></div>
                </div>
                <div className="flex justify-between items-center px-2">
                  <div className="text-center"><span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Netral</span><span className="text-[14px] font-black text-slate-700">{neuPct}%</span></div>
                  <div className="text-center"><span className="text-[10px] font-bold text-rose-400 uppercase block mb-1">Negative</span><span className="text-[14px] font-black text-rose-600">{negPct}%</span></div>
                  <div className="text-center"><span className="text-[10px] font-bold text-emerald-400 uppercase block mb-1">Positive</span><span className="text-[14px] font-black text-emerald-600">{posPct}%</span></div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[350px]">
              <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
                <div><h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">Sentiment & Keyword Analysis</h2><p className="text-[10px] text-slate-500 mt-1">Frekuensi kata terbanyak (Emoji dihapus otomatis)</p></div><Database size={16} className="text-slate-400" />
              </div>
              <div className="flex-1 overflow-y-auto">
                <table className="w-full text-left text-[12px]">
                  <thead className="bg-white border-b border-slate-100 text-slate-400 font-bold uppercase tracking-wider text-[10px] sticky top-0"><tr><th className="px-5 py-3">Kata (Keyword)</th><th className="px-5 py-3 text-center">Frekuensi</th><th className="px-5 py-3 text-center">Jenis Sentimen</th></tr></thead>
                  <tbody>
                    {analysisData.keywords && analysisData.keywords.map((row, i) => {
                      let badgeColor = 'bg-slate-100 text-slate-600 border-slate-200';
                      if (row.type === 'Positive') badgeColor = 'bg-emerald-50 text-emerald-600 border-emerald-100';
                      if (row.type === 'Negative') badgeColor = 'bg-rose-50 text-rose-600 border-rose-100';
                      return (
                        <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                          <td className="px-5 py-3 font-bold text-slate-700 capitalize">{row.word}</td>
                          <td className="px-5 py-3 font-black text-slate-800 text-center">{row.freq}</td>
                          <td className="px-5 py-3 text-center"><span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border shadow-sm ${badgeColor}`}>{row.type === 'Neutral' ? 'Netral' : row.type}</span></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col h-[350px]">
              <div className="flex justify-between items-start mb-4">
                <div><h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">Sentiment Trend & Drift</h2><p className="text-[10px] text-slate-500 mt-1">Distribusi respons audiens</p></div><TrendingUp size={16} className="text-slate-400" />
              </div>
              <div className="flex-1 w-full min-h-[250px] relative px-2 pb-6">
                {analysisData.trend_data && analysisData.trend_data.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={analysisData.trend_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <XAxis dataKey="time" hide={true} />
                        <YAxis hide={true} domain={['dataMin - 5', 'dataMax + 5']} />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4' }} />
                        <Line type="basis" name="Netral" dataKey="Neutral" stroke="#94a3b8" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#94a3b8', stroke: '#fff', strokeWidth: 2 }} />
                        <Line type="basis" name="Positif" dataKey="Positive" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#10b981', stroke: '#fff', strokeWidth: 2 }} />
                        <Line type="basis" name="Negatif" dataKey="Negative" stroke="#f43f5e" strokeWidth={3} strokeDasharray="6 6" dot={false} activeDot={{ r: 6, fill: '#f43f5e', stroke: '#fff', strokeWidth: 2 }} />
                      </LineChart>
                    </ResponsiveContainer>
                    <div className="absolute w-full flex justify-between bottom-0 left-0 px-4 text-[10px] font-bold text-slate-400">
                      <span>Awal</span><span>Mid</span><span>Akhir</span>
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm">Belum ada data trend yang memadai.</div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-sm font-black text-slate-800 mb-4 flex items-center gap-2"><BrainCircuit size={16} className="text-indigo-600" /> Uji Sentimen Manual</h3>
            <div className="flex gap-4">
              <textarea className="w-full h-24 p-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none" placeholder="Ketik kalimat apapun di sini, AI akan membedah sentimennya..." value={manualText} onChange={(e) => setManualText(e.target.value)} />
              <button onClick={handleManualTest} disabled={manualLoading || !manualText} className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50 flex items-center justify-center min-w-[120px]">
                {manualLoading ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div> : 'Analisis Teks'}
              </button>
            </div>
            {manualResult && (
              <div className={`mt-4 p-4 rounded-xl flex items-center gap-3 font-bold text-sm border ${manualResult.sentiment === 'Positive' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : manualResult.sentiment === 'Negative' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                <div className="text-2xl">{manualResult.sentiment === 'Positive' ? '✅' : manualResult.sentiment === 'Negative' ? '🚨' : 'ℹ️'}</div>
                <div>
                  <div>Sentimen: <span className="uppercase tracking-widest">{manualResult.sentiment === 'Neutral' ? 'Netral' : manualResult.sentiment}</span></div>
                  <div className="text-xs opacity-75 mt-1 font-medium">Emosi Terdeteksi: {emotionTranslation[manualResult.emotion]?.name || manualResult.emotion}</div>
                </div>
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col">
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-2xl">
              <div className="flex items-center gap-2"><MessageCircle size={16} className="text-slate-600" /><h2 className="text-[13px] font-black text-slate-800 uppercase tracking-wider">RAW CUSTOMER FEEDBACK (LIVE NLP)</h2></div>
            </div>
            <div className="overflow-x-auto max-h-[500px]">
              <table className="w-full text-left text-[12px]">
                <thead className="bg-white border-b border-slate-100 text-slate-400 font-bold uppercase tracking-wider text-[10px] sticky top-0">
                  <tr><th className="px-5 py-4 whitespace-nowrap">Time</th><th className="px-5 py-4 whitespace-nowrap">Author</th><th className="px-5 py-4 w-1/2">Message</th><th className="px-5 py-4 whitespace-nowrap text-center">Sentiment</th><th className="px-5 py-4 whitespace-nowrap text-center">Detected Emotion</th></tr>
                </thead>
                <tbody>
                  {analysisData.raw_feedback && analysisData.raw_feedback.map((row, i) => {
                    let badgeColor = 'bg-slate-100 text-slate-600 border-slate-200';
                    if (row.sentiment === 'Positive') badgeColor = 'bg-emerald-50 text-emerald-600 border-emerald-100';
                    if (row.sentiment === 'Negative') badgeColor = 'bg-rose-50 text-rose-600 border-rose-100';
                    
                    const emotionInfo = emotionTranslation[row.emotion] || { name: row.emotion, color: 'bg-slate-100' };

                    return (
                      <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                        <td className="px-5 py-4 font-bold text-slate-500 whitespace-nowrap">{new Date(row.time).toLocaleTimeString()}</td>
                        <td className="px-5 py-4 font-bold text-indigo-600 whitespace-nowrap truncate max-w-[120px]">{row.author}</td>
                        <td className="px-5 py-4 font-medium text-slate-700 leading-relaxed pr-8">{row.message}</td>
                        <td className="px-5 py-4 text-center whitespace-nowrap">
                          <span className={`px-3 py-1 rounded-md text-[10px] font-bold border shadow-sm ${badgeColor}`}>
                            {row.sentiment === 'Neutral' ? 'Netral' : row.sentiment}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-center whitespace-nowrap">
                          <span className={`text-[11px] font-bold px-2.5 py-1 rounded border ${emotionInfo.color.replace('bg-', 'bg-opacity-20 text-').replace('400', '700').replace('500', '700')} border-opacity-30`}>
                            {emotionInfo.name}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}