import React from 'react';
import './Sidebar.css'; // Path remains relative because Sidebar.css is next to Sidebar.js
import { useAuth } from '../auth/AuthContext'; // Import useAuth to handle logout

function Sidebar() {
  const { logout } = useAuth(); // Get the logout function from context

  return (
    <div className="sidebar-container">
      <div className="sidebar-header">
        <h1>TapYou</h1>
      </div>
      <nav className="sidebar-nav">
        <ul>
          <li className="nav-item active">ToDo List</li> {/* This will eventually be a Link */}
          <li className="nav-item">Planner</li>
          <li className="nav-item">Statistics</li>
          <li className="nav-item">Analytics</li>
        </ul>
      </nav>
      <div className="sidebar-footer">
        <button className="logout-button" onClick={logout}> {/* Add onClick handler */}
          <span className="icon">→</span> Log out
        </button>
      </div>
    </div>
  );
}

export default Sidebar;