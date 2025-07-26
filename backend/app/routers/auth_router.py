from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
import jwt # For creating dummy JWTs (install python-jose[jwt])
from datetime import datetime, timedelta

from ..database import get_session
import app.models as models

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# --- Dummy Secret Key for JWT (CHANGE THIS IN PRODUCTION!) ---
# This should ideally be loaded from environment variables and be much stronger.
SECRET_KEY = "super-secret-key-that-should-be-in-env-vars-and-long"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Dummy token expiration

@router.post(
    "/login",
    response_model=models.LoginResponse,
    summary="User Login",
    description="Authenticates a user. For now, only checks if username exists. No password verification.",
    operation_id="login_user",
    responses={
        200: {"description": "Successful login."},
        400: {"model": models.MessageResponse, "description": "Invalid credentials (username not found)."},
    }
)
def login_user(
    *,
    session: Session = Depends(get_session),
    login_in: models.LoginRequest
):
    """
    **Endpoint for user login.**
    Currently, this only checks if the username exists in the database.
    Password provided in `login_in` is ignored.
    """
    user = session.exec(select(models.User).where(models.User.username == login_in.username)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password (username not found)."
        )

    # In a real app, you would verify the password here:
    # if not verify_password(login_in.password, user.hashed_password):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    # Create a dummy access token (JWT)
    # This token doesn't actually contain any user info for security,
    # but in a real app, you might encode user_id or roles.
    # For this example, we're just making a valid-looking JWT.
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user.user_id), "username": user.username} # Sub is usually user ID
    
    expire = datetime.utcnow() + access_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return models.LoginResponse(
        access_token=encoded_jwt,
        username=user.username,
        user_id=user.user_id
    )