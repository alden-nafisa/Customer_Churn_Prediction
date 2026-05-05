"use client";

export default function NotFound() {
  return (
    <main className="not-found-page">
      <div className="surface-card not-found-card">
        <div className="status-circle">404</div>
        <h1>Website Not Responding</h1>
        <p>Please wait until the process begins.</p>
        <a className="primary-button" href="/">Refresh</a>
      </div>
    </main>
  );
}
