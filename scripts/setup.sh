#!/bin/bash

# Setup script for Document Ingestion POC

set -e

echo "================================"
echo "Document Ingestion POC Setup"
echo "================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo " Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✓ Docker Compose found"

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠ Ollama is not installed. Please install Ollama:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Ollama found"
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "⚠ Ollama is not running. Starting Ollama..."
        ollama serve &
        sleep 5
    fi
    echo "✓ Ollama is running"
    
    # Check if model is pulled
    if ! ollama list | grep -q "qwen3-embedding:latest"; then
        echo "⚠ Model qwen3-embedding:latest not found. Pulling model..."
        ollama pull qwen3-embedding:latest
    fi
    echo "✓ Model qwen3-embedding:latest is available"
fi

# Check jq (optional, for testing)
if ! command -v jq &> /dev/null; then
    echo "⚠ jq is not installed (optional, needed for test scripts)"
    echo "  Install: sudo apt install jq  (Ubuntu/Debian)"
    echo "           brew install jq       (macOS)"
else
    echo "✓ jq found"
fi

echo ""
echo "================================"

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi

# Create directories
echo "Creating directories..."
mkdir -p storage/uploads
mkdir -p storage/vectordb
mkdir -p evaluation/results
mkdir -p samples
echo "✓ Directories created"

# Make scripts executable
echo "Making scripts executable..."
chmod +x evaluation/test_ingestion.sh
chmod +x evaluation/test_queries.sh
chmod +x evaluation/test_queries.py
chmod +x scripts/setup.sh
echo "✓ Scripts are executable"

echo ""
echo "================================"
echo "Building and starting services..."
echo "================================"
echo ""

# Build and start services
docker-compose up -d --build

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Wait for Weaviate
echo -n "Waiting for Weaviate..."
for i in {1..30}; do
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Redis
echo -n "Waiting for Redis..."
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Ingestion service
echo -n "Waiting for Ingestion service..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Query service
echo -n "Waiting for Query service..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "================================"
echo "Initializing database and vector store..."
echo "================================"
echo ""

# Initialize SQLite database
echo "Initializing SQLite database..."
docker-compose exec -T ingestion_service python /app/scripts/init_db.py
echo "✓ Database initialized"

# Initialize Weaviate schema
echo "Initializing Weaviate schema..."
docker-compose exec -T embedding_service python /app/scripts/init_weaviate.py
echo "✓ Weaviate schema initialized"

echo ""
echo "================================"
echo "✓ Setup Complete!"
echo "================================"
echo ""
echo "Services are running:"
echo "  - Ingestion API:  http://localhost:8000"
echo "  - Query API:      http://localhost:8001"
echo "  - Weaviate:       http://localhost:8080"
echo "  - Redis:          localhost:6379"
echo ""
echo "API Documentation:"
echo "  - Ingestion Swagger: http://localhost:8000/docs"
echo "  - Query Swagger:     http://localhost:8001/docs"
echo ""
echo "Next steps:"
echo "  1. Upload sample documents:"
echo "     cd evaluation && ./test_ingestion.sh"
echo ""
echo "  2. Wait for processing (check logs):"
echo "     docker-compose logs -f processing_service embedding_service"
echo ""
echo "  3. Test queries:"
echo "     cd evaluation && ./test_queries.sh"
echo ""
echo "  4. Run full evaluation:"
echo "     cd evaluation && python test_queries.py"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo "" found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo "✓ Docker