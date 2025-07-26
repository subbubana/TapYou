import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App'; // Import the new App.js
import './index.css'; // Global CSS

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);