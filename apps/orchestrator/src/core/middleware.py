"""
Middleware for automatic metrics collection
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog
from typing import Callable

from src.core.metrics import get_metrics_collector

logger = structlog.get_logger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect HTTP request metrics
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Normalize endpoint for metrics (remove IDs)
        endpoint = self._normalize_endpoint(path)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            self.metrics_collector.record_http_request(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            
            self.metrics_collector.record_http_request(
                method=method,
                endpoint=endpoint,
                status_code=500,
                duration=duration
            )
            
            self.metrics_collector.record_application_error(
                error_type=type(e).__name__,
                component="http_middleware",
                severity="error"
            )
            
            raise
    
    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint paths for metrics grouping
        Replace UUIDs and IDs with placeholders
        """
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace transaction references
        path = re.sub(r'/TXN_[A-Z0-9]+', '/{txn_ref}', path)
        
        return path
