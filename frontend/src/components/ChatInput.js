import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';

function ChatInput() {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      // Temporarily set height to 'auto' to correctly measure content
      textareaRef.current.style.height = 'auto';
      // Calculate max height for 4 lines based on computed line-height and padding
      const computedStyle = getComputedStyle(textareaRef.current);
      const lineHeight = parseFloat(computedStyle.lineHeight); // e.g., 24px
      const verticalPadding = parseFloat(computedStyle.paddingTop) + parseFloat(computedStyle.paddingBottom);
      const maxHeight = (lineHeight * 4) + verticalPadding;

      // Set height to scrollHeight, clamped by max height
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`;
    }
  }, [inputValue]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };

  const handleSendMessage = () => {
    if (inputValue.trim()) { // Only send if input is not empty
      console.log("Sending message:", inputValue);
      setInputValue(''); // Clear input after sending
      // After clearing, force height recalculation
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'; // Reset to auto to shrink
      }
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) { // Send on Enter, allow Shift+Enter for new line
      event.preventDefault(); // Prevent new line in textarea
      handleSendMessage();
    }
  };

  return (
    <div className="chat-input-container">
      <div className="chat-input-main-area">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
          placeholder="Start Adding Tasks"
          className="chat-text-input"
          rows="1" // Visual hint, but JS manages actual height
        ></textarea>
        <button className="send-button" onClick={handleSendMessage}>
          <span className="icon">▶</span> {/* Changed icon here (Black Right-Pointing Triangle) */}
        </button>
      </div>
    </div>
  );
}

export default ChatInput;