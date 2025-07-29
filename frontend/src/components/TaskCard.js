// src/components/TaskCard.js
import React from 'react';
import './TaskCard.css'; // Create this CSS file

function TaskCard({ task, onClick, onEdit, onDelete }) {
  const handleEditClick = (e) => {
    e.stopPropagation(); // Prevent triggering the task click
    onEdit(task);
  };

  const handleDeleteClick = (e) => {
    e.stopPropagation(); // Prevent triggering the task click
    onDelete(task);
  };

  return (
    <div className="task-card-container" onClick={() => onClick(task)}>
      <div className="task-content">
        <p className="task-description">{task.task_description}</p>
        <div className="task-actions">
          <button
            className="edit-task-button"
            onClick={handleEditClick}
            title="Edit task"
          >
            ✏️
          </button>
          <button
            className="delete-task-button"
            onClick={handleDeleteClick}
            title="Delete task"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  );
}

export default TaskCard;