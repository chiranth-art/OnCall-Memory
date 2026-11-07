
import { useState } from "react";

import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";

import Dashboard from "./pages/Dashboard";
import NewIncident from "./pages/NewIncident";
import IncidentHistory from "./pages/IncidentHistory";
import MemoryInsights from "./pages/MemoryInsights";
import Runbooks from "./pages/Runbooks";

import "./App.css";

function App() {
  const [activePage, setActivePage] = useState("Dashboard");

  const renderPage = () => {
    switch (activePage) {

      case "Dashboard":
        return (
          <Dashboard setActivePage={setActivePage} />
        );

      case "New Incident":
        return <NewIncident />;

      case "Incident History":
        return <IncidentHistory />;

      case "Memory Insights":
        return <MemoryInsights />;

      case "Runbooks":
        return <Runbooks />;

      case "Settings":
        return (
          <div className="coming-soon">
            <h2>Settings</h2>
            <p>Application settings will be available soon.</p>
          </div>
        );

      default:
        return (
          <Dashboard setActivePage={setActivePage} />
        );
    }
  };

  return (
    <div className="app-layout">

      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
      />

      <main className="main-layout">

        <Navbar activePage={activePage} />

        <div className="page-content">
          {renderPage()}
        </div>

      </main>

    </div>
  );
}

export default App;
