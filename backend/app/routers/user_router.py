from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID

from ..database import get_session
import app.models as models # Use module import

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post(
    "/",
    response_model=models.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Registers a new user with a unique username. A unique user_id is generated automatically.",
    operation_id="create_user",
    responses={
        201: {"description": "User successfully created."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        409: {"model": models.MessageResponse, "description": "Username already exists."},
    }
)
def create_user(*, session: Session = Depends(get_session), user_in: models.UserCreate):
    """
    **Endpoint to create a new user.**
    """
    # Check if username already exists
    existing_user = session.exec(select(models.User).where(models.User.username == user_in.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' already exists."
        )

    db_user = models.User.model_validate(user_in)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get(
    "/{username}",
    response_model=models.UserResponse,
    summary="Retrieve user details by username",
    description="Fetches the details of a specific user using their username.",
    operation_id="get_user_by_username",
    responses={
        200: {"description": "User details retrieved successfully."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    }
)
def get_user_by_username(*, session: Session = Depends(get_session), username: str):
    """
    **Endpoint to retrieve user details by username.**
    """
    user = session.exec(select(models.User).where(models.User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )
    return user

@router.get(
    "/{user_id}/id", # Using a different path to avoid conflict with /users/{username}
    response_model=models.UserResponse,
    summary="Retrieve user details by user ID",
    description="Fetches the details of a specific user using their unique user ID.",
    operation_id="get_user_by_id",
    responses={
        200: {"description": "User details retrieved successfully."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    }
)
def get_user_by_id(*, session: Session = Depends(get_session), user_id: UUID):
    """
    **Endpoint to retrieve user details by user ID.**
    """
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )
    return user

@router.put(
    "/{username}",
    response_model=models.UserResponse,
    summary="Update user details by username",
    description="Updates the username of an existing user. The new username must be unique.",
    operation_id="update_user",
    responses={
        200: {"description": "User successfully updated."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        404: {"model": models.MessageResponse, "description": "User not found."},
        409: {"model": models.MessageResponse, "description": "New username already taken."},
    }
)
def update_user(*, session: Session = Depends(get_session), username: str, user_in: models.UserUpdate):
    """
    **Endpoint to update user details by username.**
    """
    db_user = session.exec(select(models.User).where(models.User.username == username)).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )

    if user_in.new_username is not None:
        if user_in.new_username == db_user.username:
            # Username is the same, no actual change needed.
            # We can just return the existing user details.
            return db_user

        # Check if the new username is already taken by another user
        existing_user_with_new_name = session.exec(
            select(models.User).where(models.User.username == user_in.new_username)
        ).first()
        if existing_user_with_new_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{user_in.new_username}' is already taken."
            )

        db_user.username = user_in.new_username

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.delete(
    "/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description="Deletes a user by their username. All associated tasks will also be deleted (due to CASCADE).",
    operation_id="delete_user",
    responses={
        204: {"description": "User successfully deleted."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    }
)
def delete_user(*, session: Session = Depends(get_session), username: str):
    """
    **Endpoint to delete a user by username.**
    """
    user = session.exec(select(models.User).where(models.User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )
    session.delete(user)
    session.commit()
    return