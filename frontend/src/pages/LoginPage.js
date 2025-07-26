// src/pages/LoginPage.js
import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { login as apiLogin } from '../api/auth'; // Renamed to avoid conflict
import './LoginPage.css'; // Create this CSS file

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Clear previous errors
    try {
      const data = await apiLogin(username, password);
      login(data.access_token, { username: data.username, user_id: data.user_id });
      // Redirection handled by AuthContext
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during login.');
    }
  };

  return (
    <div className="login-page-container">
      <div className="login-box">
        <h2>Login to TapYou</h2>
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="input-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" className="login-button">Login</button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;