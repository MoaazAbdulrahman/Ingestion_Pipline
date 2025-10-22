#!/usr/bin/env python3
"""
Initialize SQLite database schema
"""
import sys
sys.path.append('/app/shared')

from database import init_database
from logger import get_logger

logger = get_logger(__name__)


def main():
    """Initialize database"""
    try:
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()