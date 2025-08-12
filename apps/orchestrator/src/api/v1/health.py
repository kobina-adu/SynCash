"""
Health check endpoints for SyncCash Orchestrator
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog
import time

from src.core.database import get_db_session
from src.core.redis_client import get_redis_client

logger = structlog.get_logger(__name__)
router = APIRouter()

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    timestamp: float
    version: str

class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""
    status: str
    service: str
    timestamp: float
    version: str
    database: str
    redis: str
    uptime: float

@router.get("/health", response_model=HealthResponse)
async def basic_health():
    """Basic health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="synccash-orchestrator",
        timestamp=time.time(),
        version="1.0.0"
    )

@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health():
    """Detailed health check including dependencies"""
    
    # Check database connectivity
    
    db_status = "healthy"
    try:
        async with get_db_session() as session:
            await session.execute("SELECT 1")
    except Exception as e:
        logger.error("Database health check failed", exc_info=e)
        db_status = "unhealthy"
    
    # Check Redis connectivity
    redis_status = "healthy"
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
    except Exception as e:
        logger.error("Redis health check failed", exc_info=e)
        redis_status = "unhealthy"
    
    # Overall status
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
    
    return DetailedHealthResponse(
        status=overall_status,
        service="synccash-orchestrator",
        timestamp=time.time(),
        version="1.0.0",
        database=db_status,
        redis=redis_status,
        uptime=time.time()  # Simplified uptime
    )

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Check critical dependencies
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        
        redis_client = await get_redis_client()
        await redis_client.ping()
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error("Readiness check failed", exc_info=e)
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
