"""
Monitoring middleware for FastAPI application
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from .metrics import metrics

logger = structlog.get_logger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract endpoint info
        method = request.method
        path = request.url.path
        
        # Normalize path for metrics (remove IDs)
        normalized_path = self._normalize_path(path)
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record successful request
            duration = time.time() - start_time
            metrics.record_http_request(
                method=method,
                endpoint=normalized_path,
                status_code=status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            metrics.record_http_request(
                method=method,
                endpoint=normalized_path,
                status_code=500,
                duration=duration
            )
            
            metrics.record_error(
                error_type=type(e).__name__,
                component="http_middleware"
            )
            
            logger.error("HTTP request error", 
                        method=method, 
                        path=path, 
                        error=str(e),
                        duration=duration)
            raise
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics to avoid high cardinality"""
        # Replace UUIDs and IDs with placeholders
        import re
        
        # Replace UUID patterns
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to track system health metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Update system metrics periodically
        if request.url.path in ["/health", "/api/v1/health/detailed"]:
            await self._update_system_metrics()
        
        return await call_next(request)
    
    async def _update_system_metrics(self):
        """Update system health gauges"""
        try:
            # TODO: Get actual counts from database and Redis
            # For now, use placeholder values
            active_txns = 0  # await get_active_transaction_count()
            db_conns = 1     # await get_database_connection_count()
            redis_conns = 1  # await get_redis_connection_count()
            
            metrics.update_system_gauges(
                active_txns=active_txns,
                db_conns=db_conns,
                redis_conns=redis_conns
            )
            
        except Exception as e:
            logger.error("Failed to update system metrics", error=str(e))
            metrics.record_error(
                error_type=type(e).__name__,
                component="health_middleware"
            )
