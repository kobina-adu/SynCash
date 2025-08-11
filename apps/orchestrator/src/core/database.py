"""
Database connection and session management for SyncCash Orchestrator
"""

import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.config.settings import get_settings
from src.models.transaction import Base

logger = structlog.get_logger(__name__)

# Global engine and session maker
_engine = None
_session_maker = None

def get_engine():
    """Get database engine"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            poolclass=NullPool if settings.environment == "test" else None,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine

def get_session_maker():
    """Get session maker"""
    global _session_maker
    if _session_maker is None:
        engine = get_engine()
        _session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _session_maker

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", exc_info=e)
        raise

async def close_db():
    """Close database connections"""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")
