"use client";

import React, { useState } from "react";

export default function CustomerChurnPrediction() {
  // State untuk menyimpan nilai input
  const [formData, setFormData] = useState({
    planType: "",
    contractType: "",
    threshold: "0.50",
    lastLoginDaysAgo: "",
    supportTickets: "",
    tenureMonths: "",
    featureAdoptionPct: "",
    monthlyRevenue: "",
    paymentDelayCount: "",
    algorithm: "XGBoost", // Default mengikuti warna biru pada desain Figma
  });

  // State untuk mengatur proses UI: 'idle' | 'loading' | 'success'
  const [predictionState, setPredictionState] = useState("idle");
  const [result, setResult] = useState<null | {
    probability: number;
    prediction: string;
    model: string;
    threshold: number;
    selectedFeatures: number;
    missingFeatures: string[];
    usedFeatures: string[];
  }>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleAlgorithmChange = (alg: string) => {
    setFormData((prev) => ({ ...prev, algorithm: alg }));
  };

  const handleRunPrediction = () => {
    setPredictionState("loading");
    // small helper to parse numbers from inputs
    const parseNum = (v: any) => {
      if (v === undefined || v === null || v === "") return NaN;
      const s = String(v).replace(',', '.');
      const n = Number(s);
      return isNaN(n) ? NaN : n;
    };

    // determine used/missing features
    const featureKeys = [
      'threshold',
      'lastLoginDaysAgo',
      'supportTickets',
      'tenureMonths',
      'featureAdoptionPct',
      'monthlyRevenue',
      'paymentDelayCount',
    ];

    const missing: string[] = [];
    const used: string[] = [];
    featureKeys.forEach((k) => {
      const v = (formData as any)[k];
      if (v === null || v === undefined || v === '') missing.push(k);
      else used.push(k);
    });

    // compute a simple heuristic probability (0..100)
    const lastLogin = parseNum(formData.lastLoginDaysAgo);
    const support = parseNum(formData.supportTickets);
    const tenure = parseNum(formData.tenureMonths);
    const adoption = parseNum(formData.featureAdoptionPct);
    const revenue = parseNum(formData.monthlyRevenue);
    const delay = parseNum(formData.paymentDelayCount);
    const thr = parseNum(formData.threshold);

    // base score from inputs (simple heuristic, for demo only)
    let score = 0.5;
    if (!isNaN(support)) score += Math.min(support * 0.03, 0.3);
    if (!isNaN(lastLogin)) score += Math.min(lastLogin * 0.005, 0.2);
    if (!isNaN(delay)) score += Math.min(delay * 0.04, 0.2);
    if (!isNaN(adoption)) score -= Math.min(adoption * 0.003, 0.3);
    if (!isNaN(tenure)) score -= Math.min(tenure * 0.002, 0.15);
    if (!isNaN(revenue)) score -= Math.min(revenue / 10000, 0.15);

    // clamp and convert to percent
    score = Math.max(0, Math.min(1, score));
    const probability = Math.round(score * 10000) / 100; // two decimals

    // prediction based on threshold (default 0.5)
    const thresholdForDecision = isNaN(thr) ? 0.5 : thr;
    const predictionLabel = score >= thresholdForDecision ? 'Churn' : 'Not Churn';

    setTimeout(() => {
      setResult({
        probability,
        prediction: predictionLabel,
        model: formData.algorithm || 'XGBoost',
        threshold: isNaN(thr) ? 0.5 : thr,
        selectedFeatures: used.length,
        missingFeatures: missing,
        usedFeatures: used,
      });
      setPredictionState('success');
    }, 1200);
  };

  return (
    <div className="flex w-full min-h-screen bg-slate-100 overflow-hidden font-['Lato']">
      
      {/* Sidebar Navigation */}
      <div className="w-20 min-h-screen bg-white border-r border-gray-100 flex flex-col items-center py-6">
        {/* Placeholder untuk ikon profil/menu di sidebar */}
        <div className="w-[30px] h-[30px] bg-slate-200 rounded-md mb-8"></div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-y-auto">
        
        {/* Top Bar */}
        <div className="w-full h-20 flex items-center justify-between px-8 bg-slate-100">
          <div className="flex items-center gap-4">
            <button className="w-9 h-9 bg-[#F0F0F3] rounded-md flex items-center justify-center text-slate-500">
              {/* Ikon Menu */}
              <span>☰</span> 
            </button>
            <h1 className="text-zinc-900 text-xl font-bold">Customer Churn Prediction</h1>
          </div>
          <div className="flex items-center gap-4">
            <button className="w-9 h-9 bg-[#F0F0F3] rounded-md flex items-center justify-center text-slate-500">
              {/* Ikon Search */}
              <span>🔍</span>
            </button>
            <button className="w-9 h-9 bg-[#F0F0F3] rounded-md flex items-center justify-center text-slate-500">
              {/* Ikon Add */}
              <span>+</span>
            </button>
          </div>
        </div>

        {/* Prediction Input Section */}
        <div className="px-8 pb-12">
          <div className="bg-white rounded-[10px] outline outline-1 outline-gray-100 p-6 shadow-sm">
            
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-zinc-900 text-lg font-bold">Prediction Input</h2>
              
              {/* Algorithm Type Selection */}
              <div className="flex items-center gap-4">
                <span className="text-slate-500 text-sm">Algorithm Type</span>
                <div className="flex gap-4">
                  <button 
                    onClick={() => handleAlgorithmChange("XGBoost")}
                    className="flex items-center gap-2"
                  >
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center ${formData.algorithm === "XGBoost" ? "bg-[#5E81F4]" : "bg-[#F0F0F3]"}`}>
                      {formData.algorithm === "XGBoost" && <div className="w-2 h-2 bg-white rounded-full"></div>}
                    </div>
                    <span className={`text-sm font-bold ${formData.algorithm === "XGBoost" ? "text-zinc-900" : "text-slate-500"}`}>XGBoost</span>
                  </button>
                  <button 
                    onClick={() => handleAlgorithmChange("CatBoost")}
                    className="flex items-center gap-2"
                  >
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center ${formData.algorithm === "CatBoost" ? "bg-[#5E81F4]" : "bg-[#F0F0F3]"}`}>
                      {formData.algorithm === "CatBoost" && <div className="w-2 h-2 bg-white rounded-full"></div>}
                    </div>
                    <span className={`text-sm font-bold ${formData.algorithm === "CatBoost" ? "text-zinc-900" : "text-slate-500"}`}>CatBoost</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Input Grid matching Analysis Input (no Status) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 mb-8">
              {/* Row 1: Plan Type */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Plan Type</label>
                <select name="planType" value={formData.planType} onChange={handleInputChange} className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none">
                  <option value="" disabled>Choose The Plan</option>
                  <option value="starter">Starter</option>
                  <option value="enterprise">Enterprise</option>
                  <option value="professional">Professional</option>
                </select>
              </div>

              {/* Row 1: Contract Type */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Contract Type</label>
                <select name="contractType" value={formData.contractType} onChange={handleInputChange} className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none">
                  <option value="" disabled>Choose The Contract</option>
                  <option value="month-to-month">Month-to-Month</option>
                  <option value="annual">Annual</option>
                </select>
              </div>

              {/* Row 2: Model (left) */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Model</label>
                <select name="algorithm" value={formData.algorithm} onChange={handleInputChange} className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none">
                  <option value="XGBoost">XGBoost</option>
                  <option value="CatBoost">CatBoost</option>
                </select>
              </div>

              {/* Row 2: Threshold (right) */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Threshold</label>
                <input type="text" name="threshold" value={formData.threshold} onChange={handleInputChange} placeholder="0.50" className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none placeholder-slate-400" />
              </div>

              {/* Row 3: Last Login Days Ago */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Last Login Days Ago</label>
                <input type="number" name="lastLoginDaysAgo" value={formData.lastLoginDaysAgo} onChange={handleInputChange} placeholder="0" className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
              </div>

              {/* Row 3: Support Tickets Last 90d */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Support Tickets Last 90d</label>
                <input type="number" name="supportTickets" value={formData.supportTickets} onChange={handleInputChange} placeholder="2" className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
              </div>

              {/* Row 4: Tenure Months */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Tenure Months</label>
                <input type="number" name="tenureMonths" value={formData.tenureMonths} onChange={handleInputChange} placeholder="24" className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
              </div>

              {/* Row 4: Feature Adoption PCT */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Feature Adoption PCT</label>
                <input type="text" name="featureAdoptionPct" value={formData.featureAdoptionPct} onChange={handleInputChange} placeholder="53.2" className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
              </div>

              {/* Row 5: Monthly Revenue */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Monthly Revenue</label>
                <input type="number" name="monthlyRevenue" value={formData.monthlyRevenue} onChange={handleInputChange} placeholder="181.75" className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
              </div>

              {/* Row 5: Payment Delay Count */}
              <div className="flex flex-col gap-2">
                <label className="text-slate-500 text-sm">Payment Delay Count</label>
                <input type="number" name="paymentDelayCount" value={formData.paymentDelayCount} onChange={handleInputChange} placeholder="0" className="rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" />
              </div>
            </div>

            {/* Run Prediction Button */}
            <div className="flex justify-center mt-6">
              <button 
                onClick={handleRunPrediction}
                disabled={predictionState === "loading"}
                className={`w-96 h-14 rounded-lg flex items-center justify-center text-white text-xl font-black tracking-wide transition-all ${predictionState === "loading" ? "bg-indigo-400 cursor-not-allowed" : "bg-indigo-500 hover:bg-indigo-600"}`}
              >
                {predictionState === "loading" ? "PROCESSING..." : "RUN PREDICTION"}
              </button>
            </div>
          </div>

          {/* Prediction Response Section */}
          <div className="mt-12">
            <h2 className="text-zinc-900 text-2xl font-bold mb-6">Prediction Response</h2>
            
            {/* Box Response (Rectangle 10 dari Figma) */}
            <div className="w-full h-96 bg-zinc-400/20 rounded-lg flex flex-col items-center justify-center p-8">
              
              {predictionState === "idle" && (
                <p className="text-slate-500 text-lg">Input the customer data above and run the model to view prediction results.</p>
              )}
              
              {predictionState === "loading" && (
                <div className="flex flex-col items-center animate-pulse">
                  <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                  <p className="text-slate-600 font-bold">Evaluating Customer Data with {formData.algorithm}...</p>
                </div>
              )}

              {predictionState === "success" && result && (
                <div className="w-full flex flex-col gap-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white p-4 rounded-md shadow-sm border border-gray-100 flex flex-col justify-center">
                      <span className="text-sm text-slate-500">Probability</span>
                      <strong className="text-3xl mt-2">{result.probability}%</strong>
                    </div>
                    <div className="bg-white p-4 rounded-md shadow-sm border border-gray-100 flex flex-col justify-center">
                      <span className="text-sm text-slate-500">Prediction</span>
                      <strong className="text-3xl mt-2">{result.prediction}</strong>
                    </div>
                    <div className="bg-white p-4 rounded-md shadow-sm border border-gray-100 flex flex-col justify-center">
                      <span className="text-sm text-slate-500">Model</span>
                      <strong className="text-3xl mt-2">{result.model}</strong>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-100 p-4 rounded-md flex flex-col justify-center">
                      <span className="text-sm text-slate-500">Threshold</span>
                      <strong className="text-2xl mt-2">{String(result.threshold).replace('.', ',')}</strong>
                    </div>
                    <div className="bg-slate-100 p-4 rounded-md flex flex-col justify-center">
                      <span className="text-sm text-slate-500">Plan Type</span>
                      <strong className="text-2xl mt-2">{formData.planType || '—'}</strong>
                    </div>
                    <div className="bg-slate-100 p-4 rounded-md flex flex-col justify-center">
                      <span className="text-sm text-slate-500">Selected Features</span>
                      <strong className="text-2xl mt-2">{result.selectedFeatures}</strong>
                    </div>
                  </div>

                  <div className="bg-white p-4 rounded-md shadow-sm border border-gray-100">
                    <div className="text-sm text-slate-700 font-semibold mb-2">Missing features: {result.missingFeatures.length === 0 ? 'None' : result.missingFeatures.join(', ')}</div>
                    <div className="text-sm text-slate-600">Used features: {result.usedFeatures.join(', ')}</div>
                  </div>

                  {/* explainable section */}
                  <div className="flex-1 bg-white p-6 rounded-md shadow-sm border border-gray-100">
                    <h4 className="font-bold text-slate-700 mb-4">Key Impact Factors (SHAP Values)</h4>
                    <div className="flex flex-col gap-3">
                      <div className="w-full bg-slate-100 h-8 rounded-md flex items-center px-4 relative overflow-hidden">
                        <div className="absolute left-0 top-0 h-full bg-red-400/50 w-[80%]"></div>
                        <span className="relative z-10 text-sm font-bold text-zinc-800">Support Tickets Last 90d (+1.2)</span>
                      </div>
                      <div className="w-full bg-slate-100 h-8 rounded-md flex items-center px-4 relative overflow-hidden">
                        <div className="absolute left-0 top-0 h-full bg-red-400/50 w-[65%]"></div>
                        <span className="relative z-10 text-sm font-bold text-zinc-800">Last Login Days Ago (+0.8)</span>
                      </div>
                      <div className="w-full bg-slate-100 h-8 rounded-md flex items-center px-4 relative overflow-hidden">
                        <div className="absolute left-0 top-0 h-full bg-blue-400/50 w-[30%]"></div>
                        <span className="relative z-10 text-sm font-bold text-zinc-800">Feature Adoption PCT (-0.4)</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}