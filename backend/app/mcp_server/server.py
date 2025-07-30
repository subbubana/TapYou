# backend/app/mcp_server/server.py
from fastapi_mcp import FastApiMCP
from app.main import app as fastapi_app  # Import FastAPI app WITH registered routers

mcp = FastApiMCP(fastapi_app)
mcp.mount()  # Exposes all /api as MCP tools at /mcp

app = fastapi_app  # To allow `uvicorn app.mcp_server.server:app`

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.mcp_server.server:app", host="0.0.0.0", port=9000, reload=True)
