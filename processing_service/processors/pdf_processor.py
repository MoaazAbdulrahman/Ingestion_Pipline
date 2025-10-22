from pathlib import Path
from typing import Dict, Any
from pypdf import PdfReader

import sys
sys.path.append('/app/shared')
from logger import get_logger

logger = get_logger(__name__)


class PDFProcessor:
    """
    PDF document processor
    Extracts text content from PDF files
    """
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
    
    def can_process(self, file_path: str) -> bool:
        """
        Check if file can be processed
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is PDF
        """
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            logger.info(f"Processing PDF: {file_path}")
            
            reader = PdfReader(file_path)
            
            # Extract metadata
            metadata = {
                "num_pages": len(reader.pages),
                "pdf_metadata": {}
            }
            
            # Get PDF metadata if available
            if reader.metadata:
                metadata["pdf_metadata"] = {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                }
            
            # Extract text from all pages
            text_content = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append({
                            "page": page_num,
                            "text": page_text
                        })
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")
                    continue
            
            # Combine all text
            full_text = "\n\n".join([page["text"] for page in text_content])
            
            if not full_text.strip():
                raise ValueError("No text content extracted from PDF")
            
            logger.info(f"Successfully extracted {len(full_text)} characters from {len(text_content)} pages")
            
            return {
                "text": full_text,
                "metadata": metadata,
                "page_contents": text_content
            }
            
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {str(e)}")
            raise
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate PDF file can be opened and read
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if file is valid
        """
        try:
            reader = PdfReader(file_path)
            # Try to access first page
            if len(reader.pages) > 0:
                _ = reader.pages[0]
            return True
        except Exception as e:
            logger.error(f"Invalid PDF file {file_path}: {str(e)}")
            return False