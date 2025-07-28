import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css'; // Path remains relative because Sidebar.css is next to Sidebar.js
import { useAuth } from '../auth/AuthContext'; // Import useAuth to handle logout

function Sidebar() {
  const { logout } = useAuth(); // Get the logout function from context
  const location = useLocation(); // Get current location to highlight active nav item

  return (
    <div className="sidebar-container">
      <div className="sidebar-header">
        <h1>TapYou</h1>
      </div>
      <nav className="sidebar-nav">
        <ul>
          <li className={`nav-item ${location.pathname === '/todo' ? 'active' : ''}`}>
            <Link to="/todo">ToDo List</Link>
          </li>
          <li className={`nav-item ${location.pathname === '/planner' ? 'active' : ''}`}>
            <Link to="/planner">Planner</Link>
          </li>
          <li className={`nav-item ${location.pathname === '/statistics' ? 'active' : ''}`}>
            <Link to="/statistics">Statistics</Link>
          </li>
          <li className={`nav-item ${location.pathname === '/analytics' ? 'active' : ''}`}>
            <Link to="/analytics">Analytics</Link>
          </li>
        </ul>
      </nav>
      <div className="sidebar-footer">
        <button className="logout-button" onClick={logout}> {/* Add onClick handler */}
          <span className="icon">←</span> Log out
        </button>
      </div>
    </div>
  );
}

export default Sidebar;