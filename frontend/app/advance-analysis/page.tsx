import React from "react";

export default function AdvanceAnalysisPage() {
  return (
    <main className="min-h-screen p-8 bg-slate-50">
      {/* Banner / Title */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">Advance Analysis</p>
          <h1 className="text-2xl font-bold text-slate-900">Churn insights & model explainability</h1>
          <p className="text-sm text-slate-500">Analisis lebih dalam untuk menentukan faktor churn, estimasi risiko, dan rekomendasi retensi.</p>
        </div>
        <div className="flex gap-3">
          <IconButton icon="🔍" />
          <IconButton icon="🔁" />
        </div>
      </div>

      {/* SECTION 1: Filters + KPI */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-slate-400">Analysis Input</p>
              <h2 className="font-semibold text-slate-800">Filter customer behavior</h2>
            </div>
            <div className="flex gap-3">
              <button className="px-4 py-2 rounded-full bg-indigo-100 text-indigo-700">XGBoost</button>
              <button className="px-4 py-2 rounded-full bg-white border">CatBoost</button>
            </div>
          </div>

          <form className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-slate-500">Plan Type</label>
              <select className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none">
                <option>Choose The Plan</option>
                <option>All</option>
                <option>Starter</option>
                <option>Professional</option>
                <option>Enterprise</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-500">Contract Type</label>
              <select className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none">
                <option>Choose The Contract</option>
                <option>All</option>
                <option>Monthly</option>
                <option>Annual</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-500">Threshold</label>
              <input type="number" step="0.01" defaultValue={0.5} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
            </div>
            <div />

            <div>
              <label className="text-sm text-slate-500">Last Login Days Ago</label>
              <input type="number" defaultValue={0} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
            </div>
            <div>
              <label className="text-sm text-slate-500">Support Tickets Last 90d</label>
              <input type="number" defaultValue={2} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
            </div>
            <div>
              <label className="text-sm text-slate-500">Tenure Months</label>
              <input type="number" defaultValue={24} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
            </div>
            <div>
              <label className="text-sm text-slate-500">Feature Adoption PCT</label>
              <input type="number" defaultValue={53.2} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
            </div>

            <div>
              <label className="text-sm text-slate-500">Monthly Revenue</label>
              <input type="number" defaultValue={181.75} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
            </div>
            <div>
              <label className="text-sm text-slate-500">Payment Delay Count</label>
              <input type="number" defaultValue={0} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
            </div>
          </form>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <KPICard title="Total Evaluated" value="3,000" sub="Customers in view" />
            <KPICard title="High-Risk Cust" value="1,569" sub="Predicted Churn" color="text-red-500" />
            <KPICard title="Model Accuracy" value="77.07%" sub="XGBoost Performance" />
            <KPICard title="Avg. Probability" value="50.80%" sub="Across all segments" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-slate-400">Histogram Probabilities</p>
              <h3 className="font-semibold text-slate-800">Churn distribution</h3>
            </div>
            <div className="flex gap-2">
              <button className="px-3 py-1 rounded-full bg-white border">Day</button>
              <button className="px-3 py-1 rounded-full bg-white border">Week</button>
              <button className="px-3 py-1 rounded-full bg-white border">Month</button>
            </div>
          </div>
          <div className="h-56 bg-slate-50 rounded-lg border border-dashed border-slate-200 flex items-center justify-center text-slate-400">[ Chart placeholder ]</div>

          <div className="mt-6">
            <p className="text-xs text-slate-400">Predicted Revenue Loss</p>
            <h3 className="font-semibold text-slate-800">Risk impact</h3>
            <div className="mt-3 h-40 bg-slate-50 rounded-lg border border-dashed border-slate-200 flex items-center justify-center text-slate-400">[ Chart placeholder ]</div>
          </div>
        </div>
      </section>

      {/* SECTION 2: Global SHAP & Risk Table */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="font-bold text-slate-800 mb-4">Customer Risk & Explanation Table</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-50">
                  <th className="pb-3 font-medium">Customer ID</th>
                  <th className="pb-3 font-medium">Risk Score</th>
                  <th className="pb-3 font-medium">Primary Factor</th>
                  <th className="pb-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                <TableRow id="C-0992" score="85%" factor="Support Tickets > 5" status="High" />
                <TableRow id="C-0112" score="68%" factor="Usage Drop 40%" status="Medium" />
                <TableRow id="C-0267" score="12%" factor="Stable Usage" status="Low" />
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="font-bold text-slate-800 mb-4">Global Feature Importance</h3>
          <div className="space-y-4">
            <SHAPBar label="Monthly Usage" val={85} color="bg-indigo-500" />
            <SHAPBar label="Tenure Months" val={70} color="bg-indigo-400" />
            <SHAPBar label="NPS Score" val={60} color="bg-indigo-300" />
            <SHAPBar label="Support Tickets" val={45} color="bg-red-400" />
          </div>
        </div>
      </section>

      {/* SECTION 3: Local SHAP */}
      <section className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mb-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold">Individual Deep Dive</h2>
            <p className="text-sm text-slate-500">Explaining specific prediction for C-0992</p>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-white/10 rounded-lg">Prev</button>
            <button className="px-4 py-2 bg-indigo-500 text-white rounded-lg">Next</button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-50 p-6 rounded-2xl">
            <h4 className="font-bold text-indigo-700 mb-4">Local SHAP Values (Waterfall)</h4>
            <div className="space-y-3">
              <div className="flex justify-between text-xs"><span>Base Value</span><span>0.51</span></div>
              <SHAPBar label="Tickets (+1.2)" val={80} color="bg-red-500" isDark />
              <SHAPBar label="Tenure (-0.4)" val={30} color="bg-green-500" isDark />
              <div className="flex justify-between font-bold pt-2 border-t border-white/10 text-lg">
                <span>Final Probability</span><span className="text-red-500">0.85</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-bold text-indigo-700 mb-4">Retained Action Suggestions</h4>
            <ul className="space-y-3 text-sm text-slate-700">
              <li className="flex gap-3"><span className="text-green-500">✓</span> Tawarkan diskon loyalitas 15% segera.</li>
              <li className="flex gap-3"><span className="text-green-500">✓</span> Eskalasi tiket dukungan terbuka ke level Senior.</li>
              <li className="flex gap-3"><span className="text-green-500">✓</span> Jadwalkan demo fitur baru yang belum diadopsi.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* SECTION 4: NLP & Sentiment */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="font-bold text-slate-800 mb-4">Top Keywords & Impact</h3>
          <div className="space-y-4">
            <KeywordItem word="Telat" count={157} sentiment="Negative" color="text-red-500" />
            <KeywordItem word="Sangat Cepat" count={120} sentiment="Positive" color="text-green-500" />
            <KeywordItem word="Dokumentasi" count={85} sentiment="Neutral" color="text-amber-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="font-bold text-slate-800 mb-4">Recent Analyzed Feedbacks</h3>
          <FeedbackItem id="C-0992" text="Aplikasi sedikit lambat saat load dataset besar." sentiment="Negative" />
          <FeedbackItem id="C-0112" text="Sangat membantu untuk prediksi churn bulanan kami!" sentiment="Positive" />
        </div>
      </section>
    </main>
  );
}

// --- SUB-COMPONENTS ---

function IconButton({ icon }: any) {
  return (
    <button className="w-10 h-10 bg-white border border-gray-200 rounded-xl flex items-center justify-center shadow-sm hover:bg-slate-50 transition-colors">{icon}</button>
  );
}

function KPICard({ title, value, sub, color = "text-slate-800" }: any) {
  return (
    <div className="bg-white p-4 rounded-xl border border-gray-100">
      <p className="text-xs text-slate-400 uppercase">{title}</p>
      <p className={`text-2xl font-black ${color}`}>{value}</p>
      <p className="text-[11px] text-slate-500">{sub}</p>
    </div>
  );
}

function SHAPBar({ label, val, color, isDark = false }: any) {
  return (
    <div>
      <div className="flex justify-between text-xs font-bold mb-1">
        <span className={isDark ? "text-slate-400" : "text-slate-600"}>{label}</span>
        <span className={isDark ? "text-white" : "text-slate-800"}>{val}%</span>
      </div>
      <div className={`w-full h-2 ${isDark ? "bg-white/10" : "bg-slate-100"} rounded-full overflow-hidden`}>
        <div className={`${color}`} style={{ width: `${val}%`, height: '100%' }} />
      </div>
    </div>
  );
}

function TableRow({ id, score, factor, status }: any) {
  const statusColors: any = { High: "text-red-500", Medium: "text-amber-500", Low: "text-green-500" };
  return (
    <tr className="hover:bg-slate-50 transition-colors">
      <td className="py-3 font-bold text-slate-800">{id}</td>
      <td className={`py-3 font-black ${statusColors[status]}`}>{score}</td>
      <td className="py-3 text-slate-600">{factor}</td>
      <td className="py-3"><button className="text-indigo-500 font-bold hover:underline">Detail</button></td>
    </tr>
  );
}

function KeywordItem({ word, count, sentiment, color }: any) {
  return (
    <div className="flex justify-between items-center p-2 hover:bg-slate-50 rounded-lg">
      <span className="font-bold text-slate-700">{word}</span>
      <div className="flex gap-4 items-center">
        <span className="text-xs text-slate-400">{count} times</span>
        <span className={`text-xs font-black uppercase ${color}`}>{sentiment}</span>
      </div>
    </div>
  );
}

function FeedbackItem({ id, text, sentiment }: any) {
  const color = sentiment === "Positive" ? "bg-green-50 border-green-100" : "bg-red-50 border-red-100";
  return (
    <div className={`p-4 rounded-xl border ${color} mb-3`}>
      <div className="flex justify-between mb-1">
        <span className="text-xs font-black text-slate-800">{id}</span>
        <span className="text-[10px] uppercase font-bold text-slate-400">{sentiment}</span>
      </div>
      <p className="text-sm text-slate-700 italic">"{text}"</p>
    </div>
  );
}
