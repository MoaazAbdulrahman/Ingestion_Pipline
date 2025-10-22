#!/usr/bin/env python3
"""
Embedding Service Worker
Consumes jobs from Redis queue and generates embeddings
"""
import sys
sys.path.append('/app/shared')

from rq import Worker, Queue
from redis import Redis

from config import settings, get_redis_url
from logger import get_logger

logger = get_logger(__name__)


def main():
    """
    Start RQ worker for embedding queue
    """
    try:
        logger.info("Starting Embedding Worker...")
        logger.info(f"Queue: {settings.QUEUE_EMBEDDING}")
        logger.info(f"Redis URL: {get_redis_url()}")
        logger.info(f"Ollama Model: {settings.OLLAMA_MODEL}")
        
        # Connect to Redis
        redis_conn = Redis.from_url(get_redis_url())
        
        # Create queue
        queue = Queue(settings.QUEUE_EMBEDDING, connection=redis_conn)
        
        logger.info(f"Connected to Redis. Queue size: {len(queue)}")
        
        # Create worker
        worker = Worker(
            [queue],
            connection=redis_conn,
            name=f"embedding-worker-{settings.ENVIRONMENT}"
        )
        
        logger.info("Worker ready. Waiting for jobs...")
        
        # Start worker (blocking call)
        worker.work(with_scheduler=True)
        
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()