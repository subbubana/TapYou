// src/components/TaskCard.js
import React from 'react';
import './TaskCard.css'; // Create this CSS file

function TaskCard({ task, onClick }) {
  return (
    <div className="task-card-container" onClick={() => onClick(task)}>
      <p className="task-description">{task.task_description}</p>
    </div>
  );
}

export default TaskCard;