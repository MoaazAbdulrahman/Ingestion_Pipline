from fastapi import APIRouter
from datetime import datetime

import sys
sys.path.append('/app/shared')
from vector_store import get_weaviate_client
from config import get_ollama_url
from logger import get_logger

from models.schemas import HealthResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Checks connection to Weaviate and Ollama
    """
    weaviate_connected = False
    ollama_connected = False
    
    # Check Weaviate
    try:
        client = get_weaviate_client()
        weaviate_connected = client.is_ready()
        client.close()
    except Exception as e:
        logger.warning(f"Weaviate health check failed: {str(e)}")
    
    # Check Ollama (basic connectivity check)
    try:
        import requests
        response = requests.get(f"{get_ollama_url()}/api/tags", timeout=5)
        ollama_connected = response.status_code == 200
    except Exception as e:
        logger.warning(f"Ollama health check failed: {str(e)}")
    
    return HealthResponse(
        status="healthy" if (weaviate_connected and ollama_connected) else "degraded",
        service="query_service",
        timestamp=datetime.now(),
        weaviate_connected=weaviate_connected,
        ollama_connected=ollama_connected
    )