"""
Enhanced Retry Service for SyncCash Orchestrator
Comprehensive retry mechanisms for external service calls
"""
import asyncio
import random
import time
from typing import Dict, Any, Optional, Callable, Awaitable, List, Type
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import structlog

from src.monitoring.metrics import metrics
from src.services.circuit_breaker import get_provider_circuit_breaker, get_fraud_detection_circuit_breaker

logger = structlog.get_logger(__name__)

class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"

class ErrorCategory(Enum):
    """Error categorization for retry decisions"""
    RETRYABLE = "retryable"          # Network errors, timeouts, 5xx
    NON_RETRYABLE = "non_retryable"  # 4xx client errors, validation
    CIRCUIT_BREAKER = "circuit_breaker"  # Circuit breaker open
    RATE_LIMITED = "rate_limited"    # Rate limit exceeded

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0          # Base delay in seconds
    max_delay: float = 60.0          # Maximum delay in seconds
    backoff_multiplier: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True              # Add random jitter
    retryable_exceptions: List[Type[Exception]] = None
    non_retryable_exceptions: List[Type[Exception]] = None

class RetryResult:
    """Result of retry operation"""
    
    def __init__(self, success: bool, result: Any = None, error: Exception = None, 
                 attempts: int = 0, total_duration: float = 0.0):
        self.success = success
        self.result = result
        self.error = error
        self.attempts = attempts
        self.total_duration = total_duration

class EnhancedRetryService:
    """Enhanced retry service with circuit breaker integration"""
    
    def __init__(self):
        self.retry_stats = {}
        
        # Default retryable exceptions (network/temporary errors)
        self.default_retryable_exceptions = [
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            OSError,
        ]
        
        # Default non-retryable exceptions (client errors)
        self.default_non_retryable_exceptions = [
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ]
    
    async def retry_with_circuit_breaker(
        self,
        func: Callable[[], Awaitable[Any]],
        service_name: str,
        config: RetryConfig = None,
        *args,
        **kwargs
    ) -> RetryResult:
        """Execute function with retry logic and circuit breaker protection"""
        
        config = config or RetryConfig()
        start_time = time.time()
        last_error = None
        
        # Get appropriate circuit breaker
        if service_name.startswith("provider_"):
            circuit_breaker = get_provider_circuit_breaker(service_name.replace("provider_", ""))
        elif service_name == "fraud_detection":
            circuit_breaker = get_fraud_detection_circuit_breaker()
        else:
            from src.services.circuit_breaker import circuit_breaker_manager
            circuit_breaker = circuit_breaker_manager.get_circuit_breaker(service_name)
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                # Execute with circuit breaker protection
                result = await circuit_breaker.call(func, *args, **kwargs)
                
                total_duration = time.time() - start_time
                
                # Record success metrics
                metrics.record_counter(f"retry_success_{service_name}")
                metrics.record_histogram(f"retry_duration_{service_name}", total_duration)
                metrics.record_gauge(f"retry_attempts_{service_name}", attempt)
                
                logger.info("Retry operation succeeded",
                           service=service_name,
                           attempt=attempt,
                           duration=total_duration)
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt,
                    total_duration=total_duration
                )
                
            except Exception as e:
                last_error = e
                error_category = self._categorize_error(e, config)
                
                logger.warning("Retry attempt failed",
                              service=service_name,
                              attempt=attempt,
                              error=str(e),
                              error_category=error_category.value)
                
                # Record failure metrics
                metrics.record_counter(f"retry_failure_{service_name}")
                metrics.record_counter(f"retry_error_{error_category.value}_{service_name}")
                
                # Check if should retry
                if not self._should_retry(e, attempt, config, error_category):
                    break
                
                # Calculate delay before next attempt
                if attempt < config.max_attempts:
                    delay = self._calculate_delay(attempt, config, error_category)
                    
                    logger.debug("Waiting before retry",
                                service=service_name,
                                attempt=attempt,
                                delay=delay,
                                next_attempt=attempt + 1)
                    
                    await asyncio.sleep(delay)
        
        # All attempts failed
        total_duration = time.time() - start_time
        
        metrics.record_counter(f"retry_exhausted_{service_name}")
        metrics.record_histogram(f"retry_duration_{service_name}", total_duration)
        metrics.record_gauge(f"retry_attempts_{service_name}", config.max_attempts)
        
        logger.error("All retry attempts exhausted",
                    service=service_name,
                    max_attempts=config.max_attempts,
                    total_duration=total_duration,
                    final_error=str(last_error))
        
        return RetryResult(
            success=False,
            error=last_error,
            attempts=config.max_attempts,
            total_duration=total_duration
        )
    
    def _categorize_error(self, error: Exception, config: RetryConfig) -> ErrorCategory:
        """Categorize error to determine retry behavior"""
        
        # Check circuit breaker errors
        from src.services.circuit_breaker import CircuitBreakerError
        if isinstance(error, CircuitBreakerError):
            return ErrorCategory.CIRCUIT_BREAKER
        
        # Check rate limiting errors
        if "rate limit" in str(error).lower() or "too many requests" in str(error).lower():
            return ErrorCategory.RATE_LIMITED
        
        # Check explicit non-retryable exceptions
        non_retryable = config.non_retryable_exceptions or self.default_non_retryable_exceptions
        if any(isinstance(error, exc_type) for exc_type in non_retryable):
            return ErrorCategory.NON_RETRYABLE
        
        # Check explicit retryable exceptions
        retryable = config.retryable_exceptions or self.default_retryable_exceptions
        if any(isinstance(error, exc_type) for exc_type in retryable):
            return ErrorCategory.RETRYABLE
        
        # HTTP status code based categorization
        if hasattr(error, 'status_code'):
            status_code = error.status_code
            if 400 <= status_code < 500 and status_code != 429:  # 429 is rate limit
                return ErrorCategory.NON_RETRYABLE
            elif status_code >= 500 or status_code == 429:
                return ErrorCategory.RETRYABLE
        
        # Default to retryable for unknown errors
        return ErrorCategory.RETRYABLE
    
    def _should_retry(
        self,
        error: Exception,
        attempt: int,
        config: RetryConfig,
        error_category: ErrorCategory
    ) -> bool:
        """Determine if should retry based on error and attempt"""
        
        # Don't retry if max attempts reached
        if attempt >= config.max_attempts:
            return False
        
        # Don't retry non-retryable errors
        if error_category == ErrorCategory.NON_RETRYABLE:
            return False
        
        # Don't retry circuit breaker errors (circuit breaker handles timing)
        if error_category == ErrorCategory.CIRCUIT_BREAKER:
            return False
        
        # Retry rate limited errors with longer delay
        if error_category == ErrorCategory.RATE_LIMITED:
            return True
        
        # Retry retryable errors
        if error_category == ErrorCategory.RETRYABLE:
            return True
        
        return False
    
    def _calculate_delay(
        self,
        attempt: int,
        config: RetryConfig,
        error_category: ErrorCategory
    ) -> float:
        """Calculate delay before next retry attempt"""
        
        base_delay = config.base_delay
        
        # Longer delays for rate limiting
        if error_category == ErrorCategory.RATE_LIMITED:
            base_delay = min(config.base_delay * 5, 30.0)  # 5x delay, max 30s
        
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
            
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * attempt
            
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (config.backoff_multiplier ** (attempt - 1))
            
        elif config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0.0
            
        else:
            delay = base_delay
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter and delay > 0:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)  # Ensure non-negative
        
        return delay
    
    async def retry_payment_provider_call(
        self,
        func: Callable[[], Awaitable[Any]],
        provider_name: str,
        *args,
        **kwargs
    ) -> RetryResult:
        """Retry payment provider call with provider-specific configuration"""
        
        config = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=2.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter=True
        )
        
        return await self.retry_with_circuit_breaker(
            func, f"provider_{provider_name}", config, *args, **kwargs
        )
    
    async def retry_fraud_detection_call(
        self,
        func: Callable[[], Awaitable[Any]],
        *args,
        **kwargs
    ) -> RetryResult:
        """Retry fraud detection call with ML service configuration"""
        
        config = RetryConfig(
            max_attempts=2,  # Fewer retries for ML service
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=3.0,
            jitter=True
        )
        
        return await self.retry_with_circuit_breaker(
            func, "fraud_detection", config, *args, **kwargs
        )
    
    async def retry_database_operation(
        self,
        func: Callable[[], Awaitable[Any]],
        *args,
        **kwargs
    ) -> RetryResult:
        """Retry database operation with database-specific configuration"""
        
        config = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=0.5,
            max_delay=5.0,
            backoff_multiplier=2.0,
            jitter=True
        )
        
        return await self.retry_with_circuit_breaker(
            func, "database", config, *args, **kwargs
        )
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        # This would be enhanced with actual stats collection
        return {
            "total_operations": len(self.retry_stats),
            "services": list(self.retry_stats.keys()) if self.retry_stats else [],
            "timestamp": datetime.now().isoformat()
        }

# Global enhanced retry service
enhanced_retry_service = EnhancedRetryService()
