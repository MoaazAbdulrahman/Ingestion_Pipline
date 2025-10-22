import time
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional

import sys
sys.path.append('/app/shared')
from config import settings
from logger import get_logger
from vector_store import get_vector_store, search_similar_documents
from database import get_all_documents, get_document_chunks

from models.schemas import (
    QueryRequest,
    QueryResponse,
    ChunkResult,
    DocumentListResponse,
    DocumentInfo
)

# Import Ollama embeddings
from langchain_ollama import OllamaEmbeddings

router = APIRouter()
logger = get_logger(__name__)

# Global embedder instance (initialized on first use)
_embedder = None


def get_embedder():
    """Get or create embedder instance"""
    global _embedder
    if _embedder is None:
        from config import get_ollama_url
        logger.info("Initializing Ollama embedder for queries...")
        _embedder = OllamaEmbeddings(
            model=settings.OLLAMA_MODEL,
            base_url=get_ollama_url()
        )
    return _embedder


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents using semantic search
    
    Args:
        request: Query request with search parameters
    
    Returns:
        Query results with relevant chunks
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: '{request.q}'")
        logger.info(f"Parameters: top_k={request.top_k}, document_id={request.document_id}, file_type={request.file_type}")
        
        # Step 1: Get embedder
        embedder = get_embedder()
        
        # Step 2: Get vector store
        vector_store = get_vector_store(embedder)
        
        # Step 3: Build filter if needed
        filter_dict = None
        if request.document_id or request.file_type:
            filter_dict = {}
            if request.document_id:
                filter_dict["document_id"] = request.document_id
            if request.file_type:
                filter_dict["file_type"] = request.file_type
        
        # Step 4: Search
        logger.info("Executing semantic search...")
        results = search_similar_documents(
            vector_store=vector_store,
            query=request.q,
            k=request.top_k,
            filter_dict=filter_dict
        )
        
        # Step 5: Format results
        chunk_results = []
        for doc in results:
            chunk_result = ChunkResult(
                chunk_id=doc.metadata.get("chunk_id", ""),
                document_id=doc.metadata.get("document_id", ""),
                chunk_index=doc.metadata.get("chunk_index", 0),
                text=doc.page_content,
                score=doc.metadata.get("score"),  # If available
                metadata={
                    "filename": doc.metadata.get("filename", ""),
                    "file_type": doc.metadata.get("file_type", ""),
                    **{k: v for k, v in doc.metadata.items() 
                       if k not in ["chunk_id", "document_id", "chunk_index", "filename", "file_type"]}
                }
            )
            chunk_results.append(chunk_result)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(f"Query completed: {len(chunk_results)} results in {execution_time:.2f}ms")
        
        return QueryResponse(
            query=request.q,
            num_results=len(chunk_results),
            results=chunk_results,
            execution_time_ms=round(execution_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(status_filter: Optional[str] = None):
    """
    List all documents
    
    Args:
        status_filter: Optional filter by status (uploaded, processing, completed, failed)
    
    Returns:
        List of documents with metadata
    """
    try:
        logger.info(f"Listing documents (filter: {status_filter})")
        
        # Get documents from database
        documents = get_all_documents(status=status_filter)
        
        # Format response
        doc_infos = []
        for doc in documents:
            # Get chunk count
            chunks = get_document_chunks(doc["document_id"])
            
            doc_info = DocumentInfo(
                document_id=doc["document_id"],
                filename=doc["filename"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                status=doc["status"],
                upload_time=doc["upload_time"],
                num_chunks=len(chunks)
            )
            doc_infos.append(doc_info)
        
        logger.info(f"Found {len(doc_infos)} documents")
        
        return DocumentListResponse(
            total_documents=len(doc_infos),
            documents=doc_infos
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/documents/{document_id}")
async def get_document_details(document_id: str):
    """
    Get details for a specific document including all chunks
    
    Args:
        document_id: Document ID
    
    Returns:
        Document metadata and chunks
    """
    try:
        from database import get_document
        
        logger.info(f"Getting document details: {document_id}")
        
        # Get document
        doc = get_document(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Get chunks
        chunks = get_document_chunks(document_id)
        
        return {
            "document": doc,
            "num_chunks": len(chunks),
            "chunks": chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )