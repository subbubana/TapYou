// src/pages/AnalyticsPage.js
import React from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import '../App.css';

function AnalyticsPage() {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content-area flex-container">
        <Header />
        <div className="analytics-page-container">
          <h2>Analytics</h2>
          <p>Analytics page coming soon...</p>
        </div>
      </div>
    </div>
  );
}

export default AnalyticsPage; 