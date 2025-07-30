# init_db.py
import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please create a .env file.")

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """
    Creates all database tables defined by SQLModel metadata.
    This function should be run ONLY ONCE to initialize the database schema.
    """
    # Ensure all models are imported so SQLModel.metadata knows about them
    # This imports the User and Task models, making them known to SQLModel
    from app.models import User, Task, ChatMessage
    print("Attempting to create database tables (users and tasks) if they don't exist...")
    SQLModel.metadata.create_all(engine)
    print("Database tables created/checked successfully.")

if __name__ == "__main__":
    create_db_and_tables()