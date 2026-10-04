import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.config import settings
from backend.app.db.database import init_db
from backend.app.api.v1 import api_v1_router, ws_router
import backend.app.tools  # Register all tools
import backend.app.agents  # Register all agents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("desktop_ai.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Universal Autonomous Desktop AI...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down Universal Autonomous Desktop AI.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Universal Autonomous Desktop AI - Intelligent Desktop Operating Assistant",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)
app.include_router(ws_router)

# Mount frontend if build directory exists
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "OPERATIONAL",
        "autonomy_level": settings.DEFAULT_AUTONOMY_LEVEL,
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }
