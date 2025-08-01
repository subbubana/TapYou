from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func # Import func for lower()
from typing import List
from uuid import UUID, uuid4

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
        is_verified=True, # User is verified by default
        chat_id=uuid4()
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get(
    "/profile",
    response_model=models.UserResponse,
    summary="Retrieve current user's profile",
    description="Fetches the details of the currently authenticated user.",
    operation_id="get_current_user_profile",
    responses={
        200: {"description": "User details retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
    }
)
async def get_current_user_profile(
    *,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to retrieve the current user's profile details.**
    """
    return current_user

@router.get(
    "/{user_id}",
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
    Allows an authenticated user to retrieve their own profile details.
    """
    user = session.get(models.User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )
    
    # Ensure authenticated user is trying to view their own profile (basic authorization)
    if user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user's details."
        )
    
    return user

@router.put(
    "/profile",
    response_model=models.UserResponse,
    summary="Update current user's profile",
    description="Updates the username of the currently authenticated user. The new username must be unique.",
    operation_id="update_current_user",
    responses={
        200: {"description": "User successfully updated."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        409: {"model": models.MessageResponse, "description": "New username already taken."},
    }
)
async def update_current_user(
    *,
    session: Session = Depends(get_session),
    user_in: models.UserUpdate,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to update the current user's profile.**
    """
    # Check if new username is provided
    if not user_in.new_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New username is required."
        )

    # Check if new username is different from current
    if user_in.new_username.lower() == current_user.username.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New username must be different from current username."
        )

    # Check if new username already exists (case-insensitive)
    existing_user = session.exec(
        select(models.User).where(
            (func.lower(models.User.username) == func.lower(user_in.new_username)) & \
            (models.User.user_id != current_user.user_id)
        )
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.new_username}' is already taken."
        )

    # Update the username
    current_user.username = user_in.new_username
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user

@router.delete(
    "/profile",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user's account",
    description="Deletes the currently authenticated user's account. All associated tasks will also be deleted (due to CASCADE).",
    operation_id="delete_current_user",
    responses={
        204: {"description": "User successfully deleted."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
    }
)
async def delete_current_user(
    *,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **Endpoint to delete the current user's account.**
    """
    # Delete the user (tasks will be deleted due to CASCADE)
    session.delete(current_user)
    session.commit()
    return None

# Keep the legacy endpoints for backward compatibility but mark them as deprecated
@router.get(
    "/{username}",
    response_model=models.UserResponse,
    summary="[DEPRECATED] Retrieve user details by username",
    description="[DEPRECATED] Use /users/profile instead. Fetches the details of a specific user using their username. Requires authentication.",
    operation_id="get_user_by_username_deprecated",
    responses={
        200: {"description": "User details retrieved successfully."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to view this user."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    },
    deprecated=True
)
async def get_user_by_username_deprecated(
    *,
    session: Session = Depends(get_session),
    username: str,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **[DEPRECATED] Endpoint to retrieve user details by username.**
    Use /users/profile instead.
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

@router.put(
    "/{username}",
    response_model=models.UserResponse,
    summary="[DEPRECATED] Update user details by username",
    description="[DEPRECATED] Use /users/profile instead. Updates the username of an existing user. Requires authentication. The new username must be unique.",
    operation_id="update_user_deprecated",
    responses={
        200: {"description": "User successfully updated."},
        400: {"model": models.MessageResponse, "description": "Invalid input."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to update this user or new username taken."},
        404: {"model": models.MessageResponse, "description": "User not found."},
        409: {"model": models.MessageResponse, "description": "New username already taken."},
    },
    deprecated=True
)
async def update_user_deprecated(
    *,
    session: Session = Depends(get_session),
    username: str,
    user_in: models.UserUpdate,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **[DEPRECATED] Endpoint to update user details by username.**
    Use /users/profile instead.
    """
    # Find the user by username
    user = session.exec(select(models.User).where(func.lower(models.User.username) == func.lower(username))).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )
    
    # Ensure authenticated user is trying to update their own profile
    if user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this user."
        )

    # Check if new username is provided
    if not user_in.new_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New username is required."
        )

    # Check if new username is different from current
    if user_in.new_username.lower() == user.username.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New username must be different from current username."
        )

    # Check if new username already exists (case-insensitive)
    existing_user = session.exec(
        select(models.User).where(
            (func.lower(models.User.username) == func.lower(user_in.new_username)) & \
            (models.User.user_id != user.user_id)
        )
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.new_username}' is already taken."
        )

    # Update the username
    user.username = user_in.new_username
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user

@router.delete(
    "/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[DEPRECATED] Delete a user account",
    description="[DEPRECATED] Use /users/profile instead. Deletes a user by their username. Requires authentication. All associated tasks will also be deleted (due to CASCADE).",
    operation_id="delete_user_deprecated",
    responses={
        204: {"description": "User successfully deleted."},
        401: {"model": models.MessageResponse, "description": "Authentication required."},
        403: {"model": models.MessageResponse, "description": "Not authorized to delete this user."},
        404: {"model": models.MessageResponse, "description": "User not found."},
    },
    deprecated=True
)
async def delete_user_deprecated(
    *,
    session: Session = Depends(get_session),
    username: str,
    current_user: models.User = Depends(get_current_active_user) # Authenticated user
):
    """
    **[DEPRECATED] Endpoint to delete a user account by username.**
    Use /users/profile instead.
    """
    # Find the user by username
    user = session.exec(select(models.User).where(func.lower(models.User.username) == func.lower(username))).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )
    
    # Ensure authenticated user is trying to delete their own account
    if user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this user."
        )

    # Delete the user (tasks will be deleted due to CASCADE)
    session.delete(user)
    session.commit()
    return None