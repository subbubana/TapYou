from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel

from sqlmodel import Field, SQLModel, Relationship

# --- User Models ---
class UserBase(SQLModel):
    """Base model for user properties."""
    # Username will be stored as lowercase for case-insensitive lookup
    username: str = Field(unique=True, index=True, max_length=100)

class User(UserBase, table=True):
    """Database model for the 'users' table."""
    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str = Field(nullable=False) # Store hashed password
    is_verified: bool = Field(default=False) # New field for verification status
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    chat_id: UUID = Field(default_factory=uuid4, unique=True, nullable=False)
    chat_messages: list["ChatMessage"] = Relationship(back_populates="user")

    # Relationship to tasks
    tasks: list["Task"] = Relationship(back_populates="owner")

class UserCreate(UserBase):
    """Pydantic model for creating a new user (registration)."""
    password: str = Field(nullable=False, min_length=6) # User provides password during creation

class UserUpdate(SQLModel):
    """Pydantic model for updating an existing user. Allows changing username."""
    new_username: Optional[str] = Field(default=None, max_length=100, description="New username for the user")

class UserResponse(UserBase):
    """Pydantic model for responding with user details."""
    user_id: UUID
    is_verified: bool # Include verification status
    created_at: datetime

    class Config:
        from_attributes = True


# --- Task Models ---
class TaskBase(SQLModel):
    task_description: str = Field(nullable=False, max_length=1000)
    current_status: str = Field(default="active", max_length=50)
    user_id: UUID = Field(foreign_key="users.user_id", nullable=False, index=True)

class Task(TaskBase, table=True):
    __tablename__ = "tasks"
    task_id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    modified_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    previous_status: Optional[str] = Field(default=None, max_length=50)
    last_status_change_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    owner: Optional[User] = Relationship(back_populates="tasks")

# --- API Input/Output Models for Tasks ---
class TaskCreateInput(SQLModel):
    """
    Pydantic model for the request body when creating a new task.
    User context is derived from authentication token.
    """
    task_description: str = Field(nullable=False, max_length=1000, description="Description of the task to create")

class TaskUpdateInput(SQLModel):
    """
    Pydantic model for the request body when updating an existing task.
    User context is derived from authentication token.
    """
    task_description: Optional[str] = Field(default=None, max_length=1000, description="New description for the task")
    current_status: Optional[str] = Field(default=None, max_length=50, description="New status for the task (active, completed, backlog)")

class TaskBatchDeleteInput(SQLModel):
    """Pydantic model for deleting multiple tasks by their IDs."""
    task_ids: List[UUID] = Field(..., description="List of task IDs to delete")

class TaskStatusCounts(SQLModel):
    """Pydantic model for task status counts response."""
    active: int = Field(default=0, description="Number of active tasks")
    completed: int = Field(default=0, description="Number of completed tasks")
    backlog: int = Field(default=0, description="Number of backlog tasks")
    total: int = Field(default=0, description="Total number of tasks")


# --- Chat Models ---
class ChatMessageBase(SQLModel):
    """Base model for chat message properties."""
    chat_id: UUID = Field(foreign_key="users.chat_id", nullable=False, index=True) # Links to User's chat_id
    is_user: bool = Field(nullable=False) # True if user sent, False otherwise
    is_agent: bool = Field(nullable=False) # True if agent sent, False otherwise
    content: str = Field(nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class ChatMessage(ChatMessageBase, table=True):
    """Database model for the 'chat_messages' table."""
    __tablename__ = "chat_messages"
    message_id: UUID = Field(default_factory=uuid4, primary_key=True)

    user: Optional[User] = Relationship(back_populates="chat_messages") # Relationship back to User

class ChatInput(SQLModel):
    """Pydantic model for chat input."""
    message: str = Field(..., description="Message content to send to the agent")

class ChatResponse(SQLModel):
    """Pydantic model for chat response."""
    agent_response: str = Field(..., description="Response from the AI agent")
    message_id: UUID = Field(..., description="ID of the stored agent message")

class ChatMessageRead(SQLModel):
    """Pydantic model for reading chat messages."""
    chat_id: UUID
    is_user: bool
    is_agent: bool
    content: str
    timestamp: datetime
    message_id: UUID

    class Config:
        from_attributes = True


# --- Authentication Models ---
class LoginRequest(SQLModel):
    """Model for user login request."""
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="Password for login")

class Token(SQLModel):
    """Model for JWT access token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    username: str = Field(..., description="Username of the authenticated user")
    user_id: UUID = Field(..., description="User ID of the authenticated user")


# --- Standard Response Models ---
class MessageResponse(SQLModel):
    """Standard message response model."""
    message: str = Field(..., description="Response message")