import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import Message from '../components/Message';
import ChatInput from '../components/ChatInput';
import { useAuth } from '../auth/AuthContext';
import { chatHistory as chatApi } from '../api';
import './PlannerPage.css';
import '../App.css';

function PlannerPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [lastMessageId, setLastMessageId] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);
  const [waitingForAI, setWaitingForAI] = useState(false);
  const messagesEndRef = useRef(null);

  // Function to scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Function to fetch chat history
  const loadChatHistory = useCallback(async () => {
    console.log('loadChatHistory called with user:', user);
    console.log('user_id type:', typeof user?.user_id);
    console.log('user_id value:', user?.user_id);
    
    if (!user?.user_id) {
      console.log('User object:', user);
      console.log('User ID is missing:', user?.user_id);
      return;
    }

    setLoading(true);
    try {
      console.log('Fetching chat history for user:', user.user_id);
      const chatHistory = await chatApi.getChatHistory(user.user_id);
      console.log('Chat history received:', chatHistory);
      console.log('Number of messages:', chatHistory.length);
      
      if (chatHistory.length > 0) {
        console.log('First message:', chatHistory[0]);
        console.log('Last message:', chatHistory[chatHistory.length - 1]);
      }
      
      setMessages(chatHistory);
      
      // Update last message ID for auto-refresh
      if (chatHistory.length > 0) {
        setLastMessageId(chatHistory[chatHistory.length - 1].message_id);
        console.log('Set last message ID:', chatHistory[chatHistory.length - 1].message_id);
      }
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, [user?.user_id]);

  // Function to check for new messages (for general polling)
  const checkForNewMessages = useCallback(async () => {
    if (!user?.user_id || !lastMessageId) return;

    try {
      const chatHistory = await chatApi.getChatHistory(user.user_id);
      
      // Check if there are new messages
      if (chatHistory.length > 0) {
        const latestMessageId = chatHistory[chatHistory.length - 1].message_id;
        
        if (latestMessageId !== lastMessageId) {
          // New messages found, add only the new ones to existing state
          setMessages(prev => {
            // Find messages that are not already in the UI
            const newMessages = chatHistory.filter(dbMsg => 
              !prev.some(uiMsg => uiMsg.message_id === dbMsg.message_id)
            );
            
            if (newMessages.length > 0) {
              console.log('Adding new messages to UI:', newMessages.length);
              return [...prev, ...newMessages];
            }
            
            return prev;
          });
          setLastMessageId(latestMessageId);
        }
      }
    } catch (error) {
      console.error('Failed to check for new messages:', error);
    }
  }, [user?.user_id, lastMessageId]);

  // Function to poll for AI response
  const pollForAIResponse = useCallback(async (userMessageId, timeoutMs = 30000) => {
    console.log('Starting AI response polling for user message:', userMessageId);
    const startTime = Date.now();
    const pollInterval = 2000; // Poll every 2 seconds
    
    const poll = async () => {
      try {
        console.log('Polling for AI response...');
        const chatHistory = await chatApi.getChatHistory(user.user_id);
        console.log('Polling found', chatHistory.length, 'messages');
        
        // Look for AI message that came after our user message
        const aiMessage = chatHistory.find(msg => 
          !msg.is_user && 
          msg.message_id !== userMessageId &&
          new Date(msg.timestamp) > startTime
        );
        
        if (aiMessage) {
          console.log('AI response found:', aiMessage.content.substring(0, 50) + '...');
          // AI response found, stop polling
          setMessages(prev => {
            // Remove any temporary messages and add the real AI message
            const filtered = prev.filter(msg => msg.message_id !== 'temp-ai-response');
            return [...filtered, aiMessage];
          });
          setLastMessageId(aiMessage.message_id);
          setWaitingForAI(false);
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
          return true;
        }
        
        // Check timeout
        if (Date.now() - startTime > timeoutMs) {
          console.log('AI response timeout reached');
          // Timeout reached, add default response
          const defaultResponse = {
            message_id: Date.now().toString(),
            content: "I'm sorry, I'm taking longer than expected to respond. Please try again in a moment.",
            is_user: false,
            is_agent: true,
            timestamp: new Date().toISOString()
          };
          
          setMessages(prev => {
            const filtered = prev.filter(msg => msg.message_id !== 'temp-ai-response');
            return [...filtered, defaultResponse];
          });
          setLastMessageId(defaultResponse.message_id);
          setWaitingForAI(false);
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
          return true;
        }
        
        return false; // Continue polling
      } catch (error) {
        console.error('Failed to poll for AI response:', error);
        return false;
      }
    };
    
    // Start polling
    const interval = setInterval(async () => {
      const shouldStop = await poll();
      if (shouldStop) {
        clearInterval(interval);
      }
    }, pollInterval);
    
    setPollingInterval(interval);
    
    // Initial poll
    await poll();
  }, [user?.user_id, pollingInterval]);

  // Function to send a new message
  const handleSendMessage = async (messageText) => {
    if (!messageText.trim() || !user?.user_id) return;

    setSending(true);
    setWaitingForAI(true);
    
    // Add user message to local state immediately for better UX
    const userMessage = {
      message_id: Date.now().toString(),
      content: messageText,
      is_user: true,
      is_agent: false,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setLastMessageId(userMessage.message_id);
    
    try {
      // Send user message to backend
      console.log('Sending message to backend:', messageText);
      const response = await chatApi.sendUserMessage(messageText, user.user_id);
      console.log('Backend response:', response);
      
      // If we get a successful response, the agent message should be included
      if (response && response.agent_response) {
        const agentMessage = {
          message_id: response.message_id || Date.now().toString(),
          content: response.agent_response,
          is_user: false,
          is_agent: true,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, agentMessage]);
        setLastMessageId(agentMessage.message_id);
        setWaitingForAI(false);
      } else {
        // No immediate response, start polling for AI response
        console.log('No immediate agent response, starting polling...');
        await pollForAIResponse(userMessage.message_id);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      console.log('Error details:', error.message);
      
      // Even if the POST request fails, the user message might still be stored
      // Let's poll for any new messages that might have been added
      console.log('POST failed, but checking if user message was stored...');
      
      // Wait a moment and then check for new messages
      setTimeout(async () => {
        try {
          const chatHistory = await chatApi.getChatHistory(user.user_id);
          console.log('Polling after POST failure, found messages:', chatHistory.length);
          
          if (chatHistory.length > 0) {
            // Check if our user message is in the database
            const ourUserMessage = chatHistory.find(msg => 
              msg.is_user && msg.content === messageText
            );
            
            if (ourUserMessage) {
              console.log('User message found in database, updating local state');
              // Update our local message with the real database ID
              setMessages(prev => prev.map(msg => 
                msg.content === messageText && msg.is_user 
                  ? { ...msg, message_id: ourUserMessage.message_id }
                  : msg
              ));
              
              // Check for any agent response
              const agentMessage = chatHistory.find(msg => 
                !msg.is_user && new Date(msg.timestamp) > new Date(ourUserMessage.timestamp)
              );
              
              if (agentMessage) {
                console.log('Agent message found in database');
                setMessages(prev => [...prev, agentMessage]);
                setLastMessageId(agentMessage.message_id);
                setWaitingForAI(false);
              } else {
                console.log('No agent message yet, continuing to poll...');
                await pollForAIResponse(ourUserMessage.message_id);
              }
            } else {
              console.log('User message not found in database, adding error message');
              // Add error message
              const errorMessage = {
                message_id: Date.now().toString(),
                content: "Sorry, I couldn't send your message. Please try again.",
                is_user: false,
                is_agent: true,
                timestamp: new Date().toISOString()
              };
              setMessages(prev => [...prev, errorMessage]);
              setWaitingForAI(false);
            }
          }
        } catch (pollError) {
          console.error('Failed to poll after POST error:', pollError);
          const errorMessage = {
            message_id: Date.now().toString(),
            content: "Sorry, I couldn't send your message. Please try again.",
            is_user: false,
            is_agent: true,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMessage]);
          setWaitingForAI(false);
        }
      }, 1000); // Wait 1 second before polling
    } finally {
      setSending(false);
    }
  };

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory();
  }, [loadChatHistory]);

  // Set up auto-refresh polling (check every 5 seconds, but only when not waiting for AI)
  useEffect(() => {
    if (!waitingForAI) {
      const interval = setInterval(checkForNewMessages, 5000);
      return () => clearInterval(interval);
    }
  }, [checkForNewMessages, waitingForAI]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content-area flex-container">
        <Header />
        <div className="planner-page-container">
          <div className="chat-window-container flex-container">
            <div className="messages-display">
              {loading ? (
                <div className="loading-message">Loading chat history...</div>
              ) : messages.length === 0 ? (
                <div className="no-messages-message">No messages yet. Start a conversation!</div>
              ) : (
                <>
                  {messages.map(msg => (
                    <Message 
                      key={msg.message_id} 
                      text={msg.content} 
                      type={msg.is_user ? 'user' : 'agent'} 
                    />
                  ))}
                  {waitingForAI && (
                    <div className="typing-indicator">
                      <div className="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <span>AI is thinking...</span>
                    </div>
                  )}
                  <div ref={messagesEndRef} /> {/* Invisible element to scroll to */}
                </>
              )}
            </div>
            <ChatInput onSendMessage={handleSendMessage} disabled={sending || waitingForAI} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlannerPage; 