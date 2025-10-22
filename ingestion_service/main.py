from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import sys
sys.path.append('/app/shared')
from logger import get_logger
from config import settings

from routes import ingest, health

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Ingestion Service...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ingestion Service...")


# Create FastAPI app
app = FastAPI(
    title="Document Ingestion Service",
    description="Microservice for uploading and queuing documents for processing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(ingest.router, tags=["Ingestion"])


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "service": "ingestion_service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )