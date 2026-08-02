import "./App.css";

function LandingPage({ onDemo, onLogin }) {
  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <h2>GrantAI</h2>

        <button
          type="button"
          className="secondary-button"
          onClick={onLogin}
        >
          Admin Login
        </button>
      </nav>

      <main className="landing-hero">
        <div className="landing-content">
          <p className="landing-label">
            AI-Powered Research Administration
          </p>

          <h1>Research Grant Management AI Platform</h1>

          <p className="landing-description">
            Manage research grants, upload documents, extract structured
            information with AI, monitor deadlines, track compliance, and
            export reports from one dashboard.
          </p>

          <div className="landing-actions">
            <button
              type="button"
              className="primary-large-button"
              onClick={onDemo}
            >
              Try Live Demo
            </button>

            <button
              type="button"
              className="secondary-large-button"
              onClick={onLogin}
            >
              Admin Login
            </button>
          </div>
        </div>

        <div className="feature-grid">
          <article className="feature-card">
            <h3>AI Document Extraction</h3>
            <p>
              Extract titles, investigators, agencies, funding amounts,
              deadlines, and summaries from grant documents.
            </p>
          </article>

          <article className="feature-card">
            <h3>Grant Dashboard</h3>
            <p>
              Track funding totals, grant statuses, deadlines, agencies,
              compliance issues, and administrative tasks.
            </p>
          </article>

          <article className="feature-card">
            <h3>Workflow Automation</h3>
            <p>
              Automatically flag urgent deadlines, create compliance tasks,
              and maintain audit logs.
            </p>
          </article>

          <article className="feature-card">
            <h3>Reports and Exports</h3>
            <p>
              Export grant records to CSV and Excel for analysis and business
              intelligence workflows.
            </p>
          </article>
        </div>
      </main>
    </div>
  );
}

export default LandingPage;