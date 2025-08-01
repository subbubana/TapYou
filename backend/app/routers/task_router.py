from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date

from ..database import get_session
import app.models as models
# Import authentication helpers
from .auth_router import get_current_active_user # Only need active user now

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)

@router.post(
    "/",
    response_model=models.Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task for the authenticated user",
    description="Creates a new task associated with the currently authenticated user. Task status defaults to 'active'.",
    operation_id="create_task",
    responses={
        201: {"description": "Task successfully created."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
    }
)
async def create_task(
    *,
    session: Session = Depends(get_session),
    task_input: models.TaskCreateInput, # Use the proper input model
    current_user: models.User = Depends(get_current_active_user) # Get authenticated user
):
    """
    **Endpoint to create a new task.**
    """
    # user_id comes directly from the authenticated user
    db_task_base = models.TaskBase(
        user_id=current_user.user_id, # User ID from JWT
        task_description=task_input.task_description
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
    task_input: models.TaskUpdateInput, # Use the proper input model
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

    if task_input.current_status is not None and task_input.current_status != db_task.current_status:
        db_task.previous_status = db_task.current_status
        db_task.last_status_change_at = datetime.utcnow()

    if task_input.task_description is not None:
        db_task.task_description = task_input.task_description

    if task_input.current_status is not None:
        db_task.current_status = task_input.current_status

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
    **Endpoint to delete a specific task by its ID.**
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
            detail="You are not authorized to delete this task."
        )

    session.delete(db_task)
    session.commit()
    return None

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
    **Endpoint to delete multiple tasks by their IDs.**
    """
    if not task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task IDs provided."
        )

    # Get all tasks that belong to the authenticated user
    user_tasks = session.exec(
        select(models.Task).where(
            (models.Task.task_id.in_(task_ids)) & 
            (models.Task.user_id == current_user.user_id)
        )
    ).all()

    # Check if all requested tasks were found and belong to the user
    found_task_ids = {task.task_id for task in user_tasks}
    missing_task_ids = set(task_ids) - found_task_ids

    if missing_task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tasks not found or not authorized to delete: {missing_task_ids}"
        )

    # Delete all tasks
    for task in user_tasks:
        session.delete(task)

    session.commit()
    return models.MessageResponse(
        message=f"Successfully deleted {len(user_tasks)} tasks."
    )

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
    **Endpoint to retrieve details of a specific task by its ID.**
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
            detail="You are not authorized to view this task."
        )

    return db_task

@router.get(
    "/",
    response_model=List[models.Task],
    tags=["Tasks"],
    summary="List tasks for the authenticated user",
    description="Retrieves a list of tasks for the currently authenticated user, with options for filtering, sorting, and pagination.",
    operation_id="list_user_tasks",
    responses={
        200: {"description": "List of tasks retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
    }
)
async def list_user_tasks(
    *,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_active_user), # Authenticated user
    status: Optional[str] = Query(None, description="Filter tasks by current status (e.g., 'active', 'completed', 'backlog'). If not provided, returns all tasks."),
    target_date: date = Query(..., description="Filter tasks for this specific date (YYYY-MM-DD). Required for 'active' and 'completed' statuses. Ignored for 'backlog' status."),
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g., 'created_at', 'modified_at', 'task_description')."),
    sort_order: Optional[str] = Query("asc", description="Sort order ('asc' or 'desc')."),
    limit: int = Query(100, ge=1, description="Maximum number of tasks to return."),
    offset: int = Query(0, ge=0, description="Number of tasks to skip from the beginning."),
):
    """
    **Endpoint to list tasks for the authenticated user, filtered by status and date.**
    - If `target_date` is provided:
        - For 'active' status: Tasks created on `target_date`.
        - For 'completed' status: Tasks whose status was changed to 'completed' on `target_date`.
        - For 'backlog' status: Tasks whose status was changed to 'backlog' on `target_date`.
    """
    # Build the query using current_user.user_id
    query = select(models.Task).where(models.Task.user_id == current_user.user_id)

    # Apply filters and sorting
    if status:
        query = query.where(models.Task.current_status == status)

    # Apply date filtering based on status
    if status is None:
        # If no status filter, return all tasks for the date (for counting purposes)
        # This will include tasks created on the target_date regardless of their current status
        query = query.where(func.date(models.Task.created_at) == target_date)
    elif status.lower() == 'active':
        # For 'active' status, filter by created_at date
        query = query.where(func.date(models.Task.created_at) == target_date)
    elif status.lower() == 'completed':
        # For 'completed', filter by last_status_change_at date
        query = query.where(
            (models.Task.last_status_change_at != None) & \
            (func.date(models.Task.last_status_change_at) == target_date)
        )
    elif status.lower() == 'backlog':
        # Filter backlog tasks where last_status_change_at is on or BEFORE target_date
        query = query.where(
            (models.Task.last_status_change_at != None) & \
            (func.date(models.Task.last_status_change_at) <= target_date) # <= (on or before)
        )
    else:
        # Should not happen if status is properly validated
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status filter. Status must be 'active', 'completed', or 'backlog'."
        )

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

@router.get(
    "/counts",
    response_model=models.TaskStatusCounts,
    tags=["Tasks"],
    summary="Get task counts by status for the authenticated user",
    description="Returns the total count of active, completed, and backlog tasks for the authenticated user.",
    operation_id="get_user_task_counts",
    responses={
        200: {"description": "Task counts retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
    }
)
async def get_user_task_counts(
    *,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_active_user),
    target_date: date = Query(..., description="Filter counts for tasks associated with this specific date (YYYY-MM-DD)."),
):
    """
    **Endpoint to get task counts by status for the authenticated user.**
    """
    # Count active tasks (created on target_date)
    active_count = session.exec(
        select(func.count(models.Task.task_id)).where(
            (models.Task.user_id == current_user.user_id) & \
            (models.Task.current_status == "active") & \
            (func.date(models.Task.created_at) == target_date)
        )
    ).first() or 0

    # Count completed tasks (status changed to completed on target_date)
    completed_count = session.exec(
        select(func.count(models.Task.task_id)).where(
            (models.Task.user_id == current_user.user_id) & \
            (models.Task.current_status == "completed") & \
            (models.Task.last_status_change_at != None) & \
            (func.date(models.Task.last_status_change_at) == target_date)
        )
    ).first() or 0

    # Count backlog tasks (status changed to backlog on or before target_date)
    backlog_count = session.exec(
        select(func.count(models.Task.task_id)).where(
            (models.Task.user_id == current_user.user_id) & \
            (models.Task.current_status == "backlog") & \
            (models.Task.last_status_change_at != None) & \
            (func.date(models.Task.last_status_change_at) <= target_date)
        )
    ).first() or 0

    total_count = active_count + completed_count + backlog_count

    return models.TaskStatusCounts(
        active=active_count,
        completed=completed_count,
        backlog=backlog_count,
        total=total_count
    )

@router.post(
    "/auto-mark-backlog",
    response_model=models.MessageResponse,
    summary="Automated job to mark old active tasks as backlog",
    description="Identifies active tasks created on previous days and updates their status to 'backlog'. This endpoint simulates a daily background cron job.",
    operation_id="auto_mark_backlog_tasks",
    responses={
        200: {"description": "Backlog conversion job completed."},
        401: {"model": models.MessageResponse, "description": "Authentication required (e.g., admin token)."},
    }
)
async def auto_mark_backlog_tasks(
    *,
    session: Session = Depends(get_session),
    # For a real system, this would be protected by an API Key or admin role check.
    # For now, it requires any authenticated user.
    current_user: models.User = Depends(get_current_active_user)
):
    """
    **Endpoint to automatically mark old active tasks as backlog.**
    This simulates a daily background job that would run to move tasks to backlog.
    """
    # Get today's date
    today = date.today()
    
    # Find active tasks created before today that belong to the authenticated user
    old_active_tasks = session.exec(
        select(models.Task).where(
            (models.Task.user_id == current_user.user_id) & \
            (models.Task.current_status == "active") & \
            (func.date(models.Task.created_at) < today)
        )
    ).all()

    # Update each task to backlog status
    for task in old_active_tasks:
        task.previous_status = task.current_status
        task.current_status = "backlog"
        task.last_status_change_at = datetime.utcnow()
        task.modified_at = datetime.utcnow()
        session.add(task)

    session.commit()

    return models.MessageResponse(
        message=f"Successfully moved {len(old_active_tasks)} active tasks to backlog for user {current_user.username}."
    )
