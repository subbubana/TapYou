// src/pages/StatisticsPage.js
import React from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import '../App.css';

function StatisticsPage() {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content-area flex-container">
        <Header />
        <div className="statistics-page-container">
          <h2>Statistics</h2>
          <p>Statistics page coming soon...</p>
        </div>
      </div>
    </div>
  );
}

export default StatisticsPage; 