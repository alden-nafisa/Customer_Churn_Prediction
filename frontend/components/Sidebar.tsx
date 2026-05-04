"use client";

export default function Sidebar() {
  return (
    <aside className="app-sidebar">
      <div className="sidebar-top">
        <div className="logo-wrap">
          <div className="logo-mark">◧</div>
          <div className="logo-text">
            <strong>LapisAI</strong>
            <div className="muted">Welcome, Admin</div>
          </div>
        </div>

        <nav className="main-nav">
          <button className="nav-btn">🏠</button>
          <button className="nav-btn">📊</button>
          <button className="nav-btn">👥</button>
          <button className="nav-btn">📁</button>
          <button className="nav-btn">✉️</button>
        </nav>
      </div>

      <div className="sidebar-body">
        <div className="log-feed">
          <h4>Log System & Machine Learning</h4>
          <ul>
            <li><strong>Model Retrained</strong><div className="muted">XGBoost accuracy increased</div></li>
            <li><strong>Data Sync</strong><div className="muted">500 new rows synced</div></li>
            <li><strong>Auto-Action</strong><div className="muted">Retention email sent</div></li>
          </ul>
        </div>

        <div className="high-risk">
          <h5>HIGH-RISK ALERT</h5>
          <ul>
            <li><strong>C-0992 (Enterprise)</strong><div className="muted">Probabilitas naik ke 85%</div></li>
            <li><strong>C-0112 (Professional)</strong><div className="muted">3 tiket komplain</div></li>
          </ul>
        </div>
      </div>

      <div className="sidebar-foot">
        <small className="muted">Version 1.0 • Refresh</small>
      </div>
    </aside>
  );
}
