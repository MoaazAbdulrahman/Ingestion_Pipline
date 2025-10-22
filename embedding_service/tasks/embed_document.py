from typing import Dict, Any, List
import json

import sys
sys.path.append('/app/shared')
from config import settings
from logger import get_logger
from database import update_document_status, get_document
from vector_store import get_vector_store, add_documents_to_vectorstore

from models import get_ollama_embedder
from langchain_core.documents import Document

logger = get_logger(__name__)


def embed_document_task(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate embeddings and store in Weaviate
    
    This is the main task executed by RQ worker
    
    Args:
        job_data: Dictionary containing:
            - document_id: Document ID
            - chunks: List of chunk dictionaries
    
    Returns:
        Result dictionary with embedding information
    """
    document_id = job_data.get("document_id")
    chunks = job_data.get("chunks", [])
    
    logger.info(f"Starting embedding generation for document: {document_id}")
    logger.info(f"Number of chunks to embed: {len(chunks)}")
    
    try:
        if not chunks:
            raise ValueError("No chunks provided for embedding")
        
        # Step 1: Initialize Ollama embedder
        logger.info("Initializing Ollama embedder...")
        embedder = get_ollama_embedder()
        
        # Step 2: Get document metadata
        doc_metadata = get_document(document_id)
        if not doc_metadata:
            raise ValueError(f"Document not found: {document_id}")
        
        # Step 3: Prepare documents for embedding
        logger.info("Preparing documents for embedding...")
        langchain_docs = []
        
        for chunk in chunks:
            # Parse metadata if it's a string
            chunk_metadata = chunk.get("metadata", {})
            if isinstance(chunk_metadata, str):
                try:
                    chunk_metadata = json.loads(chunk_metadata)
                except:
                    chunk_metadata = {}
            
            # Create metadata for vector store
            metadata = {
                "document_id": document_id,
                "chunk_id": chunk["chunk_id"],
                "chunk_index": chunk["chunk_index"],
                "filename": doc_metadata.get("filename", ""),
                "file_type": doc_metadata.get("file_type", ""),
                **chunk_metadata
            }
            
            # Create LangChain Document
            doc = Document(
                page_content=chunk["chunk_text"],
                metadata=metadata
            )
            langchain_docs.append(doc)
        
        # Step 4: Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = get_vector_store(embedder)
        
        # Step 5: Add documents to vector store (embeddings generated automatically)
        logger.info("Generating embeddings and storing in Weaviate...")
        vector_ids = add_documents_to_vectorstore(
            vector_store=vector_store,
            documents=langchain_docs
        )
        
        logger.info(f"Successfully stored {len(vector_ids)} embeddings in Weaviate")
        
        # Step 6: Update document status to completed
        update_document_status(document_id, "completed")
        logger.info(f"Document status updated to completed: {document_id}")
        
        # Step 7: Return result
        result = {
            "document_id": document_id,
            "status": "completed",
            "num_embeddings": len(vector_ids),
        }
        
        logger.info(f"Embedding generation complete: {document_id}")
        return result
        
    except Exception as e:
        # Update status to failed
        error_message = f"Embedding failed: {str(e)}"
        logger.error(error_message, exc_info=True)
        update_document_status(document_id, "failed", error_message)
        raise