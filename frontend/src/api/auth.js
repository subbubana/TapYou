// src/api/auth.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

// Function to get the auth token from cookies
const getAuthToken = () => {
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i].trim();
    if (cookie.startsWith('authToken=')) {
      return cookie.substring('authToken='.length, cookie.length);
    }
  }
  return null;
};

export const login = async (username, password) => {
  try {
    // For OAuth2PasswordRequestForm, FastAPI expects x-www-form-urlencoded
    // For our simplified model, we still send JSON, but the backend is designed
    // to pick it up from a form or JSON body in login_user.
    // The OAuth2PasswordRequestForm expects 'username' and 'password' as form fields.
    // Let's adjust frontend to send FormData to match OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded', // Change content type
      },
      body: formData.toString(), // Send as URL-encoded string
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed.');
    }

    const data = await response.json();
    return data; // Contains access_token, token_type, username, user_id
  } catch (error) {
    console.error('API login error:', error);
    throw error;
  }
};

// Generic authenticated API call wrapper
export const authenticatedFetch = async (url, options = {}) => {
  const token = getAuthToken();
  if (!token) {
    // Handle unauthenticated state, e.g., redirect to login
    console.error("No authentication token found. Redirecting to login.");
    // This is where you might trigger a logout or redirect if not already handled by AuthContext
    window.location.href = '/login'; // Simple redirect for now
    throw new Error("Authentication required.");
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      // Token expired or invalid, or unauthorized. Trigger logout.
      console.error("Authentication failed or token expired. Logging out.");
      // This logic should ideally be centralized in AuthContext or an Axios interceptor
      window.location.href = '/login'; // Simple redirect for now
    }
    const errorData = await response.json();
    throw new Error(errorData.detail || `API error: ${response.status}`);
  }

  return response.json();
};