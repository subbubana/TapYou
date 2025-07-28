import React, { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { login as apiLogin } from '../api/auth';
import { Link } from 'react-router-dom'; // Import Link for registration link
import './LoginPage.css';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const data = await apiLogin(username, password);
      login(data.access_token, { username: data.username, user_id: data.user_id });
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
        <div className="register-link">
          Don't have an account? <Link to="/register">Register here</Link>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;