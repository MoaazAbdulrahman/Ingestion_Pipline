import os
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from models.schemas import IngestResponse, ErrorResponse, FileType, DocumentStatus

# These will be imported from shared module later
import sys
sys.path.append('/app/shared')
from config import settings
from database import create_document_record
from redis_queue import enqueue_processing_job
from logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Configuration
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
MAX_FILE_SIZE = settings.MAX_FILE_SIZE  # 50MB in bytes
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    file: UploadFile = File(..., description="PDF or DOCX file to ingest")
):
    """
    Ingest a document (PDF or DOCX) for processing.
    
    Steps:
    1. Validate file type and size
    2. Save file to upload directory
    3. Create metadata record in SQLite
    4. Queue processing job in Redis
    5. Return document_id and status
    """
    
    try:
        # Step 1: Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Invalid file type attempted: {file_ext}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Only PDF and DOCX files are supported. Got: {file_ext}"
            )
        
        # Determine file type
        file_type = FileType.PDF if file_ext == '.pdf' else FileType.DOCX
        
        # Step 2: Validate file size
        # Read file content to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size == 0:
            logger.warning(f"Empty file uploaded: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file.filename} ({file_size} bytes)")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Step 3: Generate unique document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        upload_time = datetime.now()
        
        # Step 4: Save file to upload directory
        # Create safe filename with document_id
        safe_filename = f"{document_id}_{Path(file.filename).name}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"File saved: {safe_filename} ({file_size} bytes)")
        
        # Step 5: Create metadata record in SQLite
        metadata = {
            "document_id": document_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "file_type": file_type.value,
            "file_size": file_size,
            "status": DocumentStatus.UPLOADED.value,
            "upload_time": upload_time
        }
        
        create_document_record(metadata)
        logger.info(f"Document record created: {document_id}")
        
        # Step 6: Queue processing job
        job_data = {
            "document_id": document_id,
            "file_path": str(file_path),
            "file_type": file_type.value
        }
        
        job_id = enqueue_processing_job(job_data)
        logger.info(f"Processing job queued: {job_id} for document {document_id}")
        
        # Step 7: Return response
        return IngestResponse(
            document_id=document_id,
            filename=file.filename,
            file_type=file_type.value,
            file_size=file_size,
            status=DocumentStatus.UPLOADED.value,
            message="Document uploaded successfully and queued for processing",
            upload_time=upload_time
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during file ingestion: {str(e)}"
        )