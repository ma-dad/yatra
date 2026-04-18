from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from app.database import init_db
from app.routers import auth, requests, matches, calendar
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Cleanup on shutdown (if needed)
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title="Yatra Platform API",
    description="Community travel assistance platform - Phase 1",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(requests.router, prefix="/api/requests", tags=["Requests"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])

# Mount static files if directory exists
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Root endpoint - serve homepage"""
    static_index = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    
    return {
        "message": "Yatra Platform API - Phase 1",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
