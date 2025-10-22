from fastapi import APIRouter
from datetime import datetime
from models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        service="ingestion_service",
        timestamp=datetime.now()
    )