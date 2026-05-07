"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./Sidebar.module.css";

const navItems = [
  { label: "Dashboard", icon: "⌂", href: "/" },
  { label: "Customer Prediction", icon: "👥", href: "/prediction" },
  { label: "Advance Analysis", icon: "📊", href: "/advance-analysis" },
  { label: "Data Management", icon: "🗂️", href: "/data-management" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.navColumn}>
        <Link href="/" className={`${styles.navBtn} ${pathname === '/' ? 'active' : ''}`}>
          <img src="/assets/icon_dashboard.svg" alt="Dashboard" style={{ width: 20, height: 20 }} />
        </Link>
        <Link href="/prediction" className={`${styles.navBtn} ${pathname === '/prediction' ? 'active' : ''}`}>
          <img src="/assets/icon_churn_prediction.svg" alt="Churn" style={{ width: 20, height: 20 }} />
        </Link>
        <Link href="/advance-analysis" className={`${styles.navBtn} ${pathname === '/advance-analysis' ? 'active' : ''}`}>
          <img src="/assets/icon_advance_analysis.svg" alt="Advance" style={{ width: 20, height: 20 }} />
        </Link>
        <Link href="/data-management" className={`${styles.navBtn} ${pathname === '/data-management' ? 'active' : ''}`}>
          <img src="/assets/icon_data_management.svg" alt="Data" style={{ width: 20, height: 20 }} />
        </Link>
        <a href="#" className={styles.navBtn} title="Sign out">
          <img src="/assets/icon_profile.svg" alt="Profile" style={{ width: 20, height: 20 }} />
        </a>
      </div>

      <div className={styles.infoPanel}>
        <div className={styles.logoWrap}>
          <img src="/assets/logo-lapisai.png" alt="LapisAI" style={{ width: 140 }} />
        </div>

        <div className="sidebar-body">
          <div className="log-feed">
            <h4>Log System & Machine Learning</h4>
            <ul>
              <li className={styles.logItem}><strong>Model Retrained</strong><div className={styles.muted}>XGBoost accuracy increased</div></li>
              <li className={styles.logItem}><strong>Data Sync</strong><div className={styles.muted}>500 new rows synced</div></li>
              <li className={styles.logItem}><strong>Auto-Action</strong><div className={styles.muted}>Retention email sent</div></li>
            </ul>
          </div>

          <div className="high-risk">
            <h5>HIGH-RISK ALERT</h5>
            <ul>
              <li className={styles.logItem}><strong>C-0992 (Enterprise)</strong><div className={styles.muted}>Probabilitas naik ke 85%</div></li>
              <li className={styles.logItem}><strong>C-0112 (Professional)</strong><div className={styles.muted}>3 tiket komplain</div></li>
            </ul>
          </div>
        </div>

        <div className="sidebar-foot">
          <small className={styles.muted}>Version 1.0 • Refresh</small>
        </div>
      </div>
    </aside>
  );
}
