export default function AdvanceAnalysisPage() {
  return (
    <main className="dashboard-page">
      <section className="dashboard-banner surface-card">
        <div className="dashboard-title">
          <span className="section-tag">Advance Analysis</span>
          <h1>Churn insights & model explainability</h1>
          <p className="dashboard-copy">Analisis lebih dalam untuk menentukan faktor churn, estimasi risiko, dan rekomendasi retensi.</p>
        </div>
        <div className="dashboard-actions">
          <button className="button-ghost" type="button">Search</button>
          <button className="button-ghost" type="button">Refresh</button>
        </div>
      </section>

      <section className="analysis-grid">
        <div className="surface-card analysis-panel">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Analysis Input</p>
              <h2>Filter customer behavior</h2>
            </div>
            <div className="toggle-group">
              <button className="toggle-button active" type="button">XGBoost</button>
              <button className="toggle-button" type="button">CatBoost</button>
            </div>
          </div>

          <form className="analysis-form">
            <label>
              Plan Type
              <select>
                <option>Choose The Plan</option>
                <option>All</option>
                <option>Starter</option>
                <option>Professional</option>
                <option>Enterprise</option>
              </select>
            </label>
            <label>
              Contract Type
              <select>
                <option>Choose The Contract</option>
                <option>All</option>
                <option>Monthly</option>
                <option>Annual</option>
              </select>
            </label>
            <label>
              Status
              <select>
                <option>Choose The Status</option>
                <option>Churned</option>
                <option>Not Churned</option>
              </select>
            </label>
            <label>
              Threshold
              <input type="number" placeholder="0.50" />
            </label>
            <label>
              Last Login Days Ago
              <input type="number" placeholder="0" />
            </label>
            <label>
              Support Tickets Last 90d
              <input type="number" placeholder="2" />
            </label>
            <label>
              Tenure Months
              <input type="number" placeholder="24" />
            </label>
            <label>
              Feature Adoption PCT
              <input type="number" placeholder="53.2" />
            </label>
            <label>
              Monthly Revenue
              <input type="number" placeholder="181.75" />
            </label>
            <label>
              Payment Delay Count
              <input type="number" placeholder="0" />
            </label>
          </form>

          <div className="analysis-summary-grid">
            <article className="metric-card small-card">
              <span>Total Evaluated</span>
              <strong>3,000</strong>
              <p>Customers in view</p>
            </article>
            <article className="metric-card small-card">
              <span>High-Risk Cust</span>
              <strong>1,569</strong>
              <p>Predicted Churn</p>
            </article>
            <article className="metric-card small-card">
              <span>Model Accuracy</span>
              <strong>77.07%</strong>
              <p>Accuracy dan Match Rate</p>
            </article>
            <article className="metric-card small-card">
              <span>Avg. Probability</span>
              <strong>50.80%</strong>
              <p>Probability</p>
            </article>
          </div>
        </div>

        <div className="surface-card chart-column">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Histogram Probabilities</p>
              <h2>Churn distribution</h2>
            </div>
            <div className="toggle-group">
              <button className="toggle-button active" type="button">Day</button>
              <button className="toggle-button" type="button">Week</button>
              <button className="toggle-button" type="button">Month</button>
            </div>
          </div>
          <div className="chart-card">Chart placeholder</div>

          <div className="panel-header" style={{ marginTop: 24 }}>
            <div>
              <p className="card-kicker">Predicted Revenue Loss</p>
              <h2>Risk impact</h2>
            </div>
          </div>
          <div className="chart-card">Chart placeholder</div>
        </div>
      </section>

      <section className="surface-card analysis-details-panel">
        <div className="panel-header">
          <div>
            <p className="card-kicker">Top Global SHAP Drivers</p>
            <h2>Model explanation</h2>
          </div>
        </div>

        <div className="shap-grid">
          <div className="shap-row">
            <span>num_monthly_usage_hrs</span>
            <div className="shap-bar" />
            <strong>0.3</strong>
          </div>
          <div className="shap-row">
            <span>num_tenure_months</span>
            <div className="shap-bar" />
            <strong>0.3</strong>
          </div>
          <div className="shap-row">
            <span>num_feature_adoption_pct</span>
            <div className="shap-bar" />
            <strong>0.3</strong>
          </div>
          <div className="shap-row">
            <span>num_last_login_days_ago</span>
            <div className="shap-bar" />
            <strong>0.3</strong>
          </div>
          <div className="shap-row">
            <span>num_support_tickets_last_90d</span>
            <div className="shap-bar" />
            <strong>0.3</strong>
          </div>
          <div className="shap-row">
            <span>num_nps_score</span>
            <div className="shap-bar" />
            <strong>0.3</strong>
          </div>
        </div>
      </section>
    </main>
  );
}
