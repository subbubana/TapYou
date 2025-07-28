from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..database import get_session
import app.models as models
# Import authentication helpers
from .auth_router import get_current_active_user # Only need active user now

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)

# Helper function to get a user (MODIFIED: now gets user from DB, raises 401 if not found)
# This helper is not directly used for authorization anymore; get_current_active_user is.
# It might be used if a task needs to be viewed by its creator's username (like in GET /tasks/user/{username})
# but the request itself is not authenticated.
# Since all GET /tasks/user/{username} is now authenticated, this helper is less direct.
# Let's remove the old get_user helper and directly use get_current_active_user or a query in endpoints.


@router.post(
    "/",
    response_model=models.Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task for the authenticated user",
    description="Creates a new task associated with the currently authenticated user. Task status defaults to 'pending'.",
    operation_id="create_task",
    responses={
        201: {"description": "Task successfully created."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "Authentication required (user not logged in)."},
        400: {"model": models.MessageResponse, "description": "User not verified (cannot create tasks)."}
    }
)
async def create_task(
    *,
    session: Session = Depends(get_session),
    task_description: str, # Directly takes task_description, user from token
    current_user: models.User = Depends(get_current_active_user) # Get authenticated user
):
    """
    **Endpoint to create a new task.**
    """
    # user_id comes directly from the authenticated user
    db_task_base = models.TaskBase(
        user_id=current_user.user_id, # User ID from JWT
        task_description=task_description
    )
    db_task = models.Task.model_validate(db_task_base)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.put(
    "/{task_id}",
    response_model=models.Task,
    tags=["Tasks"],
    summary="Update an existing task",
    description="Modifies an existing task's description or status. Requires authentication.",
    operation_id="update_task",
    responses={
        200: {"description": "Task successfully updated."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to update this task."},
        404: {"model": models.MessageResponse, "description": "Task not found."},
    }
)
async def update_task(
    *,
    session: Session = Depends(get_session),
    task_id: UUID,
    task_description: Optional[str] = None, # No TaskUpdateInput model with username
    current_status: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to update an existing task by its ID.**
    """
    db_task = session.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )

    # Authorization: Check if the authenticated user owns this task
    if db_task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this task."
        )

    if current_status is not None and current_status != db_task.current_status:
        db_task.previous_status = db_task.current_status
        db_task.last_status_change_at = datetime.utcnow()

    if task_description is not None:
        db_task.task_description = task_description
    if current_status is not None:
        db_task.current_status = current_status

    db_task.modified_at = datetime.utcnow()
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single task",
    description="Deletes a specific task by its ID. Requires authentication.",
    operation_id="delete_single_task",
    responses={
        204: {"description": "Task successfully deleted."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to delete this task."},
        404: {"model": models.MessageResponse, "description": "Task not found."},
    }
)
async def delete_single_task(
    *,
    session: Session = Depends(get_session),
    task_id: UUID,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to delete a single task by its ID.**
    """
    db_task = session.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )

    if db_task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this task."
        )

    session.delete(db_task)
    session.commit()
    return

@router.delete(
    "/batch",
    response_model=models.MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete multiple tasks",
    description="Deletes multiple tasks by their IDs. Requires authentication. All tasks in the list must be owned by the authenticated user for the operation to succeed.",
    operation_id="delete_multiple_tasks",
    responses={
        200: {"description": "Tasks successfully deleted."},
        400: {"model": models.MessageResponse, "description": "Invalid input or some tasks not specified/found."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to delete one or more tasks."},
    }
)
async def delete_multiple_tasks(
    *,
    session: Session = Depends(get_session),
    task_ids: List[UUID], # No TaskBatchDeleteInput model with username
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to delete multiple tasks.**
    """
    tasks_to_delete = session.exec(
        select(models.Task).where(
            models.Task.task_id.in_(task_ids),
            models.Task.user_id == current_user.user_id
        )
    ).all()

    if len(tasks_to_delete) != len(task_ids):
        found_owned_ids = {task.task_id for task in tasks_to_delete}
        missing_or_unauthorized_ids = [
            str(task_id) for task_id in task_ids
            if task_id not in found_owned_ids
        ]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Some tasks were not found or you are not authorized to delete them: {', '.join(missing_or_unauthorized_ids)}"
        )

    deleted_count = 0
    for task in tasks_to_delete:
        session.delete(task)
        deleted_count += 1
    session.commit()

    return models.MessageResponse(message=f"Successfully deleted {deleted_count} tasks.")

@router.get(
    "/{task_id}",
    response_model=models.Task,
    tags=["Tasks"],
    summary="Retrieve details of a single task",
    description="Fetches the complete details of a specific task by its ID. Requires authentication.",
    operation_id="get_task_details",
    responses={
        200: {"description": "Task details retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to view this task."},
        404: {"model": models.MessageResponse, "description": "Task not found."},
    }
)
async def get_task_details(
    *,
    session: Session = Depends(get_session),
    task_id: UUID,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to retrieve details of a single task.**
    """
    db_task = session.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )

    if db_task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this task."
        )

    return db_task


@router.get(
    "/user/{username}",
    response_model=List[models.Task],
    tags=["Tasks"],
    summary="List tasks for a specific user (Authenticated User's Tasks)",
    description="Retrieves a list of tasks for the currently authenticated user, with options for filtering, sorting, and pagination. The username in the path must match the authenticated user.",
    operation_id="list_user_tasks",
    responses={
        200: {"description": "List of tasks retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to view other user's tasks."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    }
)
async def list_user_tasks(
    *,
    session: Session = Depends(get_session),
    username: str, # Path parameter for the username
    current_user: models.User = Depends(get_current_active_user), # Authenticated user
    status: Optional[str] = Query(None, description="Filter tasks by current status (e.g., 'pending', 'completed')."),
    show_fresh_only: bool = Query(True, description="If true, only shows tasks not carried forward from previous days (pushed_from_past=False)."),
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g., 'created_at', 'modified_at', 'task_description')."),
    sort_order: Optional[str] = Query("asc", description="Sort order ('asc' or 'desc')."),
    limit: int = Query(100, ge=1, description="Maximum number of tasks to return."),
    offset: int = Query(0, ge=0, description="Number of tasks to skip from the beginning."),
):
    """
    **Endpoint to list tasks for a specific user.**
    """
    # 1. Ensure the username in the path matches the authenticated user's username
    if current_user.username.lower() != username.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view other user's tasks."
        )
    
    # 2. Build the query using current_user.user_id
    query = select(models.Task).where(models.Task.user_id == current_user.user_id)

    # Apply filters and sorting (rest of the logic remains the same)
    if status:
        query = query.where(models.Task.current_status == status)

    if show_fresh_only:
        query = query.where(models.Task.pushed_from_past == False)

    if sort_by:
        valid_sort_fields = ["created_at", "modified_at", "task_description", "current_status"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        if sort_order and sort_order.lower() == "desc":
            query = query.order_by(getattr(models.Task, sort_by).desc())
        else:
            query = query.order_by(getattr(models.Task, sort_by))
    else:
        query = query.order_by(models.Task.created_at.desc())


    query = query.offset(offset).limit(limit)

    tasks = session.exec(query).all()
    return tasks