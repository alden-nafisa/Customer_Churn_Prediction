"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Dashboard", icon: "⌂", href: "/" },
  { label: "Customer Prediction", icon: "👥", href: "/customer-prediction" },
  { label: "Advance Analysis", icon: "📊", href: "/advance-analysis" },
  { label: "Data Management", icon: "🗂️", href: "/data-management" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="app-sidebar">
      <div className="sidebar-top">
        <div className="logo-wrap">
          <div className="logo-mark">LA</div>
          <div className="logo-text">
            <strong>LapisAI</strong>
            <div className="muted">Welcome, Admin</div>
          </div>
        </div>

        <nav className="main-nav">
          {navItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`nav-btn ${pathname === item.href ? "active" : ""}`}
              title={item.label}
            >
              <span>{item.icon}</span>
            </Link>
          ))}
        </nav>
      </div>

      <div className="sidebar-body">
        <div className="log-feed">
          <h4>Log System & Machine Learning</h4>
          <ul>
            <li>
              <strong>Model Retrained</strong>
              <div className="muted">XGBoost model accuracy increased to 92.4%</div>
            </li>
            <li>
              <strong>Data Sync</strong>
              <div className="muted">500 new rows synced from Supabase</div>
            </li>
            <li>
              <strong>Auto-Action</strong>
              <div className="muted">Retention email sent to 5 Enterprise clients</div>
            </li>
          </ul>
        </div>

        <div className="high-risk">
          <h5>HIGH-RISK ALERT</h5>
          <ul>
            <li>
              <strong>C-0992 (Enterprise)</strong>
              <div className="muted">Probabilitas churn naik ke 85%. Segera tawarkan diskon.</div>
            </li>
            <li>
              <strong>C-0112 (Professional)</strong>
              <div className="muted">Mengirimkan 3 tiket komplain hari ini.</div>
            </li>
            <li>
              <strong>C-0091 (Starter)</strong>
              <div className="muted">Review sentiment negatif meningkat.</div>
            </li>
          </ul>
        </div>
      </div>

      <div className="sidebar-foot">
        <small className="muted">Live sync • High-risk dashboard</small>
      </div>
    </aside>
  );
}
