"""SQLAlchemy models for TicketDesk Enterprise"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import get_settings

settings = get_settings()

# Create base class for all models
Base = declarative_base()

# Database engine (lazy-loaded)
_engine = None


def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=False,
            connect_args={"ssl": settings.DATABASE_SSL} if settings.DATABASE_SSL else {}
        )
    return _engine


def get_session_factory():
    """Create session factory"""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


# Import all models to register them with Base
# (they will be imported as needed)

__all__ = ["Base", "get_engine", "get_session_factory"]
