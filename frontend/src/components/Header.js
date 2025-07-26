import React from 'react';
import './Header.css'; // Path remains relative
// You might also want to import useAuth here to display the username
import { useAuth } from '../auth/AuthContext';

function Header() {
  const { user } = useAuth(); // Get user info from context

  return (
    <header className="header-container">
      <div className="header-logo">
        <h2>TapYou</h2>
      </div>
      <div className="header-user-info">
        {user && <span className="username-display">{user.username}</span>}
        <div className="user-avatar"></div>
      </div>
    </header>
  );
}

export default Header;