"""
Database connection and session management for SyncCash Orchestrator
"""

import structlog
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.pool.impl import AsyncAdaptedQueuePool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy import text

from src.config.settings import get_settings
from src.models.transaction import Base

logger = structlog.get_logger(__name__)

# Global engine and session maker
_engine = None
_session_maker = None
_connection_pool_stats = {
    "total_connections": 0,
    "active_connections": 0,
    "pool_size": 0,
    "checked_out": 0,
    "overflow": 0,
    "last_health_check": None,
    "consecutive_failures": 0
}

def get_engine():
    """Get optimized database engine with connection pooling"""
    global _engine
    if _engine is None:
        settings = get_settings()
        
        # Optimized connection pool settings
        pool_settings = {
            "pool_size": 10,  # Base number of connections (reduced for stability)
            "max_overflow": 20,  # Additional connections when needed
            "pool_pre_ping": True,  # Validate connections before use
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_timeout": 30,  # Timeout for getting connection
            "connect_args": {
                "server_settings": {
                    "application_name": "synccash_orchestrator",
                    "jit": "off"
                },
                "command_timeout": 60
                # Removed connect_timeout as it's not supported by asyncpg
            }
        }
        
        # Use NullPool for testing, AsyncAdaptedQueuePool for production
        if settings.environment == "test":
            pool_settings = {"poolclass": NullPool}
        else:
            # Fallback to simpler pool configuration if connection issues persist
            try:
                pool_settings["poolclass"] = AsyncAdaptedQueuePool
            except Exception:
                logger.warning("Falling back to NullPool due to connection pool issues")
                pool_settings = {"poolclass": NullPool}
        
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            **pool_settings
        )
        
        logger.info("Database engine created with optimized connection pool",
                   pool_size=pool_settings.get("pool_size", "NullPool"),
                   max_overflow=pool_settings.get("max_overflow", 0))
    
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
        # Test connection first
        async with engine.begin() as conn:
            # Test basic connectivity
            await conn.execute("SELECT 1")
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", exc_info=e)
        raise

async def test_db_connection() -> Dict[str, Any]:
    """Enhanced database connectivity test with detailed diagnostics"""
    global _connection_pool_stats
    
    start_time = datetime.now()
    result = {
        "healthy": False,
        "response_time_ms": 0,
        "pool_stats": {},
        "error": None,
        "connection_test": False,
        "transaction_test": False,
        "table_access_test": False
    }
    
    try:
        engine = get_engine()
        
        # Get connection pool statistics
        if hasattr(engine.pool, 'size'):
            pool_stats = {
                "pool_size": engine.pool.size(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "checked_in": engine.pool.checkedin()
            }
            result["pool_stats"] = pool_stats
            _connection_pool_stats.update(pool_stats)
        
        # Test 1: Basic connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1 as test_connection"))
            result["connection_test"] = True
            
            # Test 2: Transaction capability
            async with conn.begin():
                await conn.execute(text("SELECT NOW() as test_transaction"))
                result["transaction_test"] = True
            
            # Test 3: Table access (if tables exist)
            try:
                await conn.execute(text("SELECT COUNT(*) FROM transactions LIMIT 1"))
                result["table_access_test"] = True
            except Exception:
                # Tables might not exist yet, this is okay
                result["table_access_test"] = "tables_not_found"
        
        # Calculate response time
        end_time = datetime.now()
        result["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        # Mark as healthy if all critical tests pass
        result["healthy"] = result["connection_test"] and result["transaction_test"]
        
        # Update stats
        _connection_pool_stats["last_health_check"] = datetime.now()
        _connection_pool_stats["consecutive_failures"] = 0
        
        logger.info("Database health check completed",
                   healthy=result["healthy"],
                   response_time_ms=result["response_time_ms"],
                   pool_stats=result["pool_stats"])
        
        return result
        
    except DisconnectionError as e:
        result["error"] = f"Database disconnection: {str(e)}"
        _connection_pool_stats["consecutive_failures"] += 1
        logger.error("Database disconnection error", exc_info=e)
        
    except SQLAlchemyError as e:
        result["error"] = f"Database error: {str(e)}"
        _connection_pool_stats["consecutive_failures"] += 1
        logger.error("Database SQLAlchemy error", exc_info=e)
        
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        _connection_pool_stats["consecutive_failures"] += 1
        logger.error("Database connection test failed", exc_info=e)
    
    # Calculate response time even on failure
    end_time = datetime.now()
    result["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
    _connection_pool_stats["last_health_check"] = datetime.now()
    
    return result

async def get_connection_pool_stats() -> Dict[str, Any]:
    """Get detailed connection pool statistics"""
    global _connection_pool_stats
    
    engine = get_engine()
    current_stats = _connection_pool_stats.copy()
    
    # Update with real-time pool stats if available
    if hasattr(engine.pool, 'size'):
        current_stats.update({
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "checked_in": engine.pool.checkedin(),
            "total_connections": engine.pool.size() + engine.pool.overflow()
        })
    
    return current_stats

async def optimize_connection_pool():
    """Optimize connection pool by clearing idle connections"""
    try:
        engine = get_engine()
        
        # Force pool recreation if too many consecutive failures
        if _connection_pool_stats["consecutive_failures"] > 5:
            logger.warning("High failure rate detected, recreating connection pool")
            await engine.dispose()
            global _engine
            _engine = None
            _connection_pool_stats["consecutive_failures"] = 0
            
        logger.info("Connection pool optimization completed")
        
    except Exception as e:
        logger.error("Connection pool optimization failed", exc_info=e)

async def close_db():
    """Close database connections gracefully"""
    global _engine, _session_maker
    
    if _engine:
        try:
            # Wait for active connections to finish (max 30 seconds)
            await asyncio.wait_for(_engine.dispose(), timeout=30.0)
            logger.info("Database connections closed gracefully")
        except asyncio.TimeoutError:
            logger.warning("Database connection closure timed out")
        except Exception as e:
            logger.error("Error closing database connections", exc_info=e)
        finally:
            _engine = None
            _session_maker = None
