"""
Resilience API endpoints for SyncCash Orchestrator
Provides monitoring and management of resilience patterns
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog

from src.services.circuit_breaker import circuit_breaker_manager
from src.services.rate_limiter import rate_limiter
from src.services.idempotency import idempotency_service
from src.services.enhanced_retry import enhanced_retry_service

logger = structlog.get_logger(__name__)
router = APIRouter()

class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status response"""
    circuit_breakers: Dict[str, Any]
    total_count: int

class RateLimitStatus(BaseModel):
    """Rate limit status response"""
    key: str
    endpoint: str
    status: Dict[str, Any]

class IdempotencyStats(BaseModel):
    """Idempotency statistics response"""
    stats: Dict[str, Any]

@router.get("/resilience/circuit-breakers", response_model=CircuitBreakerStatus)
async def get_circuit_breaker_status():
    """Get status of all circuit breakers"""
    try:
        stats = circuit_breaker_manager.get_all_stats()
        
        return CircuitBreakerStatus(
            circuit_breakers=stats,
            total_count=len(stats)
        )
        
    except Exception as e:
        logger.error("Failed to get circuit breaker status", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve circuit breaker status")

@router.post("/resilience/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    """Reset specific circuit breaker"""
    try:
        if name in circuit_breaker_manager.circuit_breakers:
            circuit_breaker_manager.circuit_breakers[name].reset()
            logger.info("Circuit breaker reset", circuit_breaker=name)
            
            return {"message": f"Circuit breaker {name} reset successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Circuit breaker {name} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reset circuit breaker", circuit_breaker=name, exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to reset circuit breaker")

@router.post("/resilience/circuit-breakers/reset-all")
async def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    try:
        circuit_breaker_manager.reset_all()
        logger.info("All circuit breakers reset")
        
        return {"message": "All circuit breakers reset successfully"}
        
    except Exception as e:
        logger.error("Failed to reset all circuit breakers", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to reset circuit breakers")

@router.get("/resilience/rate-limits/{key}/{endpoint}", response_model=RateLimitStatus)
async def get_rate_limit_status(key: str, endpoint: str):
    """Get rate limit status for specific key and endpoint"""
    try:
        status = await rate_limiter.get_rate_limit_status(key, endpoint)
        
        return RateLimitStatus(
            key=key,
            endpoint=endpoint,
            status=status
        )
        
    except Exception as e:
        logger.error("Failed to get rate limit status", key=key, endpoint=endpoint, exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit status")

@router.post("/resilience/rate-limits/{key}/{endpoint}/reset")
async def reset_rate_limit(key: str, endpoint: str):
    """Reset rate limit for specific key and endpoint"""
    try:
        await rate_limiter.reset_rate_limit(key, endpoint)
        logger.info("Rate limit reset", key=key, endpoint=endpoint)
        
        return {"message": f"Rate limit reset for {key} on {endpoint}"}
        
    except Exception as e:
        logger.error("Failed to reset rate limit", key=key, endpoint=endpoint, exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to reset rate limit")

@router.get("/resilience/idempotency/stats", response_model=IdempotencyStats)
async def get_idempotency_stats():
    """Get idempotency service statistics"""
    try:
        stats = await idempotency_service.get_record_stats()
        
        return IdempotencyStats(stats=stats)
        
    except Exception as e:
        logger.error("Failed to get idempotency stats", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve idempotency statistics")

@router.post("/resilience/idempotency/cleanup")
async def cleanup_idempotency_records():
    """Clean up expired idempotency records"""
    try:
        await idempotency_service.cleanup_expired_records()
        logger.info("Idempotency records cleanup completed")
        
        return {"message": "Expired idempotency records cleaned up successfully"}
        
    except Exception as e:
        logger.error("Failed to cleanup idempotency records", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to cleanup idempotency records")

@router.get("/resilience/retry/stats")
async def get_retry_stats():
    """Get retry service statistics"""
    try:
        stats = enhanced_retry_service.get_retry_stats()
        
        return {"retry_stats": stats}
        
    except Exception as e:
        logger.error("Failed to get retry stats", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to retrieve retry statistics")

@router.get("/resilience/health")
async def resilience_health_check():
    """Overall resilience system health check"""
    try:
        # Get circuit breaker health
        cb_stats = circuit_breaker_manager.get_all_stats()
        open_circuits = [name for name, stats in cb_stats.items() if stats["state"] == "open"]
        
        # Get rate limiter health (simplified)
        rate_limit_health = "healthy"  # Could be enhanced with actual health metrics
        
        # Get idempotency health
        idempotency_stats = await idempotency_service.get_record_stats()
        
        # Overall health assessment
        overall_health = "healthy"
        if len(open_circuits) > 0:
            overall_health = "degraded"
        
        health_data = {
            "status": overall_health,
            "circuit_breakers": {
                "total": len(cb_stats),
                "open": len(open_circuits),
                "open_circuits": open_circuits,
                "health": "degraded" if open_circuits else "healthy"
            },
            "rate_limiting": {
                "health": rate_limit_health
            },
            "idempotency": {
                "health": "healthy" if not idempotency_stats.get("error") else "degraded",
                "active_records": idempotency_stats.get("total_active_records", 0)
            },
            "retry_service": {
                "health": "healthy"
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error("Resilience health check failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Resilience health check failed")
