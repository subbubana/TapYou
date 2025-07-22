from sqlmodel import create_engine, Session, SQLModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please create a .env file.")

# Create the engine
engine = create_engine(DATABASE_URL, echo=True) # echo=True for logging SQL queries

def create_db_and_tables():
    """
    Creates all database tables defined by SQLModel metadata.
    (This function is called by init_db.py, not main.py directly now)
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Dependency to yield a database session for FastAPI endpoints.
    The session is automatically closed after the request.
    """
    with Session(engine) as session:
        yield session