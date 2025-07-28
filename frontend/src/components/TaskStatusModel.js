// src/components/TaskStatusModal.js
import React from 'react';
import './TaskStatusModel.css'; // Create this CSS file

function TaskStatusModal({ isOpen, onClose, onStatusChange, task }) {
  if (!isOpen || !task) return null;

  const statuses = ['active', 'completed', 'backlog', 'pending']; // Possible statuses

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Update Task Status</h3>
        <p className="modal-task-description">{task.task_description}</p>
        <div className="modal-status-buttons">
          {statuses.map(status => (
            <button
              key={status}
              className={`status-button ${status} ${task.current_status === status ? 'current' : ''}`}
              onClick={() => onStatusChange(task.task_id, status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
        <button className="modal-close-button" onClick={onClose}>
          &times; {/* Times symbol for close */}
        </button>
      </div>
    </div>
  );
}

export default TaskStatusModal;