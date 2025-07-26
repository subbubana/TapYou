// src/auth/AuthContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null); // Stores {username, user_id}
  const navigate = useNavigate();

  useEffect(() => {
    // Check for token on initial load
    const token = Cookies.get('authToken');
    const storedUser = Cookies.get('currentUser');
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
        setIsAuthenticated(true);
      } catch (e) {
        console.error("Failed to parse stored user data:", e);
        logout(); // Clear invalid data
      }
    }
  }, []);

  const login = (token, userData) => {
    Cookies.set('authToken', token, { expires: 1 }); // Expires in 1 day
    Cookies.set('currentUser', JSON.stringify(userData), { expires: 1 });
    setUser(userData);
    setIsAuthenticated(true);
    navigate('/chat'); // Redirect to chat page on successful login
  };

  const logout = () => {
    Cookies.remove('authToken');
    Cookies.remove('currentUser');
    setUser(null);
    setIsAuthenticated(false);
    navigate('/login'); // Redirect to login page on logout
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);