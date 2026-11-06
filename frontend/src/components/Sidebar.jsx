
import {
  LayoutDashboard,
  AlertCircle,
  History,
  Brain,
  BookOpen,
  Settings,
  Activity,
  ChevronLeft
} from "lucide-react";

const menuItems = [
  {
    name: "Dashboard",
    icon: LayoutDashboard
  },
  {
    name: "New Incident",
    icon: AlertCircle
  },
  {
    name: "Incident History",
    icon: History
  },
  {
    name: "Memory Insights",
    icon: Brain
  },
  {
    name: "Runbooks",
    icon: BookOpen
  }
];

export default function Sidebar({
  activePage,
  setActivePage
}) {
  return (
    <aside className="sidebar">

      <div className="sidebar-logo">
        <div className="logo-icon">
          <Activity size={23} />
        </div>

        <div>
          <h2>IncidentIQ</h2>
          <span>INTELLIGENT OPERATIONS</span>
        </div>
      </div>

      <div className="sidebar-section">
        <p className="sidebar-label">WORKSPACE</p>

        <nav className="sidebar-nav">
          {menuItems.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.name}
                className={`nav-item ${
                  activePage === item.name
                    ? "active"
                    : ""
                }`}
                onClick={() =>
                  setActivePage(item.name)
                }
              >
                <Icon size={19} />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="sidebar-bottom">

        <button
          className="nav-item"
          onClick={() => setActivePage("Settings")}
        >
          <Settings size={19} />
          <span>Settings</span>
        </button>

        <div className="sidebar-status">
          <span className="status-dot"></span>
          <span>Systems operational</span>
        </div>

        <div className="sidebar-user">
          <div className="user-avatar">A</div>

          <div className="user-info">
            <strong>Arjun Kumar</strong>
            <span>On-call Engineer</span>
          </div>

          <ChevronLeft size={17} />
        </div>

      </div>

    </aside>
  );
}
