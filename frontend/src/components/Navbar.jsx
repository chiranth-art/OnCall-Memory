
import { Bell, Search, ChevronDown } from "lucide-react";

export default function Navbar({ activePage }) {
  return (
    <header className="navbar">

      <div className="navbar-heading">
        <h1>{activePage}</h1>
        <p>
          Welcome back, Arjun. Here's your operations overview.
        </p>
      </div>

      <div className="navbar-actions">

        <div className="system-indicator">
          <span className="status-dot"></span>
          All systems operational
        </div>

        <button className="navbar-icon" title="Search">
          <Search size={19} />
        </button>

        <button className="navbar-icon" title="Notifications">
          <Bell size={19} />
          <span className="notification-dot"></span>
        </button>

        <div className="navbar-profile">
          <div className="profile-avatar">A</div>

          <div className="profile-details">
            <strong>Arjun Kumar</strong>
            <span>Administrator</span>
          </div>

          <ChevronDown size={16} />
        </div>

      </div>

    </header>
  );
}
