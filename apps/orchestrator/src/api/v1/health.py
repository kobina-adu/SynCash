"""
Health check endpoints for SyncCash Orchestrator
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog
import time
from typing import Dict, Any

from src.core.database import get_db_session, test_db_connection, get_connection_pool_stats
from src.core.redis_client import get_redis_client
from src.services.db_monitor import db_health_monitor

logger = structlog.get_logger(__name__)
router = APIRouter()

# Service start time for uptime calculation
SERVICE_START_TIME = time.time()

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
    database: Dict[str, Any]
    redis: Dict[str, Any]
    uptime: float
    connection_pool: Dict[str, Any]

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
    """Enhanced detailed health check with comprehensive diagnostics"""
    
    # Enhanced database connectivity check
    db_result = await test_db_connection()
    db_status = {
        "status": "healthy" if db_result["healthy"] else "unhealthy",
        "response_time_ms": db_result["response_time_ms"],
        "connection_test": db_result["connection_test"],
        "transaction_test": db_result["transaction_test"],
        "table_access_test": db_result["table_access_test"],
        "error": db_result.get("error")
    }
    
    # Enhanced Redis connectivity check
    redis_status = {
        "status": "healthy",
        "response_time_ms": 0,
        "ping_test": False,
        "memory_usage": None,
        "error": None
    }
    
    redis_start = time.time()
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        redis_status["ping_test"] = True
        
        # Get Redis info if available
        try:
            info = await redis_client.info("memory")
            redis_status["memory_usage"] = {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "unknown")
            }
        except Exception:
            pass  # Redis info not critical
            
    except Exception as e:
        logger.error("Redis health check failed", exc_info=e)
        redis_status["status"] = "unhealthy"
        redis_status["error"] = str(e)
    
    redis_status["response_time_ms"] = int((time.time() - redis_start) * 1000)
    
    # Get connection pool statistics
    pool_stats = await get_connection_pool_stats()
    
    # Determine overall status with more nuanced logic
    overall_status = "healthy"
    
    # Database issues
    if not db_result["healthy"]:
        overall_status = "unhealthy"
    elif db_result["response_time_ms"] > 1000:  # Slow response
        overall_status = "degraded"
    
    # Redis issues
    if redis_status["status"] != "healthy":
        if overall_status == "healthy":
            overall_status = "degraded"  # Redis down but DB up = degraded
        else:
            overall_status = "unhealthy"  # Both down = unhealthy
    elif redis_status["response_time_ms"] > 500:  # Slow Redis
        if overall_status == "healthy":
            overall_status = "degraded"
    
    # Connection pool issues
    if pool_stats.get("consecutive_failures", 0) > 3:
        overall_status = "degraded"
    
    logger.info("Detailed health check completed",
               overall_status=overall_status,
               db_healthy=db_result["healthy"],
               redis_healthy=redis_status["status"] == "healthy",
               db_response_ms=db_result["response_time_ms"],
               redis_response_ms=redis_status["response_time_ms"])
    
    return DetailedHealthResponse(
        status=overall_status,
        service="synccash-orchestrator",
        timestamp=time.time(),
        version="1.0.0",
        database=db_status,
        redis=redis_status,
        connection_pool=pool_stats,
        uptime=time.time()  # Simplified uptime
    )

@router.get("/health/ready")
async def readiness_check():
    """Enhanced Kubernetes readiness probe with timeout"""
    try:
        # Quick database check with timeout
        db_result = await test_db_connection()
        if not db_result["healthy"]:
            raise HTTPException(
                status_code=503, 
                detail=f"Database not ready: {db_result.get('error', 'Unknown error')}"
            )
        
        # Quick Redis check
        redis_client = await get_redis_client()
        await redis_client.ping()
        
        return {
            "status": "ready",
            "db_response_ms": db_result["response_time_ms"],
            "checks": {
                "database": "ready",
                "redis": "ready"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", exc_info=e)
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "service": "synccash-orchestrator"
    }

@router.get("/health/pool")
async def connection_pool_status():
    """Connection pool diagnostics endpoint"""
    try:
        pool_stats = await get_connection_pool_stats()
        return {
            "status": "ok",
            "pool_statistics": pool_stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("Pool status check failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Pool status unavailable: {str(e)}")

@router.get("/health/monitor/summary")
async def database_health_summary():
    """Get comprehensive database health summary"""
    try:
        summary = await db_health_monitor.get_health_summary()
        return summary
    except Exception as e:
        logger.error("Health summary failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Health summary unavailable: {str(e)}")

@router.post("/health/monitor/optimize")
async def force_database_optimization():
    """Force database optimization"""
    try:
        result = await db_health_monitor.force_optimization()
        return result
    except Exception as e:
        logger.error("Database optimization failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.get("/health/monitor/diagnostics")
async def run_database_diagnostics():
    """Run comprehensive database diagnostics"""
    try:
        diagnostics = await db_health_monitor.run_diagnostics()
        return diagnostics
    except Exception as e:
        logger.error("Database diagnostics failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {str(e)}")
