from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Service Names
    SERVICE_NAME: str = "document-ingestion-poc"
    
    # Storage Paths
    UPLOAD_DIR: str = "/app/storage/uploads"
    VECTORDB_DIR: str = "/app/storage/vectordb"
    SQLITE_DB_PATH: str = "/app/storage/metadata.db"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 52428800  # 50MB in bytes
    
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Redis Queue Names
    QUEUE_PROCESSING: str = "processing"
    QUEUE_EMBEDDING: str = "embedding"
    
    # Weaviate Configuration
    WEAVIATE_HOST: str = "weaviate"
    WEAVIATE_PORT: int = 8080
    WEAVIATE_GRPC_PORT: int = 50051
    WEAVIATE_SCHEME: str = "http"
    
    # Ollama Configuration (for embeddings)
    OLLAMA_HOST: str = "host.docker.internal"  # Access host machine
    OLLAMA_PORT: int = 11434
    OLLAMA_MODEL: str = "qwen3-embedding:latest"  # Adjust based on your Ollama setup
    
    # Chunking Configuration
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # API Configuration
    API_INGESTION_PORT: int = 8000
    API_QUERY_PORT: int = 8001
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_redis_url() -> str:
    """
    Construct Redis connection URL
    """
    if settings.REDIS_PASSWORD:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


def get_weaviate_url() -> str:
    """
    Construct Weaviate connection URL
    """
    return f"{settings.WEAVIATE_SCHEME}://{settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT}"


def get_ollama_url() -> str:
    """
    Construct Ollama API URL
    """
    return f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"