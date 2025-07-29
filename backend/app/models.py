from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

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

    # Relationship to tasks
    tasks: list["Task"] = Relationship(back_populates="owner")

class UserCreate(UserBase):
    """Pydantic model for creating a new user (registration)."""
    password: str = Field(nullable=False, min_length=6) # User provides password during creation

class UserUpdate(SQLModel):
    """Pydantic model for updating an existing user. Allows changing username."""
    # For a real system, you'd allow password change here too, but not username direct update from client for security
    # Here, we're just allowing username change by authenticated user.
    new_username: Optional[str] = Field(default=None, max_length=100, alias="username")

class UserResponse(UserBase):
    """Pydantic model for responding with user details."""
    user_id: UUID
    is_verified: bool # Include verification status
    created_at: datetime

    class Config:
        from_attributes = True


# --- Task Models (remain largely unchanged in definition, but how they are used will change) ---
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


# --- API Input/Output Models for Tasks (THESE WILL CHANGE IN ROUTERS - username field removed) ---
# Keeping them here for now, but they will be simplified for authenticated use in the routers
class TaskCreateInput(SQLModel):
    """
    Pydantic model for the request body when creating a new task.
    Username is derived from the authenticated user's token.
    """
    # REMOVED: username: str = Field(...)
    task_description: str = Field(nullable=False, max_length=1000)

class TaskUpdateInput(SQLModel):
    """
    Pydantic model for the request body when updating an existing task.
    Username is derived from the authenticated user's token.
    """
    # REMOVED: username: str = Field(...)
    task_description: Optional[str] = None
    current_status: Optional[str] = None

class TaskDeleteInput(SQLModel):
    pass

class TaskBatchDeleteInput(SQLModel):
    task_ids: List[UUID] = Field(nullable=False)


# --- Standard Message Response Model (remains unchanged) ---
class MessageResponse(SQLModel):
    message: str

# --- Authentication Models (Updated) ---
class LoginRequest(SQLModel):
    """Model for user login request."""
    username: str
    password: str

class Token(SQLModel): # Renamed from LoginResponse for standard JWT naming
    """Model for JWT access token response."""
    access_token: str
    token_type: str = "bearer"
    # Added for convenience to client, though user_id is in JWT payload
    username: str
    user_id: UUID

class TaskStatusCounts(SQLModel):
    active: int = 0
    completed: int = 0
    backlog: int = 0
    total: int = 0 # Optional: A total count of all tasks for the user