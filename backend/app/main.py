from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

# 1. Load environment variables from project root .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# 2. Import routers (relative to this package)
from .api import chat
from .api import tasks
from .api import snippets
from .api import conversations
from .api import system_monitor

# Initialize the FastAPI application
app = FastAPI(
    title="ARIS Cyber-Cockpit Core",
    description="Backend for AI-Powered Developer HUD & Personal Assistant",
    version="2.0.0"
)

# Configure CORS for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers BEFORE static mount so they take priority
app.include_router(chat.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(snippets.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(system_monitor.router, prefix="/api")

# Resolve frontend path
frontend_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))

# Serve index.html at the root URL
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# Mount frontend static assets (CSS, JS, images, sounds)
if os.path.isdir(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")