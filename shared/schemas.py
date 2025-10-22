from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ProcessingJobData(BaseModel):
    """Schema for processing job data"""
    document_id: str
    file_path: str
    file_type: str


class EmbeddingJobData(BaseModel):
    """Schema for embedding job data"""
    document_id: str
    chunks: List[Dict[str, Any]]
    

class ChunkData(BaseModel):
    """Schema for chunk data"""
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    chunk_size: int
    metadata: Optional[Dict[str, Any]] = None


class DocumentMetadata(BaseModel):
    """Schema for document metadata"""
    document_id: str
    filename: str
    file_path: str
    file_type: str
    file_size: int
    status: str
    upload_time: datetime
    processing_started_time: Optional[datetime] = None
    processing_completed_time: Optional[datetime] = None
    error_message: Optional[str] = None