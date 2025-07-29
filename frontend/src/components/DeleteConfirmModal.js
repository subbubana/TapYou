import React from 'react';
import './DeleteConfirmModal.css';

function DeleteConfirmModal({ isOpen, onClose, onConfirm, task, isDeleting }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content delete-confirm-modal">
        <div className="delete-modal-header">
          <h3>Delete Task</h3>
          <button 
            className="modal-close-button" 
            onClick={onClose}
            disabled={isDeleting}
          >
            &times;
          </button>
        </div>
        
        <div className="delete-modal-body">
          <div className="delete-icon">🗑️</div>
          <p className="delete-message">
            Are you sure you want to delete this task?
          </p>
          <div className="task-preview">
            <strong>Task:</strong> {task?.task_description}
          </div>
          <p className="delete-warning">
            This action cannot be undone.
          </p>
        </div>
        
        <div className="delete-modal-actions">
          <button 
            className="cancel-button"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button 
            className="delete-button"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Task'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmModal; 