// src/components/TaskCard.js
import React from 'react';
import './TaskCard.css'; // Create this CSS file

function TaskCard({ task, onClick }) {
  // Determine color/style based on task status
  const statusClass = task.current_status ? task.current_status.toLowerCase() : 'active';
  const displayStatus = task.current_status ? task.current_status : 'Pending';

  return (
    <div className={`task-card-container ${statusClass}`} onClick={() => onClick(task)}>
      <div className="task-content">
        <p className="task-description">{task.task_description}</p>
      </div>
      <div className="task-status-badge">
        <span className={`status-badge status-${statusClass}`}>{displayStatus}</span>
      </div>
    </div>
  );
}

export default TaskCard;