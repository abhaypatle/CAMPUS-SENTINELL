import React, { useState } from "react";

type Incident = {
  id: string;
  incident: string;
  status: string;
  risk: string;
  escalation: string;
  assigned: string;
  reports: number;
  updated: string;
};

const incidents: Incident[] = [
  {
    id: "INC-2024-0183",
    incident: "Smoke & Electrical Fault – Block A",
    status: "Responding",
    risk: "High Risk",
    escalation: "Escalating",
    assigned: "R. Chen",
    reports: 3,
    updated: "2 min ago",
  },
  {
    id: "INC-2024-0182",
    incident: "Unauthorised entry – Hostel Gate C",
    status: "Assigned",
    risk: "Medium Risk",
    escalation: "Normal",
    assigned: "A. Kumar",
    reports: 1,
    updated: "18 min ago",
  },
  {
    id: "INC-2024-0181",
    incident: "Medical emergency – Cafeteria",
    status: "Resolved",
    risk: "Low Risk",
    escalation: "Normal",
    assigned: "Campus Clinic",
    reports: 2,
    updated: "1 hr ago",
  },
  {
    id: "INC-2024-0180",
    incident: "Vandalism – Parking Bay B",
    status: "Under Review",
    risk: "Low Risk",
    escalation: "Normal",
    assigned: "Unassigned",
    reports: 1,
    updated: "2 hr ago",
  },
];

function App() {
  const [activeNav, setActiveNav] = useState("Command Center");
  const [search, setSearch] = useState("");

  const filteredIncidents = incidents.filter((item) =>
    `${item.id} ${item.incident} ${item.assigned}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="app-shell">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">♢</div>

          <div>
            <div className="brand-title">CAMPUS SENTINEL</div>
            <div className="brand-subtitle">SAFETY OPERATIONS</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${
              activeNav === "Command Center" ? "active" : ""
            }`}
            onClick={() => setActiveNav("Command Center")}
          >
            <span>⌘</span>
            Command Center
          </button>

          <div className="nav-section">INCIDENTS</div>

          <button className="nav-item">
            <span>♢</span>
            All Incidents
          </button>

          <button className="nav-item">
            <span>♨</span>
            Escalating
            <span className="nav-badge red">3</span>
          </button>

          <button className="nav-item">
            <span>⌘</span>
            Fusion Review
            <span className="nav-badge teal">AI</span>
          </button>

          <button className="nav-item">
            <span>☷</span>
            Assignments
          </button>

          <div className="nav-section">REPORTS & DATA</div>

          <button className="nav-item">
            <span>⌁</span>
            Analytics
          </button>

          <button className="nav-item">
            <span>▣</span>
            Audit Trail
          </button>

          <button className="nav-item">
            <span>⚙</span>
            Settings
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot green"></span>
            System Operational
          </div>

          <div className="user-card">
            <div className="avatar">KW</div>
            <div>
              <strong>K. Wong</strong>
              <small>Campus Admin</small>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main-area">
        {/* HEADER */}
        <header className="top-header">
          <div className="page-title">Campus Safety Command Center</div>

          <div className="header-actions">
            <div className="search-box">
              <span>⌕</span>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search incidents..."
              />
              <kbd>⌘K</kbd>
            </div>

            <div className="live-badge">
              <span></span>
              LIVE
            </div>

            <div className="notification">♧</div>

            <div className="header-user">
              <div className="avatar small">KW</div>
              <span>K. Wong</span>
              <span>⌄</span>
            </div>
          </div>
        </header>

        {/* TABS */}
        <div className="tabs">
          <button
            className={activeNav === "Command Center" ? "tab active" : "tab"}
            onClick={() => setActiveNav("Command Center")}
          >
            Command Center
          </button>

          <button className="tab">Design System</button>
        </div>

        <div className="content">
          {/* KPI CARDS */}
          <section className="stats-grid">
            <StatCard
              title="ACTIVE INCIDENTS"
              value="7"
              change="▼ 2 new today"
              type="blue"
              icon="♢"
            />

            <StatCard
              title="ESCALATING"
              value="3"
              change="▼ 1 in last hour"
              type="red"
              icon="♨"
            />

            <StatCard
              title="AI FUSIONS TODAY"
              value="4"
              change="AI-assisted"
              type="teal"
              icon="⌘"
            />

            <StatCard
              title="RESOLVED TODAY"
              value="12"
              change="▲ 1 vs yesterday"
              type="green"
              icon="✓"
            />
          </section>

          {/* INCIDENTS */}
          <section className="section">
            <div className="section-header">
              <h2>Recent Incidents</h2>
              <button className="view-all">View all →</button>
            </div>

            <div className="table-card">
              <div className="incident-table">
                <div className="table-row table-head">
                  <div>ID</div>
                  <div>Incident</div>
                  <div>Status</div>
                  <div>Risk</div>
                  <div>Escalation</div>
                  <div>Assigned To</div>
                  <div>Reports</div>
                  <div>Updated</div>
                </div>

                {filteredIncidents.map((item) => (
                  <div className="table-row" key={item.id}>
                    <div className="incident-id">{item.id}</div>

                    <div className="incident-name">
                      {item.incident}
                    </div>

                    <div>
                      <StatusBadge status={item.status} />
                    </div>

                    <div>
                      <RiskBadge risk={item.risk} />
                    </div>

                    <div>
                      <EscalationBadge
                        escalation={item.escalation}
                      />
                    </div>

                    <div>{item.assigned}</div>

                    <div>{item.reports}</div>

                    <div className="muted">{item.updated}</div>
                  </div>
                ))}
              </div>

              <div className="table-footer">
                <span>Showing 4 of 42 incidents</span>

                <div className="pagination">
                  <button className="page active">1</button>
                  <button className="page">2</button>
                  <button className="page">3</button>
                  <span>...</span>
                  <button className="page">11</button>
                </div>
              </div>
            </div>
          </section>

          {/* LOWER SECTION */}
          <section className="lower-grid">
            {/* AI CARD */}
            <div>
              <h2 className="lower-title">AI Intelligence Card</h2>
              <p className="lower-subtitle">
                Shown on incident detail view
              </p>

              <div className="ai-card">
                <div className="ai-card-header">
                  <div className="ai-label">
                    <span>▣</span>
                    AI ANALYSIS
                  </div>

                  <strong>84% confidence</strong>
                </div>

                <p className="ai-description">
                  Three reports likely describe one electrical-related
                  fire incident in Block A. Proximity and temporal
                  correlation indicate unified event.
                </p>

                <div className="ai-check">
                  <span>✓</span>
                  Spatial proximity: all reports within 40m radius
                </div>

                <div className="ai-check">
                  <span>✓</span>
                  Temporal overlap: submitted within 8-minute window
                </div>

                <div className="ai-check">
                  <span>✓</span>
                  Semantic match: smoke, burning, smell keywords
                </div>

                <div className="ai-check">
                  <span>✓</span>
                  Image evidence supports fire risk assessment
                </div>
              </div>
            </div>

            {/* ALERTS */}
            <div>
              <h2 className="lower-title">Alert Components</h2>

              <div className="alert critical">
                <div className="alert-icon">△</div>
                <div>
                  <strong>Critical Escalation Detected</strong>
                  <p>
                    INC-2024-0183 has exceeded escalation threshold.
                    Immediate human review required.
                  </p>
                </div>
              </div>

              <div className="alert warning">
                <div className="alert-icon">△</div>
                <div>
                  <strong>AI Fusion Pending Review</strong>
                  <p>
                    4 reports grouped into 1 unified incident. Please
                    confirm or reject the fusion.
                  </p>
                </div>
              </div>

              <div className="alert success">
                <div className="alert-icon">✓</div>
                <div>
                  <strong>Incident Resolved</strong>
                  <p>
                    INC-2024-0181 closed successfully. All parties
                    notified.
                  </p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function StatCard({
  title,
  value,
  change,
  type,
  icon,
}: {
  title: string;
  value: string;
  change: string;
  type: string;
  icon: string;
}) {
  return (
    <div className="stat-card">
      <div>
        <div className="stat-title">{title}</div>
        <div className="stat-value">{value}</div>
        <div className={`stat-change ${type}`}>{change}</div>
      </div>

      <div className={`stat-icon ${type}`}>{icon}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const className = status.toLowerCase().replace(" ", "-");

  return (
    <span className={`badge status ${className}`}>
      <i></i>
      {status}
    </span>
  );
}

function RiskBadge({ risk }: { risk: string }) {
  const className = risk.toLowerCase().replace(" ", "-");

  return (
    <span className={`badge risk ${className}`}>
      {risk}
    </span>
  );
}

function EscalationBadge({
  escalation,
}: {
  escalation: string;
}) {
  return (
    <span
      className={`badge escalation ${
        escalation === "Escalating" ? "danger" : ""
      }`}
    >
      {escalation === "Escalating" && "♨ "}
      {escalation}
    </span>
  );
}

export default App;