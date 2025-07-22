from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..database import get_session
import app.models as models # Use module import

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)

# Helper function to get a user (NO LONGER CREATES USER)
def get_user(username: str, session: Session) -> models.User:
    """
    Looks up a user by username in the database. Raises HTTPException if not found.
    """
    user = session.exec(select(models.User).where(models.User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Or 404 if you prefer, but 401 implies "user not authenticated/registered"
            detail=f"User '{username}' not recognized. Please create user first via /users/ endpoint."
        )
    return user

@router.post(
    "/",
    response_model=models.Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task for an existing user",
    description="Allows the agent to create individual tasks for a registered user. Task status defaults to 'pending'. User must exist.",
    operation_id="create_task",
    responses={
        201: {"description": "Task successfully created."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "User not recognized."},
    }
)
def create_task(*, session: Session = Depends(get_session), task_in: models.TaskCreateInput):
    """
    **Endpoint to create a new task.**
    """
    # 1. Get the user based on the provided username from the database (user must exist)
    user = get_user(task_in.username, session)

    # 2. Create a TaskBase instance with the resolved user_id and provided description
    db_task_base = models.TaskBase(
        user_id=user.user_id,
        task_description=task_in.task_description
    )

    # 3. Create a Task instance from the TaskBase, which will handle its default timestamps
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
    description="Modifies an existing task's description or status. Requires the username for authorization.",
    operation_id="update_task",
    responses={
        200: {"description": "Task successfully updated."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "Username not recognized."},
        403: {"model": models.MessageResponse, "description": "Not authorized to update this task."},
        404: {"model": models.MessageResponse, "description": "Task not found."},
    }
)
def update_task(*, session: Session = Depends(get_session), task_id: UUID, task_in: models.TaskUpdateInput):
    """
    **Endpoint to update an existing task by its ID.**
    """
    updating_user = get_user(task_in.username, session) # Use get_user helper

    db_task = session.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )

    if db_task.user_id != updating_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this task."
        )

    if task_in.current_status is not None and task_in.current_status != db_task.current_status:
        db_task.previous_status = db_task.current_status
        db_task.last_status_change_at = datetime.utcnow()

    if task_in.task_description is not None:
        db_task.task_description = task_in.task_description
    if task_in.current_status is not None:
        db_task.current_status = task_in.current_status

    db_task.modified_at = datetime.utcnow()
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single task",
    description="Deletes a specific task by its ID. Requires the username for authorization.",
    operation_id="delete_single_task",
    responses={
        204: {"description": "Task successfully deleted."},
        401: {"model": models.MessageResponse, "description": "Username not recognized."},
        403: {"model": models.MessageResponse, "description": "Not authorized to delete this task."},
        404: {"model": models.MessageResponse, "description": "Task not found."},
    }
)
def delete_single_task(*, session: Session = Depends(get_session), task_id: UUID, delete_in: models.TaskDeleteInput):
    """
    **Endpoint to delete a single task by its ID.**
    """
    deleting_user = get_user(delete_in.username, session) # Use get_user helper

    db_task = session.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )

    if db_task.user_id != deleting_user.user_id:
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
    description="Deletes multiple tasks by their IDs. Requires the username for authorization. If any task is not found or not owned, the entire operation will fail.",
    operation_id="delete_multiple_tasks",
    responses={
        200: {"description": "Tasks successfully deleted."},
        400: {"model": models.MessageResponse, "description": "Invalid input or some tasks not specified/found."},
        401: {"model": models.MessageResponse, "description": "Username not recognized."},
        403: {"model": models.MessageResponse, "description": "Not authorized to delete one or more tasks."},
    }
)
def delete_multiple_tasks(*, session: Session = Depends(get_session), batch_delete_in: models.TaskBatchDeleteInput):
    """
    **Endpoint to delete multiple tasks.**
    """
    deleting_user = get_user(batch_delete_in.username, session) # Use get_user helper

    tasks_to_delete = session.exec(
        select(models.Task).where(
            models.Task.task_id.in_(batch_delete_in.task_ids),
            models.Task.user_id == deleting_user.user_id
        )
    ).all()

    if len(tasks_to_delete) != len(batch_delete_in.task_ids):
        found_owned_ids = {task.task_id for task in tasks_to_delete}
        missing_or_unauthorized_ids = [
            str(task_id) for task_id in batch_delete_in.task_ids
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
    summary="Retrieve details of a single task",
    description="Fetches the complete details of a specific task by its ID. Requires the username for authorization.",
    operation_id="get_task_details",
    responses={
        200: {"description": "Task details retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Username not recognized."},
        403: {"model": models.MessageResponse, "description": "Not authorized to view this task."},
        404: {"model": models.MessageResponse, "description": "Task not found."},
    }
)
def get_task_details(
    *,
    session: Session = Depends(get_session),
    task_id: UUID,
    username: str = Query(..., description="Username of the task owner for authorization.")
):
    """
    **Endpoint to retrieve details of a single task.**
    """
    retrieving_user = get_user(username, session) # Use get_user helper

    db_task = session.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found."
        )

    if db_task.user_id != retrieving_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this task."
        )

    return db_task


@router.get(
    "/user/{username}",
    response_model=List[models.Task],
    summary="List tasks for a specific user",
    description="Retrieves a list of tasks for a given username, with options for filtering, sorting, and pagination.",
    operation_id="list_user_tasks",
    responses={
        200: {"description": "List of tasks retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Username not recognized (user not found)."},
    }
)
def list_user_tasks(
    *,
    session: Session = Depends(get_session),
    username: str, # Path parameter for the username
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
    # 1. Get the user for whom tasks are being requested
    target_user = get_user(username, session) # Use get_user helper

    # 2. Build the query
    query = select(models.Task).where(models.Task.user_id == target_user.user_id)

    # Apply status filter
    if status:
        query = query.where(models.Task.current_status == status)

    # Apply show_fresh_only filter
    if show_fresh_only:
        query = query.where(models.Task.pushed_from_past == False)

    # Apply sorting
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
        query = query.order_by(models.Task.created_at.desc()) # Default sort


    # Apply pagination
    query = query.offset(offset).limit(limit)

    # 3. Execute query and return tasks
    tasks = session.exec(query).all()
    return tasks