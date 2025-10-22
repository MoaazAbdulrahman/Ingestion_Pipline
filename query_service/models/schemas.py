from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for document query"""
    q: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)
    document_id: Optional[str] = Field(None, description="Filter by specific document ID")
    file_type: Optional[str] = Field(None, description="Filter by file type (pdf, docx)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "q": "What is the revenue in 2023?",
                "top_k": 5,
                "document_id": None,
                "file_type": None
            }
        }


class ChunkResult(BaseModel):
    """Individual chunk result"""
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    score: Optional[float] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_abc123",
                "document_id": "doc_xyz789",
                "chunk_index": 0,
                "text": "The revenue in 2023 was $10M...",
                "score": 0.85,
                "metadata": {
                    "filename": "report.pdf",
                    "file_type": "pdf"
                }
            }
        }


class QueryResponse(BaseModel):
    """Response model for document query"""
    query: str
    num_results: int
    results: List[ChunkResult]
    execution_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the revenue in 2023?",
                "num_results": 3,
                "results": [
                    {
                        "chunk_id": "chunk_abc123",
                        "document_id": "doc_xyz789",
                        "chunk_index": 0,
                        "text": "The revenue in 2023 was $10M...",
                        "score": 0.85,
                        "metadata": {"filename": "report.pdf"}
                    }
                ],
                "execution_time_ms": 125.5
            }
        }


class DocumentInfo(BaseModel):
    """Document information model"""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    upload_time: datetime
    num_chunks: int


class DocumentListResponse(BaseModel):
    """Response model for listing documents"""
    total_documents: int
    documents: List[DocumentInfo]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: datetime
    weaviate_connected: bool
    ollama_connected: bool