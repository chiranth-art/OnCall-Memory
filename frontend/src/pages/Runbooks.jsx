
import { useState } from "react";

import {
  BookOpen,
  Search,
  Database,
  Server,
  ShieldCheck,
  ChevronDown,
  ChevronUp
} from "lucide-react";

const runbooks = [
  {
    id: "RB-001",
    title: "Database Connection Pool Recovery",
    category: "Database",
    description:
      "Investigate database connection exhaustion and connection timeout errors.",
    steps: [
      "Check active database connections.",
      "Inspect application connection pool utilization.",
      "Identify services creating excessive connections.",
      "Verify database capacity and connection limits.",
      "Apply an approved connection pool configuration change.",
      "Monitor application requests and database health."
    ]
  },
  {
    id: "RB-002",
    title: "Redis Memory Recovery",
    category: "Cache",
    description:
      "Investigate Redis memory exhaustion and cache-related failures.",
    steps: [
      "Inspect Redis memory utilization.",
      "Identify high-memory keys.",
      "Review cache expiration policies.",
      "Verify available memory capacity.",
      "Apply approved cache configuration changes.",
      "Monitor cache performance."
    ]
  },
  {
    id: "RB-003",
    title: "API Gateway Timeout Recovery",
    category: "API",
    description:
      "Investigate API gateway timeouts and slow request processing.",
    steps: [
      "Inspect gateway request latency.",
      "Check upstream service health.",
      "Review request timeout configuration.",
      "Identify slow downstream dependencies.",
      "Apply approved configuration changes.",
      "Verify successful request processing."
    ]
  }
];

export default function Runbooks() {
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(null);

  const filtered = runbooks.filter((book) =>
    `${book.title} ${book.category} ${book.description}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  const icons = {
    Database,
    Cache: Server,
    API: ShieldCheck
  };

  return (
    <div className="runbooks-page">

      <div className="page-intro">
        <div>
          <span className="section-eyebrow">
            <BookOpen size={15} />
            OPERATIONAL KNOWLEDGE
          </span>

          <h2>Runbooks</h2>

          <p>
            Troubleshooting procedures for common
            production incidents.
          </p>
        </div>
      </div>

      <div className="history-search runbook-search">
        <Search size={18} />

        <input
          placeholder="Search runbooks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="runbook-list">

        {filtered.map((book) => {
          const Icon = icons[book.category] || BookOpen;
          const isExpanded = expanded === book.id;

          return (
            <div className="runbook-card" key={book.id}>

              <div className="runbook-top">

                <div className="runbook-icon">
                  <Icon size={22} />
                </div>

                <div className="runbook-title">
                  <span>{book.id} · {book.category}</span>
                  <h3>{book.title}</h3>
                  <p>{book.description}</p>
                </div>

                <button
                  className="expand-btn"
                  onClick={() =>
                    setExpanded(isExpanded ? null : book.id)
                  }
                  aria-label="Toggle runbook steps"
                >
                  {isExpanded
                    ? <ChevronUp size={19} />
                    : <ChevronDown size={19} />
                  }
                </button>

              </div>

              {isExpanded && (
                <div className="runbook-steps">

                  <h4>Resolution checklist</h4>

                  {book.steps.map((step, index) => (
                    <div className="runbook-step" key={index}>
                      <span>{index + 1}</span>
                      <p>{step}</p>
                    </div>
                  ))}

                  <div className="safety-notice">
                    <ShieldCheck size={18} />
                    <p>
                      Follow your organization's approved
                      operational procedures. Verify impact
                      before applying production changes.
                    </p>
                  </div>

                </div>
              )}

            </div>
          );
        })}

        {filtered.length === 0 && (
          <p className="empty-state">No runbooks found.</p>
        )}

      </div>

    </div>
  );
}
