// TapYou/frontend/src/api/index.js
import { authenticatedFetch } from './auth'; // Import the authenticatedFetch wrapper
import { format } from 'date-fns'; // Import format for consistent date formatting

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

export const tasks = {
  // GET /tasks/user/{username}
  getTasks: async (username, status, targetDate, sort_by, sort_order, limit, offset) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    // Format date to YYYY-MM-DD string, as expected by FastAPI's date type hint
    if (targetDate) params.append('target_date', format(targetDate, 'yyyy-MM-dd'));
    if (sort_by) params.append('sort_by', sort_by);
    if (sort_order) params.append('sort_order', sort_order);
    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);

    const url = `${API_BASE_URL}/tasks/user/${username}?${params.toString()}`;
    return authenticatedFetch(url);
  },

  // PUT /tasks/{task_id} - Update task status or description
  updateTask: async (taskId, updates) => {
    const url = `${API_BASE_URL}/tasks/${taskId}`;
    return authenticatedFetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      // Backend PUT endpoint accepts task_description and/or current_status
      body: JSON.stringify(updates),
    });
  },



  // NEW: GET /tasks/user/{username}/counts
  getTaskCounts: async (username, targetDate) => {
    const params = new URLSearchParams();
    if (targetDate) params.append('target_date', format(targetDate, 'yyyy-MM-dd'));

    const url = `${API_BASE_URL}/tasks/user/${username}/counts?${params.toString()}`;
    return authenticatedFetch(url);
  },

  // You can add other task API calls here (createTask, deleteTask, etc.)
  createTask: async (task_description) => {
    const url = `${API_BASE_URL}/tasks/`;
    
    return authenticatedFetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ task_description }),
    });
  },

  // If you need deleteTask or deleteBatch from frontend:
  deleteTask: async (taskId) => {
    const url = `${API_BASE_URL}/tasks/${taskId}`;
    return authenticatedFetch(url, {
      method: 'DELETE',
    });
  },
  deleteTaskBatch: async (task_ids) => {
    const url = `${API_BASE_URL}/tasks/batch`;
    return authenticatedFetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ task_ids }),
    });
  },
};

export const users = {
  // Example: Get authenticated user's profile
  getUserProfile: async (username) => {
    const url = `${API_BASE_URL}/users/${username}`;
    return authenticatedFetch(url);
  },
};