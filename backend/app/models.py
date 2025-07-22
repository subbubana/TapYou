from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship # Import Relationship

class UserBase(SQLModel):
    """Base model for user properties."""
    username: str = Field(unique=True, index=True, max_length=100)

class User(UserBase, table=True):
    """Database model for the 'users' table."""
    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship to tasks: A user can have multiple tasks
    tasks: list["Task"] = Relationship(back_populates="owner")

class UserCreate(UserBase):
    """Pydantic model for creating a new user."""
    pass # Inherits username from UserBase

class UserUpdate(SQLModel):
    """Pydantic model for updating an existing user. Allows changing username."""
    new_username: Optional[str] = Field(default=None, max_length=100, alias="username")
    
class UserResponse(UserBase):
    """Pydantic model for responding with user details."""
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TaskBase(SQLModel):
    """
    Base model for task properties.
    Contains fields common to creating and representing a task.
    """
    task_description: str = Field(nullable=False, max_length=1000)
    current_status: str = Field(default="pending", max_length=50) # State: 'pending', 'completed', 'backlog', 'in_progress'
    pushed_from_past: bool = Field(default=False) # Retained for future backlog logic based on original requirements

    # Foreign key linking to User
    user_id: UUID = Field(foreign_key="users.user_id", nullable=False, index=True)

class Task(TaskBase, table=True):
    """
    SQLModel class representing the 'tasks' table in the database.
    Includes primary key and timestamp fields which are managed by the system.
    """
    __tablename__ = "tasks"

    task_id: UUID = Field(default_factory=uuid4, primary_key=True) # Unique ID for the task, auto-generated
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False) # Timestamp when task was created
    modified_at: datetime = Field(default_factory=datetime.utcnow, nullable=False) # Timestamp of last modification
    previous_status: Optional[str] = Field(default=None, max_length=50) # Status before current one (retained for history)
    last_status_change_at: datetime = Field(default_factory=datetime.utcnow, nullable=False) # Timestamp when current_status was last set

    # Relationship to user: A task belongs to one user
    owner: Optional[User] = Relationship(back_populates="tasks")


# For Pydantic models used as API input/output
class TaskCreateInput(SQLModel):
    """
    Pydantic model for the request body when creating a new task.
    Only takes username and task_description from the user.
    """
    username: str = Field(nullable=False, max_length=100) # User-provided username
    task_description: str = Field(nullable=False, max_length=1000)

class TaskUpdateInput(SQLModel):
    """
    Pydantic model for the request body when updating an existing task.
    Requires username for authorization check.
    Allows partial update of task_description or current_status.
    """
    username: str = Field(nullable=False, max_length=100) # Username of the user attempting the update
    task_description: Optional[str] = None
    current_status: Optional[str] = None # Allows changing to 'backlog', 'completed', etc.

class TaskDeleteInput(SQLModel):
    """
    Pydantic model for the request body when deleting a single task.
    Requires username for authorization.
    """
    username: str = Field(nullable=False, max_length=100)

class TaskBatchDeleteInput(SQLModel):
    """
    Pydantic model for the request body when deleting multiple tasks.
    Requires username for authorization and a list of task IDs.
    """
    username: str = Field(nullable=False, max_length=100)
    task_ids: List[UUID] = Field(nullable=False)

class MessageResponse(SQLModel):
    """
    Standard model for API error or informational messages.
    """
    message: str