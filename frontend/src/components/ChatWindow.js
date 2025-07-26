import React from 'react';
import Message from './Message';
import ChatInput from './ChatInput';
import './ChatWindow.css'; // Path remains relative

function ChatWindow() {
  // Dummy messages for visual replication
  const messages = [
    { id: 1, text: "This is a place holder for user messages. This window will show messages in the chat", type: 'user' },
    { id: 2, text: "This will contain the responses from the agent. The color can be changed later on but user can discuss anything here. We need to add persistence to the agent interaction.", type: 'agent' },
  ];

  return (
    <div className="chat-window-container flex-container">
      <div className="messages-display">
        {messages.map(msg => (
          <Message key={msg.id} text={msg.text} type={msg.type} />
        ))}
      </div>
      <ChatInput />
    </div>
  );
}

export default ChatWindow;