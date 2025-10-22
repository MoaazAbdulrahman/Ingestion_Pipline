# Shared module initialization
from .config import settings, get_redis_url, get_weaviate_url, get_ollama_url
from .logger import get_logger, log_with_context
from .database import (
    init_database,
    create_document_record,
    update_document_status,
    get_document,
    create_chunk_records,
    get_document_chunks,
    get_all_documents
)
from .redis_queue import (
    get_redis_connection,
    get_queue,
    enqueue_processing_job,
    enqueue_embedding_job,
    get_job_status,
    get_queue_stats
)
from .vector_store import (
    get_weaviate_client,
    init_weaviate_schema,
    get_vector_store,
    add_documents_to_vectorstore,
    search_similar_documents,
    delete_document_chunks
)
from .schemas import (
    ProcessingJobData,
    EmbeddingJobData,
    ChunkData,
    DocumentMetadata
)

__all__ = [
    # Config
    'settings',
    'get_redis_url',
    'get_weaviate_url',
    'get_ollama_url',
    # Logger
    'get_logger',
    'log_with_context',
    # Database
    'init_database',
    'create_document_record',
    'update_document_status',
    'get_document',
    'create_chunk_records',
    'get_document_chunks',
    'get_all_documents',
    # Redis Queue
    'get_redis_connection',
    'get_queue',
    'enqueue_processing_job',
    'enqueue_embedding_job',
    'get_job_status',
    'get_queue_stats',
    # Vector Store
    'get_weaviate_client',
    'init_weaviate_schema',
    'get_vector_store',
    'add_documents_to_vectorstore',
    'search_similar_documents',
    'delete_document_chunks',
    # Schemas
    'ProcessingJobData',
    'EmbeddingJobData',
    'ChunkData',
    'DocumentMetadata'
]