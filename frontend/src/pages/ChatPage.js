// src/pages/ChatPage.js
import React from 'react';
import Sidebar from '../components/Sidebar'; // Adjust path
import Header from '../components/Header';   // Adjust path
import ChatWindow from '../components/ChatWindow'; // Adjust path
import '../App.css'; // Keep the App.css for overall layout

function ChatPage() {
  return (
    <div className="app-container"> {/* This ensures the flex layout from App.css */}
      <Sidebar />
      <div className="main-content-area flex-container">
        <Header />
        <ChatWindow />
      </div>
    </div>
  );
}

export default ChatPage;