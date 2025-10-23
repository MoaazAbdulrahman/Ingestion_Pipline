# Architecture Documentation

## System Overview

This document ingestion POC implements a microservices-based architecture for processing, embedding, and querying documents using semantic search.

## Core Components

### 1. Ingestion Service
**Technology**: FastAPI  
**Port**: 8000  
**Purpose**: Accept document uploads and initiate processing pipeline

**Responsibilities**:
- File upload validation (type, size)
- Document metadata creation in SQLite
- Job submission to Redis processing queue
- API endpoint for document ingestion

**Key Features**:
- Supports PDF and DOCX formats
- File size validation (max 50MB)
- Idempotent uploads
- Swagger/OpenAPI documentation

### 2. Processing Service
**Technology**: Python, RQ Worker  
**Purpose**: Parse documents and create semantic chunks

**Responsibilities**:
- PDF text extraction (pypdf)
- DOCX text extraction (python-docx)
- Semantic chunking (LangChain RecursiveCharacterTextSplitter)
- Chunk storage in SQLite
- Job submission to Redis embedding queue

**Processing Pipeline**:
```
Document → Parse → Extract Text → Semantic Chunk → Store → Queue Embedding
```

**Chunking Strategy**:
- Uses RecursiveCharacterTextSplitter from LangChain
- Prioritizes semantic boundaries (paragraphs, sentences)
- Configurable chunk size (default: 512 chars)
- Configurable overlap (default: 50 chars)

### 3. Embedding Service
**Technology**: Python, RQ Worker, Ollama, LangChain  
**Purpose**: Generate embeddings and store in vector database

**Responsibilities**:
- Generate embeddings using Ollama (Qwen3-8B model)
- Store vectors in Weaviate via LangChain
- Update document status to "completed"

**Embedding Pipeline**:
```
Chunks → Ollama Embeddings → Weaviate Storage → Update Status
```

**Key Features**:
- Uses official langchain-ollama package
- Batch embedding processing
- Metadata preservation
- Error handling and status updates

### 4. Query Service
**Technology**: FastAPI  
**Port**: 8001  
**Purpose**: Semantic search and document retrieval

**Responsibilities**:
- Accept search queries
- Generate query embeddings via Ollama
- Perform vector similarity search in Weaviate
- Return ranked results with metadata

**API Endpoints**:
- `POST /query` - Semantic search
- `GET /documents` - List all documents
- `GET /documents/{id}` - Get document details
- `GET /health` - Health check

**Search Features**:
- Configurable top-k results
- Filter by document_id
- Filter by file_type
- Metadata-rich results

### 5. Shared Module
**Technology**: Python  
**Purpose**: Common utilities and configuration

**Components**:
- `config.py` - Environment configuration
- `database.py` - SQLite operations
- `vector_store.py` - Weaviate integration
- `redis_queue.py` - Job queue management
- `logger.py` - Structured logging
- `schemas.py` - Shared data models

## Infrastructure Components

### Redis
**Purpose**: Message queue for async job processing  
**Port**: 6379  
**Queues**:
- `processing` - Document parsing jobs
- `embedding` - Embedding generation jobs

### Weaviate
**Purpose**: Vector database for embeddings  
**Ports**: 8080 (HTTP), 50051 (gRPC)  
**Configuration**:
- Anonymous access enabled (for POC)
- No default vectorizer (using Ollama)
- Persistent storage

### SQLite
**Purpose**: Metadata and document tracking  
**Location**: `/app/storage/metadata.db`  
**Tables**:
- `documents` - Document metadata and status
- `chunks` - Text chunks with references

### Ollama
**Purpose**: Embedding model inference  
**Port**: 11434 (host machine)  
**Model**: qwen3-embedding:latest (configurable)  
**Connection**: Via host.docker.internal

## Data Flow

### Document Ingestion Flow
```
1. User uploads file → Ingestion Service
2. Validate file (type, size)
3. Save file to storage/uploads/
4. Create document record in SQLite (status: uploaded)
5. Push job to Redis queue "processing"
6. Return document_id to user

--- Async Processing Begins ---

7. Processing worker picks up job
8. Parse document (PDF/DOCX)
9. Extract text and metadata
10. Chunk text semantically
11. Save chunks to SQLite
12. Update document status (processing)
13. Push job to Redis queue "embedding"

14. Embedding worker picks up job
15. Generate embeddings via Ollama
16. Store embeddings in Weaviate
17. Update document status (completed)
```

### Query Flow
```
1. User sends search query → Query Service
2. Generate query embedding via Ollama
3. Search Weaviate for similar vectors
4. Apply filters (document_id, file_type)
5. Retrieve top-k results
6. Return ranked chunks with metadata
```

## Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    status TEXT NOT NULL,
    upload_time TIMESTAMP NOT NULL,
    processing_started_time TIMESTAMP,
    processing_completed_time TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Chunks Table
```sql
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);
```

## Weaviate Schema

### DocumentChunk Collection
```python
{
    "name": "DocumentChunk",
    "properties": [
        {"name": "document_id", "dataType": ["text"]},
        {"name": "chunk_id", "dataType": ["text"]},
        {"name": "chunk_index", "dataType": ["int"]},
        {"name": "text", "dataType": ["text"]},
        {"name": "filename", "dataType": ["text"]},
        {"name": "file_type", "dataType": ["text"]}
    ],
    "vectorizer": "none"  # Using Ollama externally
}
```

## Security Considerations (POC)

**Current State** (suitable for POC only):
- No authentication/authorization
- Anonymous Weaviate access
- No input sanitization
- No rate limiting
- Plain HTTP (no TLS)

**For Production**:
- Add JWT/OAuth authentication
- Enable Weaviate authentication
- Input validation and sanitization
- Rate limiting per user/IP
- TLS/HTTPS for all services
- Network policies in Kubernetes
- Secrets management (Vault/K8s Secrets)

## Scalability

### Current Limitations (POC)
- Single instance of each worker
- No load balancing
- Redis without persistence
- Local file storage

### Production Scaling
- Horizontal worker scaling via Docker replicas
- Load balancer for API services
- Redis cluster with persistence
- Distributed file storage (S3/MinIO)
- Kubernetes deployment with HPA
- Caching layer (Redis/Memcached)

## Monitoring & Observability

### Current Implementation
- Structured JSON logging to stdout
- Health check endpoints
- Basic error tracking

### Production Additions
- Prometheus metrics
- Grafana dashboards
- Distributed tracing (Jaeger/OpenTelemetry)
- Log aggregation (ELK/Loki)
- Alert management
- Performance monitoring

## Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| API Framework | FastAPI | Async, auto-docs, type safety |
| Job Queue | Redis + RQ | Simple, reliable, Python-native |
| Vector DB | Weaviate | Production-ready, LangChain integration |
| Embeddings | Ollama + Qwen3 | Local inference, no API costs |
| Text Processing | LangChain | Semantic chunking, ecosystem |
| Document Parsing | pypdf, python-docx | Standard libraries, reliable |
| Metadata DB | SQLite | Simple, file-based, no server needed |
| Containerization | Docker | Standard, portable |
| Orchestration | Docker Compose | POC-appropriate, K8s-ready |

## Configuration

### Environment Variables
See `.env.example` for full list. Key settings:

```bash
# File Processing
MAX_FILE_SIZE=52428800  # 50MB
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Services
REDIS_HOST=redis
WEAVIATE_HOST=weaviate
OLLAMA_HOST=host.docker.internal
OLLAMA_MODEL=qwen3-embedding:latest

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Development Guidelines

### Adding New File Formats
1. Create processor in `processing_service/processors/`
2. Implement `extract_text()` and `validate_file()` methods
3. Update file type validation in `ingestion_service`
4. Add tests

### Adding New Features
1. Update shared module if needed
2. Implement in appropriate service
3. Update API schemas
4. Add documentation
5. Create tests

### Code Structure
- Keep services stateless
- Use shared module for common code
- Follow existing patterns
- Add type hints
- Write docstrings
- Use structured logging

## Testing Strategy

### Unit Tests
- Test individual processors
- Test chunking logic
- Test database operations
- Mock external dependencies

### Integration Tests
- Test API endpoints
- Test full pipeline
- Test error handling
- Test edge cases

### Performance Tests
- Test with large documents
- Test concurrent uploads
- Test query performance
- Test scalability

## Deployment

### Docker Compose (Current)
```bash
docker-compose up -d
```

### Kubernetes (Future)
- See `k8s/` directory
- Deploy with Helm or Kustomize
- Configure HPA for workers
- Set resource limits
- Configure persistent volumes

## Troubleshooting Guide

See README.md for common issues and solutions.

## Future Enhancements

1. **Multi-language support** - Language detection and multilingual embeddings
2. **Multimodal processing** - Extract and embed images, tables
3. **Incremental updates** - Update documents without reprocessing
4. **Advanced chunking** - Custom strategies per document type
5. **Deduplication** - SHA256-based duplicate detection
6. **Batch upload** - Process multiple files at once
7. **Webhooks** - Notify external systems on completion
8. **Export** - Download processed data
9. **Analytics** - Usage stats and metrics
10. **Admin UI** - Web interface for management