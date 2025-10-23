# Quick Start Guide

Get the Document Ingestion POC running in under 5 minutes.

## Prerequisites Checklist

- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Ollama installed (`curl -fsSL https://ollama.com/install.sh | sh`)
- [ ] Ollama model pulled (`ollama pull qwen3-embedding:latest`)
- [ ] 8GB+ free RAM
- [ ] Port 8000, 8001, 8080, 6379 available

## Setup (3 commands)

```bash
# 1. Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# That's it! Setup script does everything:
# - Creates .env file
# - Starts all services
# - Initializes database and vector store
```

## Verify Installation

```bash
# Check all services are running
docker-compose ps

# Should show 5 services running:
# - redis
# - weaviate
# - ingestion_service
# - processing_service
# - embedding_service
# - query_service
```

## Test the System (2 minutes)

### 1. Upload Documents

```bash
cd evaluation

# Add your test PDFs/DOCX to ../samples/ folder first
# Then run:
./test_ingestion.sh
```

Expected output:
```json
{
  "document_id": "doc_abc123",
  "filename": "sample1.pdf",
  "status": "uploaded",
  "message": "Document uploaded successfully and queued for processing"
}
```

### 2. Wait for Processing

```bash
# Watch the processing logs (wait ~30 seconds)
docker-compose logs -f processing_service embedding_service

# Look for:
# - "Document processing complete"
# - "Embedding generation complete"
# - "Document status updated to completed"
```

Press `Ctrl+C` to stop watching logs.

### 3. Query Documents

```bash
# Still in evaluation/ directory
./test_queries.sh
```

Expected output:
```json
{
  "query": "revenue in 2023",
  "num_results": 3,
  "execution_time_ms": 125.5,
  "results": [...]
}
```

## Using the APIs

### Ingestion API (Port 8000)

**Swagger UI**: http://localhost:8000/docs

Upload a document:
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@/path/to/document.pdf"
```

### Query API (Port 8001)

**Swagger UI**: http://localhost:8001/docs

Search documents:
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"q": "What is the revenue?", "top_k": 5}'
```

List documents:
```bash
curl http://localhost:8001/documents
```

## Common Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f processing_service

# Restart a service
docker-compose restart ingestion_service

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Troubleshooting

### "Ollama connection failed"

```bash
# Check Ollama is running
ollama list

# Test connection from container
docker-compose exec embedding_service curl http://host.docker.internal:11434/api/tags
```

### "Weaviate not ready"

```bash
# Check Weaviate health
curl http://localhost:8080/v1/.well-known/ready

# Restart if needed
docker-compose restart weaviate
sleep 10
```

### "No results found"

1. Check documents are uploaded: `curl http://localhost:8001/documents`
2. Check document status is "completed"
3. Check processing logs: `docker-compose logs processing_service embedding_service`
4. Wait a bit longer - embedding can take 30-60 seconds

### Ports already in use

Edit `.env` and change:
```bash
API_INGESTION_PORT=8000  # Change to available port
API_QUERY_PORT=8001      # Change to available port
```

Then rebuild:
```bash
docker-compose down
docker-compose up -d
```


# Structure

```
document-ingestion-poc/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
├── ingestion_service/              # File upload & job submission
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── ingest.py               # POST /ingest
│   │   └── health.py               # GET /health
│   └── models/
│       └── schemas.py
│
├── query_service/                  # Search & retrieval API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── query.py                # POST /query
│   │   └── health.py               # GET /health
│   └── models/
│       └── schemas.py
│
├── processing_service/             # Document parsing & semantic chunking
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── worker.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── process_document.py
│   └── processors/
│       ├── __init__.py
│       ├── pdf_processor.py
│       ├── docx_processor.py
│       └── semantic_chunker.py     # LangChain SemanticChunker
│
├── embedding_service/              # qwen3-embedding:latest via Ollama
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── worker.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── embed_document.py
│   └── models/
│       ├── __init__.py
│       └── ollama_embedder.py      # Ollama client wrapper
│
├── shared/                         # Common utilities & configs
│   ├── __init__.py
│   ├── config.py
│   ├── database.py                 # SQLite models
│   ├── vector_store.py             # Weaviate via LangChain
│   ├── redis_queue.py              # RQ utilities
│   ├── logger.py
│   └── schemas.py
│
├── storage/                        # Local storage for files & data
│   ├── uploads/
│   ├── vectordb/
│   └── metadata.db
│
├── samples/                        # Sample documents & queries
│   ├── sample1.pdf
│   ├── sample2.docx
│   └── test_queries.json
│
├── evaluation/                     # Integration tests & evaluation scripts
│   ├── test_ingestion.sh
│   ├── test_queries.sh
│   ├── test_queries.py
│   └── results/
│
└── scripts/                        # Setup & initialization scripts
    ├── init_weaviate.py
    ├── init_db.py
    └── seed_samples.sh
```