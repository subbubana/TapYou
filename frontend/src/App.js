// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import PrivateRoute from './auth/PrivateRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TodoListPage from './pages/TodoListPage';
import PlannerPage from './pages/PlannerPage';
import StatisticsPage from './pages/StatisticsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="App">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
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
                  <PlannerPage />
                </PrivateRoute>
              }
            />
          <Route
            path="/chat"
            element={
              <PrivateRoute>
                  <PlannerPage />
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
            {/* Redirect root to /planner if authenticated, otherwise to /login */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                  <Navigate to="/planner" replace />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} /> {/* Catch-all for unknown routes */}
        </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;