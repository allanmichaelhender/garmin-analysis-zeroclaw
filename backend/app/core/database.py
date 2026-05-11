"""Database configuration."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./garmin.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database using Alembic migrations."""
    try:
        from alembic.config import Config
        from alembic import command

        # Get the path to alembic.ini (now in backend directory)
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        alembic_ini = os.path.join(backend_dir, 'alembic.ini')

        # Configure alembic
        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option('sqlalchemy.url', DATABASE_URL)

        # Run migrations
        command.upgrade(alembic_cfg, 'head')
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Failed to apply database migrations: {e}")
        raise
