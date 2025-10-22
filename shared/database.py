import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from contextlib import contextmanager
from config import settings
from logger import get_logger

logger = get_logger(__name__)


# Database schema
SCHEMA = """
-- Documents table
CREATE TABLE IF NOT EXISTS documents (
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

-- Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    metadata TEXT,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_time ON documents(upload_time);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON chunks(document_id, chunk_index);
"""


@contextmanager
def get_db_connection():
    """
    Context manager for database connections
    """
    # Ensure directory exists
    db_path = Path(settings.SQLITE_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(settings.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        conn.close()


def init_database():
    """
    Initialize database schema
    """
    try:
        with get_db_connection() as conn:
            conn.executescript(SCHEMA)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def create_document_record(metadata: Dict[str, Any]) -> bool:
    """
    Create a new document record
    
    Args:
        metadata: Document metadata dictionary
    
    Returns:
        True if successful
    """
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO documents (
                    document_id, filename, file_path, file_type, 
                    file_size, status, upload_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata["document_id"],
                metadata["filename"],
                metadata["file_path"],
                metadata["file_type"],
                metadata["file_size"],
                metadata["status"],
                metadata["upload_time"]
            ))
        logger.info(f"Document record created: {metadata['document_id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to create document record: {str(e)}")
        raise


def update_document_status(
    document_id: str, 
    status: str, 
    error_message: Optional[str] = None
) -> bool:
    """
    Update document processing status
    
    Args:
        document_id: Document ID
        status: New status
        error_message: Optional error message
    
    Returns:
        True if successful
    """
    try:
        with get_db_connection() as conn:
            timestamp_field = None
            if status == "processing":
                timestamp_field = "processing_started_time"
            elif status in ["completed", "failed"]:
                timestamp_field = "processing_completed_time"
            
            if timestamp_field:
                conn.execute(f"""
                    UPDATE documents 
                    SET status = ?, 
                        {timestamp_field} = ?,
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = ?
                """, (status, datetime.now(), error_message, document_id))
            else:
                conn.execute("""
                    UPDATE documents 
                    SET status = ?, 
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = ?
                """, (status, error_message, document_id))
        
        logger.info(f"Document status updated: {document_id} -> {status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update document status: {str(e)}")
        raise


def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve document metadata by ID
    
    Args:
        document_id: Document ID
    
    Returns:
        Document metadata dictionary or None
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?",
                (document_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except Exception as e:
        logger.error(f"Failed to retrieve document: {str(e)}")
        raise


def create_chunk_records(chunks: List[Dict[str, Any]]) -> bool:
    """
    Create multiple chunk records
    
    Args:
        chunks: List of chunk dictionaries
    
    Returns:
        True if successful
    """
    try:
        with get_db_connection() as conn:
            conn.executemany("""
                INSERT INTO chunks (
                    chunk_id, document_id, chunk_index, 
                    chunk_text, chunk_size, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                (
                    chunk["chunk_id"],
                    chunk["document_id"],
                    chunk["chunk_index"],
                    chunk["chunk_text"],
                    chunk["chunk_size"],
                    chunk.get("metadata", "{}")
                ) for chunk in chunks
            ])
        logger.info(f"Created {len(chunks)} chunk records")
        return True
    except Exception as e:
        logger.error(f"Failed to create chunk records: {str(e)}")
        raise


def get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all chunks for a document
    
    Args:
        document_id: Document ID
    
    Returns:
        List of chunk dictionaries
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
                (document_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to retrieve chunks: {str(e)}")
        raise


def get_all_documents(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all documents, optionally filtered by status
    
    Args:
        status: Optional status filter
    
    Returns:
        List of document dictionaries
    """
    try:
        with get_db_connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM documents WHERE status = ? ORDER BY upload_time DESC",
                    (status,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM documents ORDER BY upload_time DESC"
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to retrieve documents: {str(e)}")
        raise