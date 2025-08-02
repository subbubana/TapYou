import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './Message.css'; // Path remains relative

function Message({ text, type }) { // type can be 'user' or 'agent'
  const messageClass = type === 'user' ? 'user-message' : 'agent-message';

  return (
    <div className={`message-container ${messageClass}`}>
      <div className="message-bubble">
        {type === 'agent' ? (
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              // Custom styling for markdown elements
              p: ({children}) => <p style={{margin: '0 0 8px 0'}}>{children}</p>,
              h1: ({children}) => <h1 style={{margin: '16px 0 8px 0', fontSize: '1.5em'}}>{children}</h1>,
              h2: ({children}) => <h2 style={{margin: '14px 0 6px 0', fontSize: '1.3em'}}>{children}</h2>,
              h3: ({children}) => <h3 style={{margin: '12px 0 6px 0', fontSize: '1.1em'}}>{children}</h3>,
              ul: ({children}) => <ul style={{margin: '8px 0', paddingLeft: '20px'}}>{children}</ul>,
              ol: ({children}) => <ol style={{margin: '8px 0', paddingLeft: '20px'}}>{children}</ol>,
              li: ({children}) => <li style={{margin: '4px 0'}}>{children}</li>,
              code: ({children, className}) => {
                if (className) {
                  // Code block
                  return (
                    <pre style={{
                      backgroundColor: '#f6f8fa',
                      padding: '12px',
                      borderRadius: '6px',
                      overflow: 'auto',
                      margin: '8px 0'
                    }}>
                      <code>{children}</code>
                    </pre>
                  );
                }
                // Inline code
                return <code style={{
                  backgroundColor: '#f6f8fa',
                  padding: '2px 4px',
                  borderRadius: '3px',
                  fontSize: '0.9em'
                }}>{children}</code>;
              },
              blockquote: ({children}) => (
                <blockquote style={{
                  borderLeft: '4px solid #ddd',
                  margin: '8px 0',
                  paddingLeft: '12px',
                  color: '#666'
                }}>
                  {children}
                </blockquote>
              ),
              table: ({children}) => (
                <table style={{
                  borderCollapse: 'collapse',
                  width: '100%',
                  margin: '8px 0'
                }}>
                  {children}
                </table>
              ),
              th: ({children}) => (
                <th style={{
                  border: '1px solid #ddd',
                  padding: '8px',
                  backgroundColor: '#f6f8fa',
                  textAlign: 'left'
                }}>
                  {children}
                </th>
              ),
              td: ({children}) => (
                <td style={{
                  border: '1px solid #ddd',
                  padding: '8px'
                }}>
                  {children}
                </td>
              )
            }}
          >
            {text}
          </ReactMarkdown>
        ) : (
          <p>{text}</p>
        )}
      </div>
    </div>
  );
}

export default Message;