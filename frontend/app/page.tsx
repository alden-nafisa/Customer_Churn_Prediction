"use client";

import { useState } from "react";

type DashboardTab = "Day" | "Week" | "Month";

const dashboardTabs: DashboardTab[] = ["Day", "Week", "Month"];

const metricCards = [
  { label: "Customers at Risk", value: "1,569", note: "Customers at Risk" },
  { label: "Revenue at Risk", value: "$45,200", note: "Revenue at Risk" },
  { label: "Average NPS", value: "7.4", note: "Average NPS" },
];

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

export default function Home() {
  const [churnTab, setChurnTab] = useState<DashboardTab>("Day");
  const [feedbackTab, setFeedbackTab] = useState<DashboardTab>("Month");

  return (
    <main className="dashboard-page">
      <section className="dashboard-topbar surface-card">
        <div className="topbar-left">
          <button className="icon-button" type="button">☰</button>
          <h1>Dashboard</h1>
        </div>
        <div className="topbar-actions">
          <button className="icon-button" type="button">🔍</button>
          <button className="icon-button" type="button">⟳</button>
        </div>
      </section>

      <section className="metrics-row">
        {metricCards.map((metric) => (
          <article key={metric.label} className="metric-card surface-card">
            <span className="metric-label">{metric.label}</span>
            <strong>{metric.value}</strong>
            <p className="metric-note">{metric.note}</p>
          </article>
        ))}
      </section>

      <section className="dashboard-grid">
        <section className="surface-card churn-panel">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Customer Churn</p>
              <h2>Customer Churn</h2>
            </div>
            <div className="toggle-group">
              {dashboardTabs.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`toggle-button ${churnTab === tab ? "active" : ""}`}
                  onClick={() => setChurnTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div className="list-table header-row">
            <span>Customer ID</span>
            <span>Details</span>
            <span>Details</span>
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
              <span className="score-cell">{row.score}</span>
              <span className={row.status === "Churned" ? "status-chip danger" : "status-chip success"}>
                {row.status}
              </span>
            </div>
          ))}

          <div className="panel-bottom">
            <button className="button-secondary" type="button">All Customer</button>
            <span>2,480 Total Customers</span>
          </div>
        </section>

        <section className="surface-card feedback-panel">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Feedback Customer</p>
              <h2>Feedback Customer</h2>
            </div>
            <div className="toggle-group">
              {dashboardTabs.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`toggle-button ${feedbackTab === tab ? "active" : ""}`}
                  onClick={() => setFeedbackTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div className="feedback-list">
            {feedbackRows.map((feedback) => (
              <div key={feedback.id} className="feedback-row">
                <div className="feedback-main">
                  <div className="feedback-icon">📄</div>
                  <div>
                    <strong>{feedback.id}</strong>
                    <p>{feedback.text}</p>
                  </div>
                </div>
                <div className="feedback-status">
                  <strong>NPS: {feedback.nps}</strong>
                  <span
                    className={
                      feedback.sentiment === "Positive"
                        ? "status-chip success"
                        : feedback.sentiment === "Negative"
                        ? "status-chip danger"
                        : "status-chip neutral"
                    }
                  >
                    {feedback.sentiment}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="panel-bottom">
            <button className="button-secondary" type="button">All Feedbacks</button>
            <span>1,520 Total Feedbacks</span>
          </div>
        </section>
      </section>
    </main>
  );
}
