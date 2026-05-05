export default function DataManagementPage() {
  return (
    <main className="dashboard-page">
      <section className="dashboard-banner surface-card">
        <div className="dashboard-title">
          <span className="section-tag">Data Management & Integration</span>
          <h1>Import & sync data</h1>
          <p className="dashboard-copy">Kelola aliran data pelanggan, ekspor laporan, dan pantau status pipeline dalam satu tempat.</p>
        </div>
        <div className="dashboard-actions">
          <button className="button-ghost" type="button">Search</button>
          <button className="button-ghost" type="button">Refresh</button>
        </div>
      </section>

      <section className="data-management-grid">
        <div className="surface-card data-panel import-panel">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Import & Sync Data</p>
              <h2>Upload CSV / Excel</h2>
            </div>
          </div>

          <div className="upload-card">
            <div className="upload-icon">⭳</div>
            <div>
              <strong>Drag & Drop CSV/Excel</strong>
              <p>or click to browse .csv, .xlsx</p>
            </div>
          </div>
        </div>

        <div className="surface-card data-panel export-panel">
          <div className="panel-header">
            <div>
              <p className="card-kicker">Export Data & Reports</p>
              <h2>Build export package</h2>
            </div>
          </div>

          <div className="export-grid">
            <label>
              Export Type
              <select>
                <option>Choose Type...</option>
                <option>Scored Customer Data</option>
                <option>NLP Sentiment Analysis</option>
                <option>Executive Summary Report</option>
              </select>
            </label>
            <label>
              Filter Export
              <select>
                <option>Choose Type...</option>
                <option>Starter</option>
                <option>Enterprise</option>
                <option>Professional</option>
              </select>
            </label>
          </div>

          <button className="primary-button" type="button">Download Data</button>
        </div>
      </section>

      <section className="surface-card logs-panel">
        <div className="panel-header">
          <div>
            <p className="card-kicker">Data Pipeline Logs</p>
            <h2>Pipeline activity</h2>
          </div>
        </div>

        <div className="table-scroll">
          <div className="list-table header-row">
            <span>Date & Time</span>
            <span>Action</span>
            <span>Status</span>
            <span>Rows</span>
          </div>
          <div className="list-row">
            <span>04 May 10:00</span>
            <span>Auto-Sync Supabase</span>
            <span className="status-chip success">Success</span>
            <span>+500</span>
          </div>
          <div className="list-row">
            <span>03 May 15:30</span>
            <span>Export Predicted Churn</span>
            <span className="status-chip success">Success</span>
            <span>3,050</span>
          </div>
          <div className="list-row">
            <span>01 May 09:15</span>
            <span>Upload ‘billing_apr.csv’</span>
            <span className="status-chip danger">Failed</span>
            <span>0</span>
          </div>
          <div className="list-row">
            <span>28 Apr 11:20</span>
            <span>Export NLP Sentiment</span>
            <span className="status-chip success">Success</span>
            <span>1,520</span>
          </div>
        </div>
      </section>
    </main>
  );
}
