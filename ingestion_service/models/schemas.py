from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Supported file types"""
    PDF = "pdf"
    DOCX = "docx"


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    message: str
    upload_time: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123abc",
                "filename": "sample.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "status": "uploaded",
                "message": "Document uploaded successfully and queued for processing",
                "upload_time": "2025-10-21T10:30:00"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid file type",
                "detail": "Only PDF and DOCX files are supported"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: datetime