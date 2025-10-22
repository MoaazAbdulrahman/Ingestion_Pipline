from langchain_ollama import OllamaEmbeddings

import sys
sys.path.append('/app/shared')
from config import settings, get_ollama_url
from logger import get_logger

logger = get_logger(__name__)


def get_ollama_embedder() -> OllamaEmbeddings:
    """
    Get configured Ollama embeddings instance
    
    Returns:
        OllamaEmbeddings instance
    """
    logger.info(f"Initializing OllamaEmbeddings with model: {settings.OLLAMA_MODEL}")
    logger.info(f"Ollama base URL: {get_ollama_url()}")
    
    embeddings = OllamaEmbeddings(
        model=settings.OLLAMA_MODEL,
        base_url=get_ollama_url(),
    )
    
    logger.info("OllamaEmbeddings initialized successfully")
    
    return embeddings