from fastapi import FastAPI
from app.routers import user_router, task_router # Import the new routers

# Initialize FastAPI application
app = FastAPI(
    title="Modular Task Management API",
    description="A backend API for managing modular tasks and users. Users must be created before tasks can be assigned to them.",
    version="0.1.0",
)

# Include the routers
app.include_router(user_router.router)
app.include_router(task_router.router)

# No more direct endpoint definitions or helper functions here, they are in the routers.
# The database creation logic is in init_db.py, run separately.