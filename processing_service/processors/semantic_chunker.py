from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import sys
sys.path.append('/app/shared')
from config import settings
from logger import get_logger

logger = get_logger(__name__)


class SemanticChunker:
    """
    Semantic text chunker using LangChain
    Splits text into meaningful chunks preserving semantic coherence
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize semantic chunker
        
        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # RecursiveCharacterTextSplitter tries to split on semantic boundaries
        # Priority: \n\n (paragraphs) -> \n (lines) -> . (sentences) -> space -> character
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentence endings
                "! ",    # Exclamation sentences
                "? ",    # Question sentences
                "; ",    # Semicolons
                ", ",    # Commas
                " ",     # Spaces
                ""       # Characters
            ],
            keep_separator=True,
            is_separator_regex=False
        )
        
        logger.info(
            f"SemanticChunker initialized with chunk_size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into semantic chunks
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries
        """
        try:
            if not text or not text.strip():
                raise ValueError("Cannot chunk empty text")
            
            logger.info(f"Chunking text of length {len(text)}")
            
            # Create LangChain Document
            doc = Document(
                page_content=text,
                metadata=metadata or {}
            )
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Convert to our format
            chunk_list = []
            for idx, chunk in enumerate(chunks):
                chunk_dict = {
                    "chunk_index": idx,
                    "chunk_text": chunk.page_content,
                    "chunk_size": len(chunk.page_content),
                    "metadata": chunk.metadata
                }
                chunk_list.append(chunk_dict)
            
            logger.info(
                f"Created {len(chunk_list)} chunks "
                f"(avg size: {sum(c['chunk_size'] for c in chunk_list) / len(chunk_list):.0f} chars)"
            )
            
            return chunk_list
            
        except Exception as e:
            logger.error(f"Failed to chunk text: {str(e)}")
            raise
    
    def chunk_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Chunk multiple documents
        
        Args:
            texts: List of texts to chunk
            metadatas: Optional list of metadata dictionaries
            
        Returns:
            List of chunk lists (one per document)
        """
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        if len(texts) != len(metadatas):
            raise ValueError("Number of texts and metadatas must match")
        
        all_chunks = []
        for text, metadata in zip(texts, metadatas):
            chunks = self.chunk_text(text, metadata)
            all_chunks.append(chunks)
        
        return all_chunks
    
    def get_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about chunks
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {
                "num_chunks": 0,
                "total_chars": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0
            }
        
        sizes = [c["chunk_size"] for c in chunks]
        
        return {
            "num_chunks": len(chunks),
            "total_chars": sum(sizes),
            "avg_chunk_size": sum(sizes) / len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes)
        }