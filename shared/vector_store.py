from typing import List, Dict, Any, Optional
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from langchain_weaviate import WeaviateVectorStore
from langchain_core.documents import Document

from config import settings, get_weaviate_url
from logger import get_logger

logger = get_logger(__name__)


# Weaviate class/collection name
COLLECTION_NAME = "DocumentChunk"


def get_weaviate_client() -> weaviate.WeaviateClient:
    """
    Get Weaviate client instance
    
    Returns:
        Weaviate client
    """
    try:
        client = weaviate.connect_to_custom(
            http_host=settings.WEAVIATE_HOST,
            http_port=settings.WEAVIATE_PORT,
            http_secure=False,
            grpc_host=settings.WEAVIATE_HOST,
            grpc_port=settings.WEAVIATE_GRPC_PORT,
            grpc_secure=False,
        )
        
        if not client.is_ready():
            raise ConnectionError("Weaviate client is not ready")
        
        logger.info("Connected to Weaviate successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {str(e)}")
        raise


def init_weaviate_schema(client: Optional[weaviate.WeaviateClient] = None):
    """
    Initialize Weaviate schema/collection
    
    Args:
        client: Optional Weaviate client (creates new if not provided)
    """
    should_close = False
    if client is None:
        client = get_weaviate_client()
        should_close = True
    
    try:
        # Check if collection exists
        if client.collections.exists(COLLECTION_NAME):
            logger.info(f"Collection {COLLECTION_NAME} already exists")
            return
        
        # Create collection with properties
        client.collections.create(
            name=COLLECTION_NAME,
            description="Document chunks with embeddings for semantic search",
            properties=[
                Property(
                    name="document_id",
                    data_type=DataType.TEXT,
                    description="ID of the parent document"
                ),
                Property(
                    name="chunk_id",
                    data_type=DataType.TEXT,
                    description="Unique chunk identifier"
                ),
                Property(
                    name="chunk_index",
                    data_type=DataType.INT,
                    description="Index of chunk within document"
                ),
                Property(
                    name="text",
                    data_type=DataType.TEXT,
                    description="Chunk text content"
                ),
                Property(
                    name="filename",
                    data_type=DataType.TEXT,
                    description="Original filename"
                ),
                Property(
                    name="file_type",
                    data_type=DataType.TEXT,
                    description="File type (pdf, docx)"
                ),
            ],
            # Configure vectorizer - we'll provide vectors manually from Ollama
            vectorizer_config=Configure.Vectorizer.none(),
        )
        
        logger.info(f"Collection {COLLECTION_NAME} created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Weaviate schema: {str(e)}")
        raise
    finally:
        if should_close:
            client.close()


def get_vector_store(embeddings) -> WeaviateVectorStore:
    """
    Get LangChain Weaviate vector store instance
    
    Args:
        embeddings: Embedding model instance
    
    Returns:
        WeaviateVectorStore instance
    """
    try:
        client = get_weaviate_client()
        
        # Initialize schema if not exists
        init_weaviate_schema(client)
        
        vector_store = WeaviateVectorStore(
            client=client,
            index_name=COLLECTION_NAME,
            text_key="text",
            embedding=embeddings
        )
        
        logger.info("Vector store initialized")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to get vector store: {str(e)}")
        raise


def add_documents_to_vectorstore(
    vector_store: WeaviateVectorStore,
    documents: List[Document],
    metadatas: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    Add documents to vector store
    
    Args:
        vector_store: Vector store instance
        documents: List of LangChain Document objects
        metadatas: Optional list of metadata dictionaries
    
    Returns:
        List of document IDs
    """
    try:
        if metadatas:
            # Merge metadata into documents
            for doc, metadata in zip(documents, metadatas):
                doc.metadata.update(metadata)
        
        ids = vector_store.add_documents(documents)
        logger.info(f"Added {len(ids)} documents to vector store")
        return ids
    except Exception as e:
        logger.error(f"Failed to add documents to vector store: {str(e)}")
        raise


def search_similar_documents(
    vector_store: WeaviateVectorStore,
    query: str,
    k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """
    Search for similar documents
    
    Args:
        vector_store: Vector store instance
        query: Search query
        k: Number of results to return
        filter_dict: Optional metadata filter
    
    Returns:
        List of similar documents with scores
    """
    try:
        if filter_dict:
            results = vector_store.similarity_search(
                query,
                k=k,
                filters=filter_dict
            )
        else:
            results = vector_store.similarity_search(query, k=k)
        
        logger.info(f"Found {len(results)} similar documents for query")
        return results
    except Exception as e:
        logger.error(f"Failed to search similar documents: {str(e)}")
        raise


def delete_document_chunks(
    document_id: str,
    client: Optional[weaviate.WeaviateClient] = None
) -> int:
    """
    Delete all chunks for a document
    
    Args:
        document_id: Document ID
        client: Optional Weaviate client
    
    Returns:
        Number of deleted chunks
    """
    should_close = False
    if client is None:
        client = get_weaviate_client()
        should_close = True
    
    try:
        collection = client.collections.get(COLLECTION_NAME)
        
        # Delete by document_id filter
        result = collection.data.delete_many(
            where={
                "path": ["document_id"],
                "operator": "Equal",
                "valueText": document_id
            }
        )
        
        deleted_count = result.matches if hasattr(result, 'matches') else 0
        logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete document chunks: {str(e)}")
        raise
    finally:
        if should_close:
            client.close()