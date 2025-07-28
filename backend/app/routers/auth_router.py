from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # New import
from sqlmodel import Session, select
from jose import jwt, JWTError # Correct import for jwt operations
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func
from passlib.context import CryptContext # For password hashing
from ..database import get_session
import app.models as models

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# --- Password Hashing Context ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Configuration ---
# You MUST change this in a production environment! Use a strong, random string.
SECRET_KEY = "super-secret-key-that-should-be-in-env-vars-and-long-and-random-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # Token expires in 7 days (for dev convenience)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login") # Point to your login endpoint

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Default 15 mins
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependency to get current authenticated user ---
async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> models.User:
    """Decodes JWT and retrieves the user from the database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") # 'sub' typically holds the user ID
        username: str = payload.get("username")
        if user_id is None or username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.get(models.User, user_id) # Retrieve user by ID
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Ensures the authenticated user is also active/verified."""
    if not current_user.is_verified: # Check the is_verified field
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not verified")
    return current_user

# --- Endpoints ---
@router.post(
    "/login",
    response_model=models.Token, # Returns a Token model (JWT)
    summary="User Login",
    description="Authenticates a user with username and password. Returns a JWT access token upon success.",
    operation_id="login_user",
    responses={
        200: {"description": "Successful login, returns JWT token."},
        400: {"model": models.MessageResponse, "description": "Invalid credentials or user not verified."},
    }
)
async def login_user(
    *,
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends() # Standard form for username/password
):
    """
    **Endpoint for user login.**
    Verifies username and password, then checks if the user is verified.
    """
    # Look up user by lowercase username for case-insensitivity
    user = session.exec(select(models.User).where(func.lower(models.User.username) == func.lower(form_data.username))).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password."
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password."
        )

    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not verified. Please contact support."
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id), "username": user.username}, # Store user_id and username in token
        expires_delta=access_token_expires
    )
    
    return models.Token(access_token=access_token, token_type="bearer", username=user.username, user_id=user.user_id)