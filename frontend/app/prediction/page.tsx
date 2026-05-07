"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import styles from "./Prediction.module.css";

type FeatureSpec = {
  name: string;
  data_type: "numeric" | "categorical";
  minimum?: number | null;
  maximum?: number | null;
  default_value?: string | number | null;
  step?: number | null;
};

type PlanSummary = {
  plan_type: string;
  selected_features: string[];
  feature_specs: FeatureSpec[];
  metrics: Record<string, unknown>;
  available_models: string[];
};

export default function PredictionPage() {
  // Default fallback plan when backend /api/plans is unavailable
  const defaultPlan: PlanSummary = {
    plan_type: "Starter",
    selected_features: [
      "last_login_days_ago",
      "support_tickets_last_90d",
      "tenure_months",
      "feature_adoption_pct",
      "monthly_revenue",
      "payment_delay_count",
    ],
    feature_specs: [
      { name: "last_login_days_ago", data_type: "numeric", minimum: 0, maximum: null, default_value: 0, step: 1 },
      { name: "support_tickets_last_90d", data_type: "numeric", minimum: 0, maximum: null, default_value: 2, step: 1 },
      { name: "tenure_months", data_type: "numeric", minimum: 0, maximum: null, default_value: 24, step: 1 },
      { name: "feature_adoption_pct", data_type: "numeric", minimum: 0, maximum: 100, default_value: 53.2, step: 0.1 },
      { name: "monthly_revenue", data_type: "numeric", minimum: 0, maximum: null, default_value: 181.75, step: 0.01 },
      { name: "payment_delay_count", data_type: "numeric", minimum: 0, maximum: null, default_value: 0, step: 1 },
    ],
    metrics: {},
    available_models: ["XGBoost", "CatBoost"],
  };
  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("XGBoost");
  const [threshold, setThreshold] = useState("0.50");
  const [contractType, setContractType] = useState<string>("all");
  const [featureValues, setFeatureValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    async function loadPlans() {
      try {
        const r = await fetch("/api/plans");
        if (!r.ok) throw new Error("Failed to fetch plans");
        const payload = await r.json();
        if (cancelled) return;
        setPlans(payload.plans ?? []);
        if (payload.plans?.length) {
          const p = payload.plans[0];
          setSelectedPlan(p.plan_type);
          setSelectedModel(p.available_models?.[0] ?? "XGBoost");
          const defaults: Record<string, string> = {};
          (p.feature_specs || []).forEach((s: FeatureSpec) => { defaults[s.name] = s.default_value == null ? "" : String(s.default_value); });
          setFeatureValues(defaults);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          // populate fallback defaults so form renders without backend
          setSelectedPlan(defaultPlan.plan_type);
          setSelectedModel(defaultPlan.available_models?.[0] ?? 'XGBoost');
          const defaults: Record<string, string> = {};
          (defaultPlan.feature_specs || []).forEach((s: FeatureSpec) => { defaults[s.name] = s.default_value == null ? "" : String(s.default_value); });
          setFeatureValues(defaults);
        }
      }
    }
    void loadPlans();
    return () => { cancelled = true; };
  }, []);

  const activePlan = useMemo(() => plans.find((p) => p.plan_type === selectedPlan) ?? null, [plans, selectedPlan]);
  const effectivePlan = activePlan ?? defaultPlan;

  function updateFeature(name: string, value: string) {
    setFeatureValues((c) => ({ ...c, [name]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedPlan) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const features = Object.fromEntries(Object.entries(featureValues).map(([k,v]) => [k, v === "" ? null : Number(v)]));
      const payload = { plan_type: selectedPlan, model_name: selectedModel, threshold: Number(threshold), features };
      const r = await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!r.ok) throw new Error(`Prediction failed: ${r.status}`);
      const body = await r.json();
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally { setLoading(false); }
  }

  return (
    <main className="min-h-screen p-8 bg-slate-50">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-3">
          <div className={styles.card}>
            <h3 className="text-lg font-semibold">Prediction Input</h3>
            {error ? <div className="text-red-600 mt-2">{error}</div> : null}
            <form className={styles.formGrid} onSubmit={handleSubmit}>
              <div className="flex items-center justify-between gap-4">
                <div className="w-full">
                  <label>
                    Plan Type
                    <select value={selectedPlan} onChange={(e) => setSelectedPlan(e.target.value)} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none">
                      {plans.length ? plans.map((p) => <option key={p.plan_type} value={p.plan_type}>{p.plan_type}</option>) : (
                        <>
                          <option value="starter">Starter</option>
                          <option value="enterprise">Enterprise</option>
                          <option value="professional">Professional</option>
                        </>
                      )}
                    </select>
                  </label>
                </div>

                <div className="w-56 flex items-center justify-end gap-3">
                  <button type="button" onClick={() => setSelectedModel('XGBoost')}
                    className={`px-4 py-2 rounded-full border ${selectedModel==='XGBoost' ? 'bg-indigo-100 border-indigo-300' : 'bg-white'} text-sm font-semibold`}>
                    XGBoost
                  </button>
                  <button type="button" onClick={() => setSelectedModel('CatBoost')}
                    className={`px-4 py-2 rounded-full border ${selectedModel==='CatBoost' ? 'bg-indigo-100 border-indigo-300' : 'bg-white'} text-sm font-semibold`}>
                    CatBoost
                  </button>
                </div>
                <div className="w-40">
                  <label>
                    Contract Type
                    <select value={contractType} onChange={(e) => setContractType(e.target.value)} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-3 text-sm text-zinc-900 outline-none">
                      <option value="all">All</option>
                      <option value="monthly">Monthly</option>
                      <option value="annualy">Annualy</option>
                    </select>
                  </label>
                </div>

                <div className="w-48">
                  <label>
                    Threshold
                    <input type="text" step="0.01" min="0" max="1" value={threshold} onChange={(e) => setThreshold(e.target.value)} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none placeholder-slate-400" />
                  </label>
                </div>
              </div>

              <div className={styles.fieldGrid}>
                {effectivePlan.feature_specs.map((spec) => (
                  <label key={spec.name}>
                    {spec.name.replace(/_/g, " ")}
                    <input type="number" step={spec.step ?? "any"} min={spec.minimum ?? undefined} max={spec.maximum ?? undefined} value={featureValues[spec.name] ?? ""} onChange={(e) => updateFeature(spec.name, e.target.value)} className="mt-1 block w-full rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm text-zinc-900 outline-none" placeholder={spec.default_value == null ? '' : String(spec.default_value)} />
                  </label>
                ))}
              </div>

              <div className="mt-4">
                <button type="submit" className="inline-flex items-center px-6 py-3 rounded-full bg-indigo-600 text-white font-bold hover:bg-indigo-700" disabled={loading}>{loading ? 'Scoring...' : 'Run Prediction'}</button>
              </div>

              {/* Selected Features moved into form under button */}
              <div className="mt-4 bg-slate-50 p-4 rounded-lg border border-slate-100">
                <div className="text-sm font-semibold mb-2">Selected Features</div>
                <div className="flex flex-wrap gap-2">
                  {(effectivePlan.selected_features ?? []).map((f) => (
                    <span key={f} className={styles.pill}>{f.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              </div>
            </form>
          </div>

          <div className="mt-6">
            <div className={styles.card}>
              <h3 className="text-lg font-semibold">Prediction Response</h3>
              {result ? (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-white rounded-lg border"> 
                    <div className="muted">Probability</div>
                    <div className={styles.resultValue}>{(result.probability * 100).toFixed(2)}%</div>
                  </div>
                  <div className="p-4 bg-white rounded-lg border">
                    <div className="muted">Prediction</div>
                    <div className="text-xl font-semibold">{result.prediction === 1 ? 'Churn' : 'Not Churn'}</div>
                  </div>
                  <div className="p-4 bg-white rounded-lg border">
                    <div className="muted">Model</div>
                    <div className="text-xl font-semibold">{result.model_name}</div>
                  </div>
                </div>
              ) : (
                <div className={styles.empty}><span className={styles.muted}>Hasil prediksi akan tampil di sini setelah menjalankan scoring.</span></div>
              )}
            </div>
          </div>
        </section>

        {/* aside removed - Selected Features now displayed inside the form */}
      </div>
    </main>
  );
}
