// src/pages/TodoListPage.js
import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import TaskCard from '../components/TaskCard';
import TaskStatusModal from '../components/TaskStatusModel';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import { useAuth } from '../auth/AuthContext';
import { format, subDays, addDays } from 'date-fns';
import { tasks as tasksApi } from '../api'; // Import tasks API
import './TodoListPage.css';
import '../App.css'; // Keep the App.css for overall layout

function TodoListPage() {
  const { user } = useAuth(); // Get authenticated user info: {username, user_id}
  const [selectedDate, setSelectedDate] = useState(new Date()); // Defaults to today
  const [activeFilter, setActiveFilter] = useState('active'); // 'active', 'completed', 'backlog'
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTaskForModal, setSelectedTaskForModal] = useState(null);
  const [taskCounts, setTaskCounts] = useState({ active: 0, completed: 0, backlog: 0, total: 0 }); // State for counts
  
  // New state for create task modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newTaskDescription, setNewTaskDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  
  // New state for edit task modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [editedTaskDescription, setEditedTaskDescription] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // New state for delete confirmation modal
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deletingTask, setDeletingTask] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // New state for inline task creation
  const [newTaskInput, setNewTaskInput] = useState('');
  const [isAddingTask, setIsAddingTask] = useState(false);

  // Function to fetch and update tasks
  const loadTasks = async () => {
    if (!user?.username) return; // Ensure user is authenticated

    setLoading(true);
    try {
      const fetchedTasks = await tasksApi.getTasks(
        user.username,
        activeFilter,
        selectedDate // Pass selectedDate as targetDate
      );
      setTasks(fetchedTasks);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      setTasks([]); // Clear tasks on error
    } finally {
      setLoading(false);
    }
  };

  // Function to fetch and update counts
  const loadTaskCounts = async () => {
    if (!user?.username) return;
    try {
      const fetchedCounts = await tasksApi.getTaskCounts(
        user.username,
        selectedDate // Pass selectedDate as targetDate
      );
      setTaskCounts(fetchedCounts);
    } catch (error) {
      console.error('Failed to fetch task counts:', error);
      setTaskCounts({ active: 0, completed: 0, backlog: 0, total: 0 });
    }
  };

  // Function to create a new task
  const handleCreateTask = async () => {
    if (!newTaskDescription.trim()) return;
    
    setIsCreating(true);
    try {
      await tasksApi.createTask(newTaskDescription.trim());
      setNewTaskDescription('');
      setIsCreateModalOpen(false);
      // Refresh tasks and counts
      await loadTasks();
      await loadTaskCounts();
    } catch (error) {
      console.error('Failed to create task:', error);
      // You could add a toast notification here
    } finally {
      setIsCreating(false);
    }
  };

  // Function to edit a task
  const handleEditTask = (task) => {
    setEditingTask(task);
    setEditedTaskDescription(task.task_description);
    setIsEditModalOpen(true);
  };

  // Function to save edited task
  const handleSaveEdit = async () => {
    if (!editedTaskDescription.trim() || !editingTask) return;
    
    setIsEditing(true);
    try {
      await tasksApi.updateTask(editingTask.task_id, {
        task_description: editedTaskDescription.trim()
      });
      setEditedTaskDescription('');
      setEditingTask(null);
      setIsEditModalOpen(false);
      // Refresh tasks and counts
      await loadTasks();
      await loadTaskCounts();
    } catch (error) {
      console.error('Failed to update task:', error);
      // You could add a toast notification here
    } finally {
      setIsEditing(false);
    }
  };

  // Function to delete a task
  const handleDeleteTask = async (task) => {
    if (!task) return;
    
    setDeletingTask(task);
    setIsDeleteModalOpen(true);
  };

  // Function to create a new task inline
  const handleAddTaskInline = async () => {
    if (!newTaskInput.trim()) return;
    
    setIsAddingTask(true);
    try {
      await tasksApi.createTask(newTaskInput.trim());
      setNewTaskInput('');
      
      // Reset textarea height and scrollbar
      const textarea = document.querySelector('.inline-task-input');
      if (textarea) {
        textarea.style.height = '40px';
        textarea.style.overflowY = 'hidden';
      }
      
      // Refresh tasks and counts
      await loadTasks();
      await loadTaskCounts();
    } catch (error) {
      console.error('Failed to create task:', error);
      alert(`Failed to create task: ${error.message}`);
    } finally {
      setIsAddingTask(false);
    }
  };

  // Function to handle Enter key press in input
  const handleInputKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAddTaskInline();
    }
  };

  // Function to auto-resize textarea
  const handleTextareaChange = (e) => {
    setNewTaskInput(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 120);
    textarea.style.height = newHeight + 'px';
    
    // Show scrollbar only when content exceeds visible area
    if (textarea.scrollHeight > 120) {
      textarea.style.overflowY = 'auto';
    } else {
      textarea.style.overflowY = 'hidden';
    }
  };

  // Effect to load tasks and counts when date, filter, or user changes
  useEffect(() => {
    loadTasks();
    loadTaskCounts();
  }, [selectedDate, activeFilter, user]); // Reload when user context changes too (e.g., after login)

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
    try {
      // Call the backend API to update status
      const result = await tasksApi.updateTask(taskId, { current_status: newStatus });
      console.log('Task update result:', result);
      // Re-fetch all tasks and counts to ensure UI is up-to-date
      await loadTasks();
      await loadTaskCounts();
    } catch (error) {
      console.error('Failed to update task status:', error);
      // Handle error, maybe show a toast message to user
    } finally {
      setLoading(false);
    }
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
                Active ({taskCounts.active})
              </button>
              <button
                className={`filter-button filter-completed ${activeFilter === 'completed' ? 'active' : ''}`}
                onClick={() => setActiveFilter('completed')}
              >
                Completed ({taskCounts.completed})
              </button>
              <button
                className={`filter-button filter-backlog ${activeFilter === 'backlog' ? 'active' : ''}`}
                onClick={() => setActiveFilter('backlog')}
              >
                Backlog ({taskCounts.backlog})
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
                <TaskCard 
                  key={task.task_id} 
                  task={task} 
                  onClick={handleTaskClick}
                  onEdit={handleEditTask}
                  onDelete={handleDeleteTask}
                />
              ))
            )}
          </div>

          {/* Bottom add task section */}
          <div className="bottom-add-task-section">
            <textarea
              className="inline-task-input"
              placeholder="Add new task..."
              value={newTaskInput}
              onChange={handleTextareaChange}
              onKeyPress={handleInputKeyPress}
              disabled={isAddingTask}
              rows={1}
            />
            <button
              className="add-task-button"
              onClick={handleAddTaskInline}
              disabled={!newTaskInput.trim() || isAddingTask}
              title="Add new task (inline)"
            >
              <span className="add-icon">+</span>
            </button>
          </div>

          <TaskStatusModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onStatusChange={handleStatusChange}
            task={selectedTaskForModal}
          />

          {/* Create Task Modal */}
          {isCreateModalOpen && (
            <div className="modal-overlay">
              <div className="modal-content create-task-modal">
                <h3>Create New Task</h3>
                <textarea
                  className="task-description-input"
                  placeholder="Enter task description..."
                  value={newTaskDescription}
                  onChange={(e) => setNewTaskDescription(e.target.value)}
                  rows={4}
                  autoFocus
                />
                <div className="modal-actions">
                  <button 
                    className="cancel-button"
                    onClick={() => {
                      setIsCreateModalOpen(false);
                      setNewTaskDescription('');
                    }}
                    disabled={isCreating}
                  >
                    Cancel
                  </button>
                  <button 
                    className="create-button"
                    onClick={handleCreateTask}
                    disabled={!newTaskDescription.trim() || isCreating}
                  >
                    {isCreating ? 'Creating...' : 'Create Task'}
                  </button>
                </div>
                <button 
                  className="modal-close-button" 
                  onClick={() => {
                    setIsCreateModalOpen(false);
                    setNewTaskDescription('');
                  }}
                >
                  &times;
                </button>
              </div>
            </div>
          )}

          {/* Edit Task Modal */}
          {isEditModalOpen && (
            <div className="modal-overlay">
              <div className="modal-content create-task-modal">
                <h3>Edit Task</h3>
                <textarea
                  className="task-description-input"
                  placeholder="Enter task description..."
                  value={editedTaskDescription}
                  onChange={(e) => setEditedTaskDescription(e.target.value)}
                  rows={4}
                  autoFocus
                />
                <div className="modal-actions">
                  <button 
                    className="cancel-button"
                    onClick={() => {
                      setIsEditModalOpen(false);
                      setEditedTaskDescription('');
                      setEditingTask(null);
                    }}
                    disabled={isEditing}
                  >
                    Cancel
                  </button>
                  <button 
                    className="create-button"
                    onClick={handleSaveEdit}
                    disabled={!editedTaskDescription.trim() || isEditing}
                  >
                    {isEditing ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
                <button 
                  className="modal-close-button" 
                  onClick={() => {
                    setIsEditModalOpen(false);
                    setEditedTaskDescription('');
                    setEditingTask(null);
                  }}
                >
                  &times;
                </button>
              </div>
            </div>
          )}

          {/* Delete Confirmation Modal */}
          {isDeleteModalOpen && deletingTask && (
            <DeleteConfirmModal
              isOpen={isDeleteModalOpen}
              onClose={() => setIsDeleteModalOpen(false)}
              onConfirm={async () => {
                setIsDeleting(true);
                try {
                  await tasksApi.deleteTask(deletingTask.task_id);
                  setIsDeleteModalOpen(false);
                  setDeletingTask(null);
                  // Refresh tasks and counts
                  await loadTasks();
                  await loadTaskCounts();
                } catch (error) {
                  console.error('Failed to delete task:', error);
                  alert(`Failed to delete task: ${error.message}`);
                } finally {
                  setIsDeleting(false);
                }
              }}
              isDeleting={isDeleting}
              task={deletingTask}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default TodoListPage;