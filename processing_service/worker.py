#!/usr/bin/env python3
"""
Processing Service Worker
Consumes jobs from Redis queue and processes documents
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
    Start RQ worker for processing queue
    """
    try:
        logger.info("Starting Processing Worker...")
        logger.info(f"Queue: {settings.QUEUE_PROCESSING}")
        logger.info(f"Redis URL: {get_redis_url()}")
        
        # Connect to Redis
        redis_conn = Redis.from_url(get_redis_url())
        
        # Create queue
        queue = Queue(settings.QUEUE_PROCESSING, connection=redis_conn)
        
        logger.info(f"Connected to Redis. Queue size: {len(queue)}")
        
        # Create worker
        worker = Worker(
            [queue],
            connection=redis_conn,
            name=f"processing-worker-{settings.ENVIRONMENT}"
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