
import {
  Zap,
  ArrowUpRight,
  Activity,
  Clock3,
  ShieldCheck
} from "lucide-react";

import StatCard from "../components/StatCard";
import IncidentTable from "../components/IncidentTable";

export default function Dashboard({ setActivePage }) {
  return (
    <div className="dashboard">

      {/* Welcome section */}
      <section className="welcome-section">
        <div>
          <span className="welcome-tag">
            <Zap size={14} /> AI-POWERED OPERATIONS
          </span>

          <h2>
            Good evening, Arjun <span>👋</span>
          </h2>

          <p>
            Monitor incidents, investigate failures and
            resolve production issues faster with AI.
          </p>
        </div>

        <button
          className="primary-btn"
          onClick={() => setActivePage("New Incident")}
        >
          <Zap size={17} />
          Analyze New Incident
        </button>
      </section>

      {/* Statistics */}
      <section className="stats-grid">

        <StatCard
          title="Active Incidents"
          value="03"
          description="2 critical · 1 high"
          type="alert"
        />

        <StatCard
          title="Resolved Incidents"
          value="128"
          description="Historical records"
          type="success"
        />

        <StatCard
          title="Avg. Resolution Time"
          value="12 min"
          description="Across recorded incidents"
          type="clock"
        />

        <StatCard
          title="AI Memory Records"
          value="245"
          description="Stored incident memories"
          type="memory"
        />

      </section>

      {/* Main content */}
      <section className="dashboard-content">

        <div className="main-column">

          <IncidentTable />

          <div className="insight-card">
            <div className="insight-icon">
              <Activity size={21} />
            </div>

            <div className="insight-content">
              <span>AI MEMORY INSIGHT</span>

              <h3>Learn from every incident</h3>

              <p>
                IncidentIQ uses historical incident
                knowledge to help engineers discover
                previously successful solutions.
              </p>

              <button
                onClick={() => setActivePage("Memory Insights")}
              >
                Explore memory insights
                <ArrowUpRight size={16} />
              </button>
            </div>
          </div>

        </div>

        {/* Right panel */}
        <aside className="dashboard-side">

          <div className="system-card">

            <div className="system-card-header">
              <ShieldCheck size={20} />
              <span>System Health</span>
            </div>

            <div className="system-health">
              <div className="health-dot"></div>
              Operational
            </div>

            <p>
              This is the current dashboard's
              illustrative system status.
            </p>

            <div className="system-divider"></div>

            <div className="system-metric">
              <span>Monitoring</span>
              <strong>Active</strong>
            </div>

            <div className="system-metric">
              <span>AI Memory</span>
              <strong>Configured</strong>
            </div>

            <div className="system-metric">
              <span>Incident Engine</span>
              <strong>Ready</strong>
            </div>

          </div>

          <div className="quick-action-card">
            <div className="quick-action-icon">
              <Clock3 size={20} />
            </div>

            <h3>Need help resolving an incident?</h3>

            <p>
              Let AI investigate historical incidents
              and suggest evidence-based solutions.
            </p>

            <button
              onClick={() => setActivePage("New Incident")}
            >
              Start investigation
              <ArrowUpRight size={16} />
            </button>
          </div>

        </aside>

      </section>

      <footer className="dashboard-footer">
        IncidentIQ · Intelligent Incident Response
        <span>Hackathon MVP · Demo environment</span>
      </footer>

    </div>
  );
}
