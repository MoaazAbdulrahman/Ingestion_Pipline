FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy shared and scripts from parent context
COPY shared /app/shared
COPY scripts /app/scripts

# Copy service-specific requirements
COPY ingestion_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY ingestion_service/ .

# Create directories
RUN mkdir -p /app/storage/uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]