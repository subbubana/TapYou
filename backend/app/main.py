from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user_router, task_router, auth_router, chat_router # Import the new routers
import os
from dotenv import load_dotenv
from fastapi_mcp import FastApiMCP
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="Modular Task Management API",
    description="A robust backend API providing comprehensive management for users and their to-do tasks. Features secure user authentication and the ability to organize tasks into modular units.",
    version="0.1.0",
)

origins = [
    "http://localhost:3000", # Your React app's address
    # You can add more origins here if your frontend might run on different addresses
    "http://127.0.0.1:3000", # Sometimes browsers use 127.0.0.1 explicitly
    "http://localhost:9000",
    "http://127.0.0.1:9000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # List of origins that are allowed to make cross-origin requests
    allow_credentials=True,             # Allow cookies to be included in cross-origin requests
    allow_methods=["*"],                # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],                # Allow all headers in the request
)

# Include the routers
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(task_router.router)
app.include_router(chat_router.router)

# Mount MCP functionality
mcp = FastApiMCP(app)
mcp.mount()

# No more direct endpoint definitions or helper functions here, they are in the routers.
# The database creation logic is in init_db.py, run separately.

mcp_app = FastAPI()
mcp = FastApiMCP(app)
mcp.mount(mcp_app)
