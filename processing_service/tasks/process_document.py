import uuid
from typing import Dict, Any
from pathlib import Path

import sys
sys.path.append('/app/shared')
from config import settings
from logger import get_logger
from database import update_document_status, create_chunk_records
from redis_queue import enqueue_embedding_job

from processors import PDFProcessor, DOCXProcessor, SemanticChunker

logger = get_logger(__name__)


def process_document_task(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process document: parse and chunk
    
    This is the main task executed by RQ worker
    
    Args:
        job_data: Dictionary containing:
            - document_id: Document ID
            - file_path: Path to file
            - file_type: File type (pdf, docx)
    
    Returns:
        Result dictionary with chunk information
    """
    document_id = job_data.get("document_id")
    file_path = job_data.get("file_path")
    file_type = job_data.get("file_type")
    
    logger.info(f"Starting document processing: {document_id}")
    
    try:
        # Update status to processing
        update_document_status(document_id, "processing")
        
        # Step 1: Select appropriate processor
        if file_type == "pdf":
            processor = PDFProcessor()
        elif file_type == "docx":
            processor = DOCXProcessor()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Step 2: Validate file
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not processor.validate_file(file_path):
            raise ValueError(f"Invalid or corrupted file: {file_path}")
        
        # Step 3: Extract text
        logger.info(f"Extracting text from {file_type}: {file_path}")
        extraction_result = processor.extract_text(file_path)
        
        text = extraction_result["text"]
        doc_metadata = extraction_result["metadata"]
        
        logger.info(f"Extracted {len(text)} characters from document")
        
        # Step 4: Chunk text using semantic chunker
        logger.info("Starting semantic chunking...")
        chunker = SemanticChunker()
        
        chunk_metadata = {
            "document_id": document_id,
            "file_type": file_type,
            **doc_metadata
        }
        
        chunks = chunker.chunk_text(text, metadata=chunk_metadata)
        
        # Get chunk statistics
        stats = chunker.get_chunk_stats(chunks)
        logger.info(f"Chunking complete: {stats}")
        
        # Step 5: Prepare chunks for database and embedding
        chunk_records = []
        for chunk in chunks:
            chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
            
            chunk_record = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "chunk_index": chunk["chunk_index"],
                "chunk_text": chunk["chunk_text"],
                "chunk_size": chunk["chunk_size"],
                "metadata": str(chunk.get("metadata", {}))  # Convert to string for SQLite
            }
            chunk_records.append(chunk_record)
        
        # Step 6: Save chunks to database
        logger.info(f"Saving {len(chunk_records)} chunks to database...")
        create_chunk_records(chunk_records)
        
        # Step 7: Queue embedding job
        logger.info("Queueing embedding job...")
        embedding_job_data = {
            "document_id": document_id,
            "chunks": chunk_records
        }
        
        job_id = enqueue_embedding_job(embedding_job_data)
        logger.info(f"Embedding job queued: {job_id}")
        
        # Step 8: Return result
        result = {
            "document_id": document_id,
            "status": "processed",
            "num_chunks": len(chunk_records),
            "stats": stats,
            "embedding_job_id": job_id
        }
        
        logger.info(f"Document processing complete: {document_id}")
        return result
        
    except Exception as e:
        # Update status to failed
        error_message = f"Processing failed: {str(e)}"
        logger.error(error_message, exc_info=True)
        update_document_status(document_id, "failed", error_message)
        raise