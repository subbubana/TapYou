// src/pages/TodoListPage.js
import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import TaskCard from '../components/TaskCard';
import TaskStatusModal from '../components/TaskStatusModel';
import { useAuth } from '../auth/AuthContext';
import { format, subDays, addDays } from 'date-fns'; // For date manipulation
import './TodoListPage.css'; // Create this CSS file
import '../App.css'; // Keep the App.css for overall layout

// Dummy API functions (will be replaced with actual fetch calls later)
const fetchTasks = async (username, date, statusFilter) => {
  console.log(`Fetching tasks for ${username} on ${format(date, 'yyyy-MM-dd')} with filter: ${statusFilter}`);
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 500));

  // --- Placeholder Logic ---
  const allDummyTasks = [
    { id: '1', user_id: 'user1', task_description: 'Call Bunny tomorrow', current_status: 'active', created_at: '2025-07-26T10:00:00Z', modified_at: '2025-07-26T10:00:00Z', pushed_from_past: false },
    { id: '2', user_id: 'user1', task_description: 'Work on TapYou backend', current_status: 'completed', created_at: '2025-07-25T09:30:00Z', modified_at: '2025-07-25T15:00:00Z', pushed_from_past: false },
    { id: '3', user_id: 'user1', task_description: 'Go to Walmart for groceries', current_status: 'active', created_at: '2025-07-26T11:00:00Z', modified_at: '2025-07-26T11:00:00Z', pushed_from_past: false },
    { id: '4', user_id: 'user1', task_description: 'Review agent design doc', current_status: 'backlog', created_at: '2025-07-20T14:00:00Z', modified_at: '2025-07-22T09:00:00Z', pushed_from_past: true },
    { id: '5', user_id: 'user2', task_description: 'Team meeting agenda', current_status: 'active', created_at: '2025-07-26T16:00:00Z', modified_at: '2025-07-26T16:00:00Z', pushed_from_past: false },
  ];

  // Filter by user (assuming user1 for current demo)
  const userTasks = allDummyTasks.filter(task => task.user_id === 'user1'); // Replace with actual user.user_id

  // Filter by date (simple check: if task created "today" or not for backlog)
  const filteredByDate = userTasks.filter(task => {
    const taskDate = new Date(task.created_at);
    // For simplicity, tasks "for today" are ones created today or pushed from past
    // A real implementation would involve 'due_date' or more complex date ranges
    return format(taskDate, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd') || task.pushed_from_past;
  });


  // Apply status filter
  if (statusFilter === 'active') {
    return filteredByDate.filter(task => task.current_status === 'active' || task.current_status === 'pending');
  } else if (statusFilter === 'completed') {
    return filteredByDate.filter(task => task.current_status === 'completed');
  } else if (statusFilter === 'backlog') {
    return filteredByDate.filter(task => task.current_status === 'backlog' || task.pushed_from_past);
  }
  return filteredByDate; // Default to all if no filter
};

// Dummy API to update task (will be replaced)
const updateTaskStatus = async (taskId, newStatus) => {
  console.log(`Updating task ${taskId} to status: ${newStatus}`);
  await new Promise(resolve => setTimeout(resolve, 300));
  // In a real app, this would return the updated task from backend
  return { success: true, taskId, newStatus };
};
// --- End Placeholder Logic ---


function TodoListPage() {
  const { user } = useAuth(); // Get authenticated user info
  const [selectedDate, setSelectedDate] = useState(new Date()); // Defaults to today
  const [activeFilter, setActiveFilter] = useState('active'); // 'active', 'completed', 'backlog'
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTaskForModal, setSelectedTaskForModal] = useState(null);

  // Function to fetch and update tasks
  const loadTasks = async () => {
    if (!user) return;
    setLoading(true);
    // Replace 'user.username' with a dummy if user is null for initial testing without login
    const fetchedTasks = await fetchTasks(user?.username || 'user1', selectedDate, activeFilter);
    setTasks(fetchedTasks);
    setLoading(false);
  };

  // Effect to load tasks when date or filter changes
  useEffect(() => {
    loadTasks();
  }, [selectedDate, activeFilter, user]); // Reload when user context changes too

  // Date navigation handlers
  const goToYesterday = () => setSelectedDate(subDays(selectedDate, 1));
  const goToTomorrow = () => setSelectedDate(addDays(selectedDate, 1));

  // Calendar dropdown change handler
  const handleDateChange = (e) => {
    setSelectedDate(new Date(e.target.value));
  };

  // Task card click handler
  const handleTaskClick = (task) => {
    setSelectedTaskForModal(task);
    setIsModalOpen(true);
  };

  // Status change handler from modal
  const handleStatusChange = async (taskId, newStatus) => {
    setIsModalOpen(false); // Close modal immediately
    setLoading(true); // Show loading while updating
    const result = await updateTaskStatus(taskId, newStatus);
    if (result.success) {
      // Optimistically update the task list or refetch
      // For now, refetch all tasks to ensure consistency
      await loadTasks();
    } else {
      console.error('Failed to update task status.');
      // Handle error, maybe show a toast message
    }
    setLoading(false);
  };

  return (
    <div className="app-container"> {/* This ensures the flex layout from App.css */}
      <Sidebar />
      <div className="main-content-area flex-container">
        <Header />
        <div className="todo-list-page-container">
          <div className="todo-header">
                      <div className="date-navigation">
            <button onClick={goToYesterday} className="nav-arrow">← Previous Day</button>
            <input
              type="date"
              className="today-date-picker"
              value={format(selectedDate, 'yyyy-MM-dd')}
              onChange={handleDateChange}
            />
            <button onClick={goToTomorrow} className="nav-arrow">Next Day →</button>
          </div>
            <div className="filter-tabs">
              <button
                className={`filter-button filter-active ${activeFilter === 'active' ? 'active' : ''}`}
                onClick={() => setActiveFilter('active')}
              >
                Active
              </button>
              <button
                className={`filter-button filter-completed ${activeFilter === 'completed' ? 'active' : ''}`}
                onClick={() => setActiveFilter('completed')}
              >
                Completed
              </button>
              <button
                className={`filter-button filter-backlog ${activeFilter === 'backlog' ? 'active' : ''}`}
                onClick={() => setActiveFilter('backlog')}
              >
                Backlog
              </button>
            </div>
          </div>

          <div className="tasks-list-area">
            {loading ? (
              <p className="loading-message">Loading tasks...</p>
            ) : tasks.length === 0 ? (
              <p className="no-tasks-message">No tasks found for this selection.</p>
            ) : (
              tasks.map(task => (
                <TaskCard key={task.id} task={task} onClick={handleTaskClick} />
              ))
            )}
          </div>

          <TaskStatusModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onStatusChange={handleStatusChange}
            task={selectedTaskForModal}
          />
        </div>
      </div>
    </div>
  );
}

export default TodoListPage;