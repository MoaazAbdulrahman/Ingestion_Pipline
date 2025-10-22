#!/usr/bin/env python3
"""
Initialize Weaviate schema/collection
"""
import sys
import time
sys.path.append('/app/shared')

from vector_store import get_weaviate_client, init_weaviate_schema
from logger import get_logger

logger = get_logger(__name__)


def main():
    """Initialize Weaviate schema"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Weaviate (attempt {attempt + 1}/{max_retries})...")
            client = get_weaviate_client()
            
            logger.info("Initializing Weaviate schema...")
            init_weaviate_schema(client)
            
            client.close()
            logger.info("Weaviate schema initialized successfully!")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize Weaviate: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Failed to initialize Weaviate.")
                sys.exit(1)


if __name__ == "__main__":
    main()