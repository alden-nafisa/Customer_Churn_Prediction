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
const dashboardTabs = ["Day", "Week", "Month"];

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
  const [dashboardView, setDashboardView] = useState<string>(dashboardTabs[0]);

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

  const churnRows = [
    { id: "C-0267", plan: "Starter/Monthly", score: "0.567", status: "Not Churned" },
    { id: "C-0091", plan: "Starter/Monthly", score: "0.867", status: "Churned" },
    { id: "C-0176", plan: "Starter/Monthly", score: "0.389", status: "Churned" },
    { id: "C-0056", plan: "Starter/Monthly", score: "0.567", status: "Churned" },
    { id: "C-0002", plan: "Starter/Monthly", score: "0.375", status: "Not Churned" },
    { id: "C-0001", plan: "Starter/Monthly", score: "0.876", status: "Churned" },
    { id: "C-0011", plan: "Starter/Monthly", score: "0.567", status: "Churned" },
  ];

  const feedbackRows = [
    { id: "C-0267", text: "UI responsif, prediksi sangat akurat.", sentiment: "Positive", nps: 9 },
    { id: "C-0091", text: "Performa lambat saat muat dataset.", sentiment: "Negative", nps: 5 },
    { id: "C-0176", text: "Analisis sentimen NLP luar biasa!", sentiment: "Positive", nps: 8 },
    { id: "C-0056", text: "Bagus, butuh fitur ekspor PDF.", sentiment: "Positive", nps: 10 },
    { id: "C-0002", text: "Dokumentasi API masih kurang lengkap.", sentiment: "Neutral", nps: 6 },
    { id: "C-0001", text: "Fitur membantu, harga agak mahal.", sentiment: "Neutral", nps: 7 },
    { id: "C-0011", text: "Integrasi mulus, tim support responsif.", sentiment: "Positive", nps: 9 },
  ];

  const metricCards = [
    { label: "Customers at Risk", value: "1,569", note: "Customers at risk" },
    { label: "Revenue at Risk", value: "$45,200", note: "Revenue at risk" },
    { label: "Average NPS", value: "7.4", note: "Sentiment score" },
  ];

  return (
    <main className="dashboard-page">
      <section className="dashboard-banner surface-card">
        <div className="dashboard-title">
          <span className="section-tag">Dashboard</span>
          <h1>Customer Health Overview</h1>
          <p className="dashboard-copy">Tinjau metrik churn, feedback pelanggan, dan jalankan prediksi langsung dari satu kontrol panel.</p>
        </div>
        <div className="dashboard-actions">
          <button className="button-ghost" type="button">Search</button>
          <button className="button-ghost" type="button">Refresh</button>
        </div>
      </section>

      <section className="metrics-row">
        {metricCards.map((metric) => (
          <article key={metric.label} className="metric-card surface-card">
            <p className="metric-label">{metric.label}</p>
            <strong>{metric.value}</strong>
            <p className="metric-note">{metric.note}</p>
          </article>
        ))}
      </section>

      <section className="dashboard-panels">
        <div className="surface-card churn-panel">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Customer Churn</p>
              <h2>High-risk customers</h2>
            </div>
            <div className="toggle-group">
              {dashboardTabs.map((period) => (
                <button
                  key={period}
                  type="button"
                  className={dashboardView === period ? "toggle-button active" : "toggle-button"}
                  onClick={() => setDashboardView(period)}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>

          <div className="table-scroll">
            <div className="list-table header-row">
              <span>Customer ID</span>
              <span>Plan</span>
              <span>Score</span>
            </div>
            {churnRows.map((row) => (
              <div key={row.id} className="list-row">
                <div className="customer-cell">
                  <div className="customer-avatar" />
                  <div>
                    <strong>{row.id}</strong>
                    <small>{row.plan}</small>
                  </div>
                </div>
                <span>{row.plan}</span>
                <div className="status-cell">
                  <span className={row.status === "Churned" ? "status-chip danger" : "status-chip success"}>
                    {row.status}
                  </span>
                  <strong>{row.score}</strong>
                </div>
              </div>
            ))}
          </div>

          <div className="panel-bottom">
            <button className="button-secondary" type="button">All Customer</button>
            <span>2,480 Total Customers</span>
          </div>
        </div>

        <div className="surface-card feedback-panel">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Feedback Customer</p>
              <h2>Sentiment summary</h2>
            </div>
            <div className="toggle-group">
              {dashboardTabs.map((period) => (
                <button
                  key={period}
                  type="button"
                  className={dashboardView === period ? "toggle-button active" : "toggle-button"}
                  onClick={() => setDashboardView(period)}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>

          <div className="table-scroll feedback-list">
            {feedbackRows.map((feedback) => (
              <div key={feedback.id} className="feedback-row">
                <div>
                  <strong>{feedback.id}</strong>
                  <p>{feedback.text}</p>
                </div>
                <div className="feedback-meta">
                  <span className={
                    feedback.sentiment === "Positive"
                      ? "status-chip success"
                      : feedback.sentiment === "Negative"
                      ? "status-chip danger"
                      : "status-chip neutral"
                  }>
                    {feedback.sentiment}
                  </span>
                  <strong>NPS: {feedback.nps}</strong>
                </div>
              </div>
            ))}
          </div>

          <div className="panel-bottom">
            <button className="button-secondary" type="button">All Feedbacks</button>
            <span>1,520 Total Feedbacks</span>
          </div>
        </div>
      </section>

      <section className="prediction-section">
        <div className="prediction-column">
          <div className="surface-card prediction-panel">
            <div className="panel-header">
              <div>
                <p className="card-kicker">Customer Churn Prediction</p>
                <h2>Prediction input</h2>
              </div>
              <div className="algorithm-group">
                <label>
                  <input
                    type="radio"
                    name="model"
                    value="XGBoost"
                    checked={selectedModel === "XGBoost"}
                    onChange={() => setSelectedModel("XGBoost")}
                  />
                  XGBoost
                </label>
                <label>
                  <input
                    type="radio"
                    name="model"
                    value="CatBoost"
                    checked={selectedModel === "CatBoost"}
                    onChange={() => setSelectedModel("CatBoost")}
                  />
                  CatBoost
                </label>
              </div>
            </div>

            {error ? <div className="alert error">{error}</div> : null}

            <form className="prediction-form grid-form" onSubmit={handleSubmit}>
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
                Contract Type
                <select>
                  <option>All</option>
                  <option>Monthly</option>
                  <option>Annual</option>
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
              <label>
                Last Login Days Ago
                <input
                  type="number"
                  value={featureValues["last_login_days_ago"] ?? ""}
                  onChange={(event) => updateFeatureValue("last_login_days_ago", event.target.value)}
                />
              </label>
              <label>
                Support Tickets Last 90d
                <input
                  type="number"
                  value={featureValues["support_tickets_last_90d"] ?? ""}
                  onChange={(event) => updateFeatureValue("support_tickets_last_90d", event.target.value)}
                />
              </label>
              <label>
                Tenure Months
                <input
                  type="number"
                  value={featureValues["tenure_months"] ?? ""}
                  onChange={(event) => updateFeatureValue("tenure_months", event.target.value)}
                />
              </label>
              <label>
                Feature Adoption PCT
                <input
                  type="number"
                  value={featureValues["feature_adoption_pct"] ?? ""}
                  onChange={(event) => updateFeatureValue("feature_adoption_pct", event.target.value)}
                />
              </label>
              <label>
                Monthly Revenue
                <input
                  type="number"
                  value={featureValues["monthly_revenue"] ?? ""}
                  onChange={(event) => updateFeatureValue("monthly_revenue", event.target.value)}
                />
              </label>
              <label>
                Payment Delay Count
                <input
                  type="number"
                  value={featureValues["payment_delay_count"] ?? ""}
                  onChange={(event) => updateFeatureValue("payment_delay_count", event.target.value)}
                />
              </label>

              <button className="primary-button full-width" type="submit" disabled={loading || !activePlan}>
                {loading ? "Running prediction..." : "Run Prediction"}
              </button>
            </form>
          </div>

          <div className="surface-card response-panel">
            <div className="panel-header">
              <div>
                <p className="card-kicker">Prediction Response</p>
                <h2>Model output</h2>
              </div>
            </div>

            {result ? (
              <div className="response-grid">
                <div className="response-card-top">
                  <div className="response-metric">
                    <span>Probability</span>
                    <strong>{(result.probability * 100).toFixed(2)}%</strong>
                  </div>
                  <div className="response-metric">
                    <span>Prediction</span>
                    <strong>{result.prediction === 1 ? "Churn" : "Not Churn"}</strong>
                  </div>
                  <div className="response-metric">
                    <span>Model</span>
                    <strong>{result.model_name}</strong>
                  </div>
                </div>

                <div className="response-info-row">
                  <div>
                    <span>Threshold</span>
                    <strong>{result.threshold.toFixed(2)}</strong>
                  </div>
                  <div>
                    <span>Plan Type</span>
                    <strong>{result.plan_type}</strong>
                  </div>
                  <div>
                    <span>Selected Features</span>
                    <strong>{result.selected_features.length}</strong>
                  </div>
                </div>

                <div className="result-summary">
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
        </div>
      </section>
    </main>
  );
}
