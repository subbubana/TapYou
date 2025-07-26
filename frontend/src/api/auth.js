// src/api/auth.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

export const login = async (username, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
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