
import { ArrowUpRight } from "lucide-react";

const incidents = [
  {
    id: "INC-1042",
    service: "Payment Service",
    issue: "Database connection timeout",
    severity: "Critical",
    status: "Resolved",
    time: "09:42 PM"
  },
  {
    id: "INC-1041",
    service: "Authentication",
    issue: "Redis memory exhaustion",
    severity: "High",
    status: "Investigating",
    time: "08:30 PM"
  },
  {
    id: "INC-1040",
    service: "Order Service",
    issue: "API gateway timeout",
    severity: "Medium",
    status: "Resolved",
    time: "07:15 PM"
  },
  {
    id: "INC-1039",
    service: "Database",
    issue: "Connection limit exceeded",
    severity: "High",
    status: "Resolved",
    time: "06:20 PM"
  }
];

export default function IncidentTable() {
  return (
    <div className="incident-table-card">

      <div className="table-heading">
        <div>
          <h3>Recent Incidents</h3>
          <p>Latest production incident activity</p>
        </div>

        <button className="view-all-btn">
          View all <ArrowUpRight size={16} />
        </button>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>INCIDENT</th>
              <th>SERVICE</th>
              <th>ISSUE</th>
              <th>SEVERITY</th>
              <th>STATUS</th>
              <th>TIME</th>
            </tr>
          </thead>

          <tbody>
            {incidents.map((incident) => (
              <tr key={incident.id}>
                <td className="incident-id">
                  {incident.id}
                </td>

                <td>{incident.service}</td>

                <td>{incident.issue}</td>

                <td>
                  <span
                    className={`severity ${incident.severity.toLowerCase()}`}
                  >
                    {incident.severity}
                  </span>
                </td>

                <td>
                  <span
                    className={`incident-status ${incident.status.toLowerCase()}`}
                  >
                    {incident.status}
                  </span>
                </td>

                <td>{incident.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}
