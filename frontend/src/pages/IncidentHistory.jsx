
import { useEffect, useState } from "react";

import {
  Search,
  History,
  RefreshCw,
  Database
} from "lucide-react";

import { getIncidents } from "../services/api";

const demoIncidents = [
  {
    id: "INC-001",
    service: "payment-service",
    symptoms: "Database connection timeout",
    root_cause: "Connection pool exhaustion",
    fix_worked: "Increased pool size to 200",
    minutes_to_resolve: 25
  },
  {
    id: "INC-002",
    service: "authentication-service",
    symptoms: "Repeated login failures",
    root_cause: "Redis memory exhaustion",
    fix_worked: "Increased Redis memory and added cache expiration",
    minutes_to_resolve: 40
  },
  {
    id: "INC-003",
    service: "order-service",
    symptoms: "API gateway timeout",
    root_cause: "High request processing latency",
    fix_worked: "Optimized request processing",
    minutes_to_resolve: 18
  }
];

export default function IncidentHistory() {
  const [incidents, setIncidents] = useState(demoIncidents);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(true);
  const [error, setError] = useState("");

  const loadIncidents = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getIncidents();

      const records = Array.isArray(data)
        ? data
        : data.incidents || [];

      setIncidents(records);
      setDemoMode(false);

    } catch {
      setIncidents(demoIncidents);
      setDemoMode(true);
      setError("Backend unavailable. Showing sample incident records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, []);

  const filtered = incidents.filter((incident) =>
    [
      incident.id,
      incident.incident_id,
      incident.service,
      incident.symptoms,
      incident.root_cause
    ]
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="history-page">

      <div className="page-intro">
        <div>
          <span className="section-eyebrow">
            <History size={15} />
            INCIDENT KNOWLEDGE BASE
          </span>

          <h2>Incident History</h2>

          <p>
            Search previous production incidents
            and review their resolutions.
          </p>
        </div>

        <button
          className="secondary-btn"
          onClick={loadIncidents}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="api-message">
          <Database size={17} />
          {error}
        </div>
      )}

      <div className="history-toolbar">

        <div className="history-search">
          <Search size={18} />

          <input
            placeholder="Search by ID, service, error or root cause..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <span className="result-mode">
          {demoMode ? "DEMO DATA" : "LIVE DATA"}
        </span>

      </div>

      <div className="history-list">

        {loading ? (
          <p className="empty-state">Loading incidents...</p>
        ) : filtered.length > 0 ? (
          filtered.map((incident, index) => (
            <div className="history-card" key={incident.id || incident.incident_id || index}>

              <div className="history-card-top">

                <div className="history-id">
                  <History size={17} />
                  {incident.id || incident.incident_id || `Incident ${index + 1}`}
                </div>

                <span className="service-tag">
                  {incident.service || "Unknown service"}
                </span>

              </div>

              <h3>
                {incident.symptoms || incident.error || "Incident details unavailable"}
              </h3>

              <div className="history-detail">
                <span>ROOT CAUSE</span>
                <p>
                  {incident.root_cause || "Not recorded"}
                </p>
              </div>

              <div className="history-detail">
                <span>SUCCESSFUL RESOLUTION</span>
                <p>
                  {incident.fix_worked || "Not recorded"}
                </p>
              </div>

              <div className="history-footer">
                <span>
                  <Database size={14} />
                  Historical memory
                </span>

                {incident.minutes_to_resolve != null && (
                  <span>
                    {incident.minutes_to_resolve} minutes to resolve
                  </span>
                )}
              </div>

            </div>
          ))
        ) : (
          <div className="empty-state">
            No matching incidents found.
          </div>
        )}

      </div>

    </div>
  );
}
