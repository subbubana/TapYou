import React from 'react';
import './ChatInput.css'; // Path remains relative

function ChatInput() {
  return (
    <div className="chat-input-container">
      <input
        type="text"
        placeholder="Start Adding Tasks"
        className="chat-text-input"
      />
      <button className="send-button">
        <span className="icon">▲</span> {/* Simple triangle icon */}
      </button>
    </div>
  );
}

export default ChatInput;