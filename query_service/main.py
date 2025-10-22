from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import sys
sys.path.append('/app/shared')
from logger import get_logger
from config import settings

from routes import query, health

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Query Service...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Ollama Model: {settings.OLLAMA_MODEL}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Query Service...")


# Create FastAPI app
app = FastAPI(
    title="Document Query Service",
    description="Microservice for semantic search and document retrieval",
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
app.include_router(query.router, tags=["Query"])


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "service": "query_service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "POST /query",
            "list_documents": "GET /documents",
            "get_document": "GET /documents/{document_id}",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )