import redis
from rq import Queue
from typing import Dict, Any, Optional
from config import settings, get_redis_url
from logger import get_logger

logger = get_logger(__name__)


def get_redis_connection() -> redis.Redis:
    """
    Get Redis connection
    
    Returns:
        Redis connection instance
    """
    try:
        redis_conn = redis.from_url(
            get_redis_url(),
            decode_responses=True
        )
        # Test connection
        redis_conn.ping()
        return redis_conn
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise


def get_queue(queue_name: str) -> Queue:
    """
    Get RQ Queue instance
    
    Args:
        queue_name: Name of the queue
    
    Returns:
        Queue instance
    """
    try:
        redis_conn = get_redis_connection()
        return Queue(queue_name, connection=redis_conn)
    except Exception as e:
        logger.error(f"Failed to get queue {queue_name}: {str(e)}")
        raise


def enqueue_processing_job(job_data: Dict[str, Any]) -> str:
    """
    Enqueue a document processing job
    
    Args:
        job_data: Job data containing document_id, file_path, file_type
    
    Returns:
        Job ID
    """
    try:
        queue = get_queue(settings.QUEUE_PROCESSING)
        
        # Enqueue job - the worker will import and execute the task
        job = queue.enqueue(
            'tasks.process_document.process_document_task',
            job_data,
            job_timeout='10m',  # 10 minutes timeout
            result_ttl=86400,   # Keep result for 24 hours
            failure_ttl=86400   # Keep failed job for 24 hours
        )
        
        logger.info(
            f"Processing job enqueued",
            extra={
                "job_id": job.id,
                "document_id": job_data.get("document_id"),
                "queue": settings.QUEUE_PROCESSING
            }
        )
        
        return job.id
    except Exception as e:
        logger.error(f"Failed to enqueue processing job: {str(e)}")
        raise


def enqueue_embedding_job(job_data: Dict[str, Any]) -> str:
    """
    Enqueue an embedding job
    
    Args:
        job_data: Job data containing document_id and chunks
    
    Returns:
        Job ID
    """
    try:
        queue = get_queue(settings.QUEUE_EMBEDDING)
        
        job = queue.enqueue(
            'tasks.embed_document.embed_document_task',
            job_data,
            job_timeout='15m',  # 15 minutes timeout
            result_ttl=86400,
            failure_ttl=86400
        )
        
        logger.info(
            f"Embedding job enqueued",
            extra={
                "job_id": job.id,
                "document_id": job_data.get("document_id"),
                "queue": settings.QUEUE_EMBEDDING
            }
        )
        
        return job.id
    except Exception as e:
        logger.error(f"Failed to enqueue embedding job: {str(e)}")
        raise


def get_job_status(job_id: str, queue_name: str) -> Optional[Dict[str, Any]]:
    """
    Get job status from queue
    
    Args:
        job_id: Job ID
        queue_name: Queue name
    
    Returns:
        Job status dictionary
    """
    try:
        from rq.job import Job
        
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)
        
        return {
            "job_id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at,
            "started_at": job.started_at,
            "ended_at": job.ended_at,
            "result": job.result,
            "exc_info": job.exc_info
        }
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        return None


def get_queue_stats(queue_name: str) -> Dict[str, int]:
    """
    Get queue statistics
    
    Args:
        queue_name: Queue name
    
    Returns:
        Dictionary with queue statistics
    """
    try:
        queue = get_queue(queue_name)
        
        return {
            "queue_name": queue_name,
            "queued": len(queue),
            "started": queue.started_job_registry.count,
            "finished": queue.finished_job_registry.count,
            "failed": queue.failed_job_registry.count,
            "deferred": queue.deferred_job_registry.count,
            "scheduled": queue.scheduled_job_registry.count
        }
    except Exception as e:
        logger.error(f"Failed to get queue stats: {str(e)}")
        return {}