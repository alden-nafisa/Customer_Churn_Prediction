"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type FeatureSpec = {
  name: string;
  data_type: "numeric" | "categorical";
  minimum?: number | null;
  maximum?: number | null;
  default_value?: string | number | null;
  step?: number | null;
};

type PlanSummary = {
  plan_type: "Starter" | "Professional" | "Enterprise";
  selected_features: string[];
  feature_specs: FeatureSpec[];
  metrics: Record<string, unknown>;
  available_models: Array<"XGBoost" | "CatBoost">;
};

type PlansResponse = {
  plans: PlanSummary[];
};

type PredictionResponse = {
  plan_type: PlanSummary["plan_type"];
  model_name: "XGBoost" | "CatBoost";
  threshold: number;
  probability: number;
  prediction: number;
  risk_label: "High Risk" | "Low Risk";
  selected_features: string[];
  used_features: Record<string, unknown>;
  missing_features: string[];
  metrics: Record<string, unknown>;
};

type FeatureValues = Record<string, string>;

const API_PROXY_BASE = "/api";

function toInputValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

export default function Home() {
  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<PlanSummary["plan_type"] | "">("");
  const [selectedModel, setSelectedModel] = useState<"XGBoost" | "CatBoost">("XGBoost");
  const [threshold, setThreshold] = useState("0.50");
  const [featureValues, setFeatureValues] = useState<FeatureValues>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PredictionResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPlans() {
      try {
        const response = await fetch(`${API_PROXY_BASE}/plans`);
        if (!response.ok) {
          throw new Error(`Failed to load plans: ${response.status}`);
        }
        const payload = (await response.json()) as PlansResponse;
        if (cancelled) {
          return;
        }

        setPlans(payload.plans);
        const firstPlan = payload.plans[0];
        if (firstPlan) {
          setSelectedPlan(firstPlan.plan_type);
          setSelectedModel(firstPlan.available_models[0] ?? "XGBoost");
          setFeatureValues(buildDefaultValues(firstPlan));
        }
      } catch (fetchError) {
        if (!cancelled) {
          setError(fetchError instanceof Error ? fetchError.message : "Failed to load plans.");
        }
      }
    }

    void loadPlans();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const plan = plans.find((item) => item.plan_type === selectedPlan);
    if (!plan) {
      return;
    }

    setSelectedModel(plan.available_models[0] ?? "XGBoost");
    setFeatureValues(buildDefaultValues(plan));
  }, [plans, selectedPlan]);

  const activePlan = useMemo(
    () => plans.find((plan) => plan.plan_type === selectedPlan) ?? null,
    [plans, selectedPlan],
  );

  function buildDefaultValues(plan: PlanSummary): FeatureValues {
    return plan.feature_specs.reduce<FeatureValues>((accumulator, spec) => {
      accumulator[spec.name] = toInputValue(spec.default_value);
      return accumulator;
    }, {});
  }

  function updateFeatureValue(name: string, value: string) {
    setFeatureValues((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlan) {
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const payload = {
        plan_type: selectedPlan,
        model_name: selectedModel,
        threshold: Number(threshold),
        features: Object.fromEntries(
          Object.entries(featureValues).map(([key, value]) => {
            if (value.trim() === "") {
              return [key, null];
            }
            const numericValue = Number(value);
            return [key, Number.isNaN(numericValue) ? value : numericValue];
          }),
        ),
      };

      const response = await fetch(`${API_PROXY_BASE}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail ?? `Prediction failed: ${response.status}`);
      }

      const prediction = (await response.json()) as PredictionResponse;
      setResult(prediction);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Prediction failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero-panel">
        <div className="hero-badge">Separated frontend • FastAPI backend • Vercel ready</div>
        <p className="eyebrow">FastAPI backend + Next.js frontend</p>
        <h1>Customer Churn Control Room</h1>
        <p className="hero-copy">
          Frontend ini terpisah dari model Python. Ia hanya mengirim fitur ke FastAPI,
          lalu menampilkan hasil prediksi per plan type.
        </p>

        <div className="hero-metrics">
          <div>
            <span>Deployment</span>
            <strong>Vercel + Render/Railway/Fly.io</strong>
          </div>
          <div>
            <span>Backend</span>
            <strong>FastAPI</strong>
          </div>
          <div>
            <span>Model routing</span>
            <strong>Per plan type</strong>
          </div>
        </div>

        <div className="hero-panel-footer">
          <div>
            <span>Live contract</span>
            <strong>/api/predict</strong>
          </div>
          <div>
            <span>UI mode</span>
            <strong>Glass dashboard</strong>
          </div>
        </div>
      </section>

      <section className="workspace-panel">
        <div className="workspace-strip">
          <div className="workspace-chip active">Plan-aware scoring</div>
          <div className="workspace-chip">API driven</div>
          <div className="workspace-chip">Responsive layout</div>
        </div>

        <div className="surface-card">
          <div className="card-header">
            <div>
              <p className="card-kicker">Prediction input</p>
              <h2>Choose plan and score a customer</h2>
            </div>
            <span className="api-pill">API proxy: same-origin /api</span>
          </div>

          {error ? <div className="alert error">{error}</div> : null}

          <form className="prediction-form" onSubmit={handleSubmit}>
            <label>
              Plan Type
              <select value={selectedPlan} onChange={(event) => setSelectedPlan(event.target.value as PlanSummary["plan_type"])}>
                {plans.map((plan) => (
                  <option key={plan.plan_type} value={plan.plan_type}>
                    {plan.plan_type}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Model
              <select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value as "XGBoost" | "CatBoost") }>
                {activePlan?.available_models.map((modelName) => (
                  <option key={modelName} value={modelName}>
                    {modelName}
                  </option>
                )) ?? null}
              </select>
            </label>

            <label>
              Threshold
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={threshold}
                onChange={(event) => setThreshold(event.target.value)}
              />
            </label>

            <div className="field-grid">
              {activePlan?.feature_specs.map((spec) => (
                <label key={spec.name}>
                  {spec.name.replace(/_/g, " ")}
                  <input
                    type="number"
                    step={spec.step ?? "any"}
                    min={spec.minimum ?? undefined}
                    max={spec.maximum ?? undefined}
                    value={featureValues[spec.name] ?? ""}
                    onChange={(event) => updateFeatureValue(spec.name, event.target.value)}
                  />
                </label>
              ))}
            </div>

            <button className="primary-button" type="submit" disabled={loading || !activePlan}>
              {loading ? "Scoring..." : "Run Prediction"}
            </button>
          </form>
        </div>

        <div className="surface-card result-card">
          <div className="card-header">
            <div>
              <p className="card-kicker">Result</p>
              <h2>Prediction response</h2>
            </div>
          </div>

          {result ? (
            <div className="result-stack">
              <div className={`result-badge ${result.risk_label === "High Risk" ? "danger" : "success"}`}>
                {result.risk_label}
              </div>
              <div className="result-grid">
                <div>
                  <span>Probability</span>
                  <strong>{(result.probability * 100).toFixed(2)}%</strong>
                </div>
                <div>
                  <span>Prediction</span>
                  <strong>{result.prediction === 1 ? "Churn" : "Not Churn"}</strong>
                </div>
                <div>
                  <span>Model</span>
                  <strong>{result.model_name}</strong>
                </div>
              </div>

              <div className="result-callout">
                <div>
                  <span>Threshold</span>
                  <strong>{result.threshold.toFixed(2)}</strong>
                </div>
                <div>
                  <span>Plan type</span>
                  <strong>{result.plan_type}</strong>
                </div>
                <div>
                  <span>Selected features</span>
                  <strong>{result.selected_features.length}</strong>
                </div>
              </div>

              <div className="result-meta">
                <p><strong>Missing features:</strong> {result.missing_features.length ? result.missing_features.join(", ") : "None"}</p>
                <p><strong>Used features:</strong> {Object.keys(result.used_features).join(", ")}</p>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p>Hasil prediksi akan muncul di sini setelah request dikirim ke FastAPI.</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
