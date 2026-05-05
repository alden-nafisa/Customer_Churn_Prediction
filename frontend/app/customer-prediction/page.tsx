"use client";

import { FormEvent, useState } from "react";

type PredictionResult = {
  probability: number;
  prediction: string;
  model: string;
  threshold: number;
  plan_type: string;
  selected_features: number;
  missing_features: string;
  used_features: string;
};

export default function CustomerPredictionPage() {
  const [selectedModel, setSelectedModel] = useState("XGBoost");
  const [planType, setPlanType] = useState("Starter");
  const [contractType, setContractType] = useState("All");
  const [threshold, setThreshold] = useState("0.50");
  const [lastLoginDays, setLastLoginDays] = useState("");
  const [supportTickets, setSupportTickets] = useState("");
  const [tenureMonths, setTenureMonths] = useState("");
  const [featureAdoption, setFeatureAdoption] = useState("");
  const [monthlyRevenue, setMonthlyRevenue] = useState("");
  const [paymentDelayCount, setPaymentDelayCount] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);

    // Simulasi prediksi - nanti diganti dengan API call
    setTimeout(() => {
      setResult({
        probability: 99.21,
        prediction: "Churn",
        model: selectedModel,
        threshold: parseFloat(threshold),
        plan_type: planType,
        selected_features: 6,
        missing_features: "None",
        used_features: "last_login_days_ago, support_tickets_last_90d, tenure_months, feature_adoption_pct, monthly_revenue, payment_delay_count",
      });
      setLoading(false);
    }, 1000);
  }

  return (
    <main className="dashboard-page">
      <section className="dashboard-topbar surface-card">
        <div className="topbar-left">
          <button className="icon-button" type="button">☰</button>
          <h1>Customer Churn Prediction</h1>
        </div>
        <div className="topbar-actions">
          <button className="icon-button" type="button">🔍</button>
          <button className="icon-button" type="button">⟳</button>
        </div>
      </section>

      <section className="surface-card prediction-section">
        <div className="prediction-header">
          <div>
            <p className="card-kicker">Prediction Input</p>
            <h2>Prediction Input</h2>
          </div>
          <div className="algorithm-group">
            <label>
              <input
                type="radio"
                name="algorithm"
                value="XGBoost"
                checked={selectedModel === "XGBoost"}
                onChange={(e) => setSelectedModel(e.target.value)}
              />
              XGBoost
            </label>
            <label>
              <input
                type="radio"
                name="algorithm"
                value="CatBoost"
                checked={selectedModel === "CatBoost"}
                onChange={(e) => setSelectedModel(e.target.value)}
              />
              CatBoost
            </label>
          </div>
        </div>

        <form className="prediction-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="plan">Plan Type</label>
            <select
              id="plan"
              value={planType}
              onChange={(e) => setPlanType(e.target.value)}
            >
              <option value="Starter">Starter</option>
              <option value="Professional">Professional</option>
              <option value="Enterprise">Enterprise</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="contract">Contract Type</label>
            <select
              id="contract"
              value={contractType}
              onChange={(e) => setContractType(e.target.value)}
            >
              <option value="All">All</option>
              <option value="Monthly">Monthly</option>
              <option value="Annual">Annual</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="threshold">Threshold</label>
            <input
              id="threshold"
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              placeholder="0.50"
            />
          </div>

          <div className="form-group">
            <label htmlFor="lastLogin">Last Login Days Ago</label>
            <input
              id="lastLogin"
              type="number"
              value={lastLoginDays}
              onChange={(e) => setLastLoginDays(e.target.value)}
              placeholder="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="support">Support Tickets Last 90d</label>
            <input
              id="support"
              type="number"
              value={supportTickets}
              onChange={(e) => setSupportTickets(e.target.value)}
              placeholder="2"
            />
          </div>

          <div className="form-group">
            <label htmlFor="tenure">Tenure Months</label>
            <input
              id="tenure"
              type="number"
              value={tenureMonths}
              onChange={(e) => setTenureMonths(e.target.value)}
              placeholder="24"
            />
          </div>

          <div className="form-group">
            <label htmlFor="adoption">Feature Adoption PCT</label>
            <input
              id="adoption"
              type="number"
              value={featureAdoption}
              onChange={(e) => setFeatureAdoption(e.target.value)}
              placeholder="53.2"
            />
          </div>

          <div className="form-group">
            <label htmlFor="revenue">Monthly Revenue</label>
            <input
              id="revenue"
              type="number"
              value={monthlyRevenue}
              onChange={(e) => setMonthlyRevenue(e.target.value)}
              placeholder="181.75"
            />
          </div>

          <div className="form-group">
            <label htmlFor="payment">Payment Delay Count</label>
            <input
              id="payment"
              type="number"
              value={paymentDelayCount}
              onChange={(e) => setPaymentDelayCount(e.target.value)}
              placeholder="0"
            />
          </div>

          <button type="submit" className="btn-predict" disabled={loading}>
            {loading ? "RUNNING..." : "RUN PREDICTION"}
          </button>
        </form>
      </section>

      <section className="surface-card prediction-response-section">
        <h3 className="response-title">Prediction Response</h3>

        {result ? (
          <>
            <div className="response-grid">
              <div className="response-card">
                <span className="response-label">Probability</span>
                <strong className="response-value">{(result.probability).toFixed(2)}%</strong>
              </div>
              <div className="response-card">
                <span className="response-label">Prediction</span>
                <strong className="response-value">{result.prediction}</strong>
              </div>
              <div className="response-card">
                <span className="response-label">Model</span>
                <strong className="response-value">{result.model}</strong>
              </div>
            </div>

            <div className="response-grid">
              <div className="response-card">
                <span className="response-label">Threshold</span>
                <strong className="response-value">{result.threshold.toFixed(2)}</strong>
              </div>
              <div className="response-card">
                <span className="response-label">Plan Type</span>
                <strong className="response-value">{result.plan_type}</strong>
              </div>
              <div className="response-card">
                <span className="response-label">Selected Features</span>
                <strong className="response-value">{result.selected_features}</strong>
              </div>
            </div>

            <div className="response-info">
              <p><strong>Missing features:</strong> {result.missing_features}</p>
              <p><strong>Used features:</strong> {result.used_features}</p>
            </div>
          </>
        ) : (
          <div className="response-empty">
            <p className="muted">Isi form dan klik RUN PREDICTION untuk menampilkan hasil di sini.</p>
          </div>
        )}
      </section>
    </main>
  );
}
