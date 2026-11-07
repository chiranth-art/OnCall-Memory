
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  AlertTriangle,
  BrainCircuit,
  Search,
  CheckCircle2,
  ShieldAlert,
  RotateCcw,
} from "lucide-react";

import { analyzeIncident } from "../services/api";

// Clearly labelled sample data for frontend demonstration
const demoResult = {
  incident_id: "INC-DEMO-1042",
  severity: "critical",
  root_cause: "Database connection pool exhaustion",
  explanation:
    "A sudden traffic spike caused the payment service to exceed its configured database connection pool limit.",
  recommendations: [
    "Inspect current database connection utilization.",
    "Verify available database connection capacity.",
    "Review the payment service connection pool configuration.",
    "Consider increasing the pool limit after capacity verification.",
    "Monitor payment requests after applying the approved fix.",
  ],
  confidence: "High",
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
        error: error.trim(),
        service,
        logs,
        severity,
      });

      if (!data || !data.analysis) {
        throw new Error("The backend did not return an AI analysis.");
      }

      setResult(data);
    } catch (err) {
      setMessage(
        err.response?.data?.detail ||
          err.message ||
          "Unable to analyze the incident. Please check the backend."
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
    setService("payment-service");
    setLogs("");
    setSeverity("critical");
    setResult(null);
    setMessage("");
    setDemoMode(false);
  };

  const liveAnalysis =
    !demoMode && typeof result?.analysis === "string"
      ? result.analysis
      : null;

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
            Describe a production issue. IncidentIQ will
            search historical knowledge and help identify
            possible solutions.
          </p>
        </div>

        <button className="secondary-btn" onClick={clearForm}>
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
              <option value="payment-service">Payment Service</option>
              <option value="authentication-service">
                Authentication Service
              </option>
              <option value="order-service">Order Service</option>
              <option value="database">Database</option>
              <option value="redis">Redis Cache</option>
              <option value="api-gateway">API Gateway</option>
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

          <button className="secondary-btn" onClick={loadDemo}>
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
                Incident ID:{" "}
                {result.incident_id ||
                  result.incident?.incident_id ||
                  "New Incident"}
              </p>
            </div>

            <span className="result-mode">
              {demoMode ? "DEMO DATA" : "LIVE RESPONSE"}
            </span>
          </div>

          {liveAnalysis ? (
            <div className="result-section live-analysis-card">
              <div className="result-section-heading">
                <div>
                  <h3>
                    <CheckCircle2 size={18} />
                    Complete AI Investigation Report
                  </h3>

                  <p>
                    Generated using historical incident knowledge
                    and AI analysis.
                  </p>
                </div>
              </div>

              <div className="markdown-report">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {liveAnalysis}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <>
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

                <h3>{result.root_cause || "Analysis completed"}</h3>

                <p>{result.explanation || "No explanation returned."}</p>

                <div className="root-cause-bottom">
                  <span>
                    Confidence: {result.confidence || "Not provided"}
                  </span>
                </div>
              </div>

              <div className="result-section recommendations-card">
                <div className="result-section-heading">
                  <div>
                    <h3>
                      <CheckCircle2 size={18} />
                      Recommended Resolution Steps
                    </h3>

                    <p>
                      Review these steps before making production
                      changes.
                    </p>
                  </div>
                </div>

                {result.recommendations?.length > 0 ? (
                  <div className="recommendation-list">
                    {result.recommendations.map((step, index) => (
                      <div className="recommendation-item" key={index}>
                        <span>{index + 1}</span>
                        <p>{step}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="empty-state">
                    No recommendations returned.
                  </p>
                )}
              </div>
            </>
          )}

          <div className="safety-notice">
            <ShieldAlert size={18} />
            <p>
              AI recommendations require engineer review. Verify
              system capacity and operational safety before
              executing production changes.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
