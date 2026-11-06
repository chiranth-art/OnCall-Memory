
import { useState } from "react";

import {
  AlertTriangle,
  BrainCircuit,
  Search,
  Clock,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  ArrowRight,
  RotateCcw,
  FileText
} from "lucide-react";

import { analyzeIncident } from "../services/api";

// Clearly labelled sample result for frontend demonstration
const demoResult = {
  incident_id: "INC-DEMO-1042",
  severity: "critical",

  root_cause: "Database connection pool exhaustion",

  explanation:
    "A sudden traffic spike caused the payment service to exceed its configured database connection pool limit.",

  similar_incidents: [
    {
      id: "INC-001",
      service: "payment-service",
      root_cause: "Database connection pool exhausted",
      fix_worked: "Increased connection pool size from 50 to 200",
      fixes_failed: [
        "Restarting payment service did not permanently resolve the issue"
      ],
      minutes_to_resolve: 25
    }
  ],

  recommendations: [
    "Inspect current database connection utilization.",
    "Verify available database connection capacity.",
    "Review the payment service connection pool configuration.",
    "Consider increasing the pool limit after capacity verification.",
    "Monitor payment requests after applying the approved fix."
  ],

  runbook: "Runbook B",
  confidence: "High"
};

export default function NewIncident() {
  const [error, setError] = useState("");
  const [service, setService] = useState("payment-service");
  const [logs, setLogs] = useState("");
  const [severity, setSeverity] = useState("critical");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [demoMode, setDemoMode] = useState(false);
  const [message, setMessage] = useState("");

  const handleAnalyze = async () => {
    if (!error.trim()) {
      setMessage("Please enter an incident description.");
      return;
    }

    setLoading(true);
    setResult(null);
    setMessage("");
    setDemoMode(false);

    try {
      const data = await analyzeIncident({
        error,
        service,
        logs,
        severity
      });

      setResult(data);

    } catch (err) {
      setMessage(
        err.response?.data?.detail ||
        "Backend unavailable. You can use the clearly labelled demo result while integration is in progress."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadDemo = () => {
    setResult(demoResult);
    setDemoMode(true);
    setMessage("");
  };

  const clearForm = () => {
    setError("");
    setLogs("");
    setResult(null);
    setMessage("");
    setDemoMode(false);
  };

  const similarIncidents =
    result?.similar_incidents || [];

  const recommendations =
    result?.recommendations || [];

  return (
    <div className="incident-page">

      <div className="page-intro">
        <div>
          <span className="section-eyebrow">
            <BrainCircuit size={15} />
            AI INVESTIGATION ENGINE
          </span>

          <h2>Investigate an Incident</h2>

          <p>
            Describe a production issue. IncidentIQ
            will search historical knowledge and
            help identify possible solutions.
          </p>
        </div>

        <button
          className="secondary-btn"
          onClick={clearForm}
        >
          <RotateCcw size={16} />
          Reset
        </button>
      </div>

      <div className="incident-form-card">

        <div className="form-heading">
          <div className="form-icon">
            <AlertTriangle size={21} />
          </div>

          <div>
            <h3>Incident Information</h3>
            <p>Provide the production error details.</p>
          </div>
        </div>

        <div className="form-grid">

          <div className="form-group full-width">
            <label>Error Description *</label>

            <textarea
              rows="3"
              placeholder="Example: Database connection timeout. Orders are failing..."
              value={error}
              onChange={(e) => setError(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Affected Service</label>

            <select
              value={service}
              onChange={(e) => setService(e.target.value)}
            >
              <option value="payment-service">
                Payment Service
              </option>

              <option value="authentication-service">
                Authentication Service
              </option>

              <option value="order-service">
                Order Service
              </option>

              <option value="database">
                Database
              </option>

              <option value="redis">
                Redis Cache
              </option>

              <option value="api-gateway">
                API Gateway
              </option>
            </select>
          </div>

          <div className="form-group">
            <label>Severity</label>

            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="form-group full-width">
            <label>Production Logs / Stack Trace</label>

            <textarea
              rows="5"
              placeholder="Paste your application logs here..."
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
            />
          </div>

        </div>

        <div className="form-actions">

          <button
            className="primary-btn"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Investigating...
              </>
            ) : (
              <>
                <Search size={17} />
                Analyze Incident
              </>
            )}
          </button>

          <button
            className="secondary-btn"
            onClick={loadDemo}
          >
            Load Demo Result
          </button>

        </div>

        {message && (
          <div className="api-message">
            <AlertTriangle size={17} />
            {message}
          </div>
        )}

      </div>

      {result && (
        <div className="analysis-results">

          <div className="results-header">
            <div>
              <span className="section-eyebrow">
                <BrainCircuit size={15} />
                INVESTIGATION REPORT
              </span>

              <h2>AI Analysis Results</h2>

              <p>
                Incident ID: {result.incident_id || "New Incident"}
              </p>
            </div>

            <span className="result-mode">
              {demoMode ? "DEMO DATA" : "LIVE RESPONSE"}
            </span>
          </div>

          <div className="root-cause-card">

            <div className="root-cause-top">
              <div className="form-icon">
                <ShieldAlert size={22} />
              </div>

              <span className="severity critical">
                {result.severity || severity}
              </span>
            </div>

            <span className="result-label">
              PROBABLE ROOT CAUSE
            </span>

            <h3>
              {result.root_cause || "Analysis completed"}
            </h3>

            <p>
              {result.explanation || "No explanation returned."}
            </p>

            <div className="root-cause-bottom">
              <span>
                Confidence: {result.confidence || "Not provided"}
              </span>

              <span>
                Runbook: {result.runbook || "Not specified"}
              </span>
            </div>

          </div>

          <div className="result-section">

            <div className="result-section-heading">
              <div>
                <h3>
                  <Search size={18} />
                  Similar Historical Incidents
                </h3>

                <p>
                  Previously recorded incidents relevant
                  to this investigation.
                </p>
              </div>

              <span className="count-badge">
                {similarIncidents.length} matches
              </span>
            </div>

            {similarIncidents.length > 0 ? (
              similarIncidents.map((incident, index) => (
                <div
                  className="similar-incident-card"
                  key={incident.id || index}
                >
                  <div className="similar-incident-top">
                    <strong>
                      {incident.id || incident.incident_id || `Match ${index + 1}`}
                    </strong>

                    <span>
                      {incident.service || "Historical incident"}
                    </span>
                  </div>

                  <p>
                    {incident.root_cause || incident.text || "Historical incident details retrieved."}
                  </p>

                  <div className="fix-comparison">

                    <div className="fix-success">
                      <CheckCircle2 size={17} />
                      <div>
                        <strong>Successful fix</strong>
                        <p>
                          {incident.fix_worked || "No successful fix recorded."}
                        </p>
                      </div>
                    </div>

                    <div className="fix-failed">
                      <XCircle size={17} />
                      <div>
                        <strong>Failed attempts</strong>
                        <p>
                          {Array.isArray(incident.fixes_failed)
                            ? incident.fixes_failed.join("; ")
                            : incident.fixes_failed || "No failed attempts recorded."}
                        </p>
                      </div>
                    </div>

                  </div>
                </div>
              ))
            ) : (
              <p className="empty-state">
                No similar historical incidents were returned.
              </p>
            )}

          </div>

          <div className="result-section recommendations-card">

            <div className="result-section-heading">
              <div>
                <h3>
                  <CheckCircle2 size={18} />
                  Recommended Resolution Steps
                </h3>

                <p>
                  Review these steps before making
                  production changes.
                </p>
              </div>
            </div>

            {recommendations.length > 0 ? (
              <div className="recommendation-list">
                {recommendations.map((step, index) => (
                  <div className="recommendation-item" key={index}>
                    <span>{index + 1}</span>
                    <p>
                      {typeof step === "string"
                        ? step
                        : step.description || step.action || JSON.stringify(step)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">
                No recommendations returned.
              </p>
            )}

            <div className="safety-notice">
              <ShieldAlert size={18} />
              <p>
                Recommendations require engineer review.
                Verify system capacity and operational
                safety before executing any production changes.
              </p>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
