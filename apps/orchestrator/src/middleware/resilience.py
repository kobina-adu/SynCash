"""
Resilience Middleware for SyncCash Orchestrator
Integrates retry logic, circuit breakers, rate limiting, and idempotency
"""
import time
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import structlog

from src.services.rate_limiter import rate_limiter, RateLimitResult
from src.services.idempotency import idempotency_service, IdempotencyResult
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class ResilienceMiddleware:
    """Middleware that applies resilience patterns to all requests"""
    
    def __init__(self, app):
        self.app = app
        
        # Endpoint configurations
        self.protected_endpoints = {
            "/api/v1/payments/initiate": {
                "rate_limit": True,
                "idempotency": True,
                "endpoint_name": "payments_initiate"
            },
            "/api/v1/payments/{id}/status": {
                "rate_limit": True,
                "idempotency": False,
                "endpoint_name": "payments_status"
            },
            "/api/v1/payments/{id}/refund": {
                "rate_limit": True,
                "idempotency": True,
                "endpoint_name": "refund_requests"
            },
            "/health": {
                "rate_limit": True,
                "idempotency": False,
                "endpoint_name": "health_checks"
            }
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request with resilience patterns"""
        start_time = time.time()
        
        try:
            # Extract request information
            endpoint_path = self._normalize_path(request.url.path)
            client_ip = self._get_client_ip(request)
            user_id = self._extract_user_id(request)
            idempotency_key = request.headers.get("Idempotency-Key")
            
            # Check if endpoint is protected
            endpoint_config = self.protected_endpoints.get(endpoint_path)
            if not endpoint_config:
                # Not a protected endpoint, proceed normally
                return await call_next(request)
            
            endpoint_name = endpoint_config["endpoint_name"]
            
            # Apply rate limiting
            if endpoint_config.get("rate_limit", False):
                rate_limit_result = await self._check_rate_limit(
                    request, endpoint_name, user_id, client_ip
                )
                
                if not rate_limit_result.allowed:
                    return self._create_rate_limit_response(rate_limit_result)
            
            # Apply idempotency checking
            idempotency_result = None
            if endpoint_config.get("idempotency", False) and idempotency_key:
                idempotency_result = await self._check_idempotency(
                    request, idempotency_key
                )
                
                if not idempotency_result.should_process:
                    return self._create_idempotency_response(idempotency_result)
            
            # Process the request
            response = await call_next(request)
            
            # Store idempotency response if applicable
            if (idempotency_result and idempotency_result.should_process and 
                idempotency_key and 200 <= response.status_code < 300):
                
                await self._store_idempotency_success(
                    idempotency_key, response, idempotency_result
                )
            
            # Record success metrics
            duration = time.time() - start_time
            metrics.record_histogram(f"request_duration_{endpoint_name}", duration)
            metrics.record_counter(f"request_success_{endpoint_name}")
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
            
        except Exception as e:
            # Handle unexpected errors
            duration = time.time() - start_time
            
            logger.error("Resilience middleware error",
                        path=request.url.path,
                        method=request.method,
                        duration=duration,
                        exc_info=e)
            
            # Store idempotency failure if applicable
            if idempotency_key:
                await self._store_idempotency_failure(idempotency_key, str(e))
            
            metrics.record_counter("resilience_middleware_error")
            metrics.record_histogram("request_duration_error", duration)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "Request processing failed",
                    "timestamp": time.time()
                }
            )
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for endpoint matching"""
        # Replace path parameters with placeholders
        import re
        
        # Replace UUIDs and IDs with {id} placeholder
        path = re.sub(r'/[0-9a-f-]{36}', '/{id}', path)  # UUID
        path = re.sub(r'/\d+', '/{id}', path)  # Numeric ID
        
        return path
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (JWT token, etc.)"""
        # TODO: Implement actual user ID extraction from JWT
        # For now, use a placeholder
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In production, decode JWT and extract user ID
            return "user_placeholder"
        
        return None
    
    async def _check_rate_limit(
        self,
        request: Request,
        endpoint_name: str,
        user_id: Optional[str],
        client_ip: str
    ) -> RateLimitResult:
        """Check rate limits for the request"""
        
        # Use user ID if available, otherwise use IP
        rate_limit_key = user_id or client_ip
        
        return await rate_limiter.check_rate_limit(
            key=rate_limit_key,
            endpoint=endpoint_name,
            user_id=user_id,
            ip_address=client_ip
        )
    
    async def _check_idempotency(
        self,
        request: Request,
        idempotency_key: str
    ) -> IdempotencyResult:
        """Check request idempotency"""
        
        # Extract request data for hashing
        request_data = {
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params)
        }
        
        # Add body data if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_data["body"] = body.decode("utf-8")
            except Exception as e:
                logger.warning("Failed to read request body for idempotency",
                              exc_info=e)
        
        return await idempotency_service.check_idempotency(
            idempotency_key=idempotency_key,
            request_data=request_data
        )
    
    def _create_rate_limit_response(self, result: RateLimitResult) -> JSONResponse:
        """Create rate limit exceeded response"""
        
        headers = {}
        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)
        
        if result.reset_time:
            headers["X-RateLimit-Reset"] = str(int(result.reset_time.timestamp()))
        
        headers["X-RateLimit-Remaining"] = str(result.remaining)
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": result.reason,
                "retry_after": result.retry_after,
                "timestamp": time.time()
            },
            headers=headers
        )
    
    def _create_idempotency_response(self, result: IdempotencyResult) -> JSONResponse:
        """Create idempotency response"""
        
        if result.cached_response:
            # Return cached successful response
            return JSONResponse(
                status_code=200,
                content=result.cached_response,
                headers={"X-Idempotency-Cached": "true"}
            )
        
        elif result.record and result.record.status.value == "processing":
            # Request is still being processed
            return JSONResponse(
                status_code=409,
                content={
                    "error": "Request already processing",
                    "message": "A request with this idempotency key is currently being processed",
                    "idempotency_key": result.record.key,
                    "timestamp": time.time()
                },
                headers={"X-Idempotency-Status": "processing"}
            )
        
        else:
            # Generic idempotency conflict
            return JSONResponse(
                status_code=409,
                content={
                    "error": "Idempotency conflict",
                    "message": "Request conflicts with existing idempotency key",
                    "timestamp": time.time()
                }
            )
    
    async def _store_idempotency_success(
        self,
        idempotency_key: str,
        response: Response,
        idempotency_result: IdempotencyResult
    ):
        """Store successful response for idempotency"""
        
        try:
            # Extract response data
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "timestamp": time.time()
            }
            
            # Try to extract JSON body if possible
            if hasattr(response, 'body'):
                try:
                    import json
                    response_data["body"] = json.loads(response.body.decode())
                except Exception:
                    response_data["body"] = "non-json-response"
            
            await idempotency_service.store_success_response(
                idempotency_key=idempotency_key,
                response_data=response_data
            )
            
        except Exception as e:
            logger.error("Failed to store idempotency success",
                        idempotency_key=idempotency_key,
                        exc_info=e)
    
    async def _store_idempotency_failure(
        self,
        idempotency_key: str,
        error_message: str
    ):
        """Store failure response for idempotency"""
        
        try:
            error_data = {
                "error": error_message,
                "timestamp": time.time()
            }
            
            await idempotency_service.store_failure_response(
                idempotency_key=idempotency_key,
                error_data=error_data
            )
            
        except Exception as e:
            logger.error("Failed to store idempotency failure",
                        idempotency_key=idempotency_key,
                        exc_info=e)
