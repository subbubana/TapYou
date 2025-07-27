// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext'; // Import AuthProvider and useAuth
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import TodoListPage from './pages/TodoListPage';
import StatisticsPage from './pages/StatisticsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import './index.css'; // Global styles for body/root, etc.
import './App.css'; // Overall flex layout (app-container, main-content-area)

// A simple component to protect routes
const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <AuthProvider> {/* Wrap the entire application with AuthProvider */}
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/todo"
            element={
              <PrivateRoute>
                <TodoListPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/planner"
            element={
              <PrivateRoute>
                <ChatPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <PrivateRoute>
                <ChatPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/statistics"
            element={
              <PrivateRoute>
                <StatisticsPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <PrivateRoute>
                <AnalyticsPage />
              </PrivateRoute>
            }
          />
          {/* Redirect root to /todo if authenticated, otherwise to /login */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Navigate to="/todo" replace />
              </PrivateRoute>
            }
          />
          {/* Add more protected routes here for other pages like /todo, /planner */}
          <Route path="*" element={<Navigate to="/login" replace />} /> {/* Catch-all for unknown routes */}
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;