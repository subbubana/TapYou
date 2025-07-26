import React from 'react';
import './Message.css'; // Path remains relative

function Message({ text, type }) { // type can be 'user' or 'agent'
  const messageClass = type === 'user' ? 'user-message' : 'agent-message';

  return (
    <div className={`message-container ${messageClass}`}>
      <div className="message-bubble">
        <p>{text}</p>
      </div>
    </div>
  );
}

export default Message;