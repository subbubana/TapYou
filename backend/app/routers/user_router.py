from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func # Import func for lower()
from typing import List
from uuid import UUID

from ..database import get_session
import app.models as models
# Import authentication helpers
from .auth_router import get_password_hash, get_current_active_user, get_current_user # get_current_user if some GETs are authenticated

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post(
    "/",
    response_model=models.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers a new user with a unique username and a password. User is initially unverified.",
    operation_id="create_user_account",
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
    # Ensure username is stored lowercase for case-insensitive lookup later
    username_lower = user_in.username.lower()

    # Check if username already exists (case-insensitive)
    existing_user = session.exec(select(models.User).where(func.lower(models.User.username) == username_lower)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' already exists."
        )

    hashed_password = get_password_hash(user_in.password) # Hash the password
    db_user = models.User(
        username=user_in.username, # Store original casing, but lookup is lower
        hashed_password=hashed_password,
        is_verified=True # User is verified by default
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get(
    "/{username}",
    response_model=models.UserResponse,
    summary="Retrieve user details by username",
    description="Fetches the details of a specific user using their username. Requires authentication.",
    operation_id="get_user_by_username",
    responses={
        200: {"description": "User details retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to view this user."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    }
)
async def get_user_by_username(
    *,
    session: Session = Depends(get_session),
    username: str,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to retrieve user details by username.**
    Allows an authenticated user to retrieve their own profile details.
    """
    user = session.exec(select(models.User).where(func.lower(models.User.username) == func.lower(username))).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )
    
    # Ensure authenticated user is trying to view their own profile (basic authorization)
    if user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user's details."
        )
    
    return user

@router.get(
    "/{user_id}/id",
    response_model=models.UserResponse,
    summary="Retrieve user details by user ID",
    description="Fetches the details of a specific user using their unique user ID. Requires authentication.",
    operation_id="get_user_by_id",
    responses={
        200: {"description": "User details retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to view this user."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    }
)
async def get_user_by_id(
    *,
    session: Session = Depends(get_session),
    user_id: UUID,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to retrieve user details by user ID.**
    Allows an authenticated user to retrieve their own profile details using their ID.
    """
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )

    # Ensure authenticated user is trying to view their own profile
    if user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user's details."
        )

    return user

@router.put(
    "/{username}",
    response_model=models.UserResponse,
    summary="Update user details by username",
    description="Updates the username of an existing user. Requires authentication. The new username must be unique.",
    operation_id="update_user",
    responses={
        200: {"description": "User successfully updated."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to update this user or new username taken."},
        404: {"model": models.MessageResponse, "description": "User not found."},
        409: {"model": models.MessageResponse, "description": "New username already taken."},
    }
)
async def update_user(
    *,
    session: Session = Depends(get_session),
    username: str,
    user_in: models.UserUpdate,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to update user details by username.**
    """
    db_user = session.exec(select(models.User).where(func.lower(models.User.username) == func.lower(username))).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )
    
    # Authorization: Only the current authenticated user can update their own profile
    if db_user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this user."
        )

    if user_in.new_username is not None:
        new_username_lower = user_in.new_username.lower()
        if new_username_lower == db_user.username.lower(): # Case-insensitive check
            # Username is the same (case-insensitive), no actual change needed.
            return db_user

        # Check if the new username is already taken by another user (case-insensitive)
        existing_user_with_new_name = session.exec(
            select(models.User).where(func.lower(models.User.username) == new_username_lower)
        ).first()
        if existing_user_with_new_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{user_in.new_username}' is already taken."
            )
        
        db_user.username = user_in.new_username # Update with new casing

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.delete(
    "/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user account",
    description="Deletes a user by their username. Requires authentication. All associated tasks will also be deleted (due to CASCADE).",
    operation_id="delete_user_account",
    responses={
        204: {"description": "User successfully deleted."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to delete this user."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    }
)
async def delete_user(
    *,
    session: Session = Depends(get_session),
    username: str,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to delete a user by username.**
    """
    user_to_delete = session.exec(select(models.User).where(func.lower(models.User.username) == func.lower(username))).first()
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )

    # Authorization: Only the current authenticated user can delete their own profile
    if user_to_delete.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this user."
        )

    session.delete(user_to_delete)
    session.commit()
    return