"""
Circuit Breaker Service for SyncCash Orchestrator
Implements resilience patterns for external service calls
"""
import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog

from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures to trigger open state
    success_threshold: int = 3          # Successes to close from half-open
    timeout_seconds: int = 60           # Time to wait before half-open
    slow_call_threshold: float = 5.0    # Seconds to consider call slow
    slow_call_rate_threshold: float = 0.5  # Rate of slow calls to trigger
    minimum_calls: int = 10             # Minimum calls before evaluation

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    slow_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    call_times: list = field(default_factory=list)

class CircuitBreakerError(Exception):
    """Circuit breaker is open"""
    pass

class CircuitBreaker:
    """Circuit breaker implementation for external service calls"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.last_state_change = datetime.now()
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[[], Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = datetime.now()
                    logger.info("Circuit breaker transitioning to HALF_OPEN", 
                               circuit=self.name)
                else:
                    metrics.record_counter(f"circuit_breaker_blocked_{self.name}")
                    raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN")
        
        # Execute the function call
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            call_duration = time.time() - start_time
            
            async with self._lock:
                await self._record_success(call_duration)
            
            return result
            
        except Exception as e:
            call_duration = time.time() - start_time
            
            async with self._lock:
                await self._record_failure(call_duration, str(e))
            
            raise
    
    async def _record_success(self, call_duration: float):
        """Record successful call"""
        self.stats.total_calls += 1
        self.stats.successful_calls += 1
        self.stats.consecutive_successes += 1
        self.stats.consecutive_failures = 0
        self.stats.last_success_time = datetime.now()
        
        # Track call times for slow call detection
        self.stats.call_times.append(call_duration)
        if len(self.stats.call_times) > 100:  # Keep last 100 calls
            self.stats.call_times.pop(0)
        
        if call_duration > self.config.slow_call_threshold:
            self.stats.slow_calls += 1
        
        # State transitions
        if self.state == CircuitState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.last_state_change = datetime.now()
                logger.info("Circuit breaker closed after recovery", 
                           circuit=self.name,
                           consecutive_successes=self.stats.consecutive_successes)
        
        metrics.record_counter(f"circuit_breaker_success_{self.name}")
        metrics.record_histogram(f"circuit_breaker_call_duration_{self.name}", call_duration)
    
    async def _record_failure(self, call_duration: float, error: str):
        """Record failed call"""
        self.stats.total_calls += 1
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0
        self.stats.last_failure_time = datetime.now()
        
        # Track call times
        self.stats.call_times.append(call_duration)
        if len(self.stats.call_times) > 100:
            self.stats.call_times.pop(0)
        
        if call_duration > self.config.slow_call_threshold:
            self.stats.slow_calls += 1
        
        # Check if should open circuit
        if (self.state == CircuitState.CLOSED and 
            self._should_open_circuit()):
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            logger.warning("Circuit breaker opened due to failures",
                          circuit=self.name,
                          consecutive_failures=self.stats.consecutive_failures,
                          failure_rate=self._get_failure_rate())
        
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            logger.warning("Circuit breaker reopened after failed test",
                          circuit=self.name, error=error)
        
        metrics.record_counter(f"circuit_breaker_failure_{self.name}")
        metrics.record_histogram(f"circuit_breaker_call_duration_{self.name}", call_duration)
    
    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened"""
        # Not enough calls to evaluate
        if self.stats.total_calls < self.config.minimum_calls:
            return False
        
        # Check failure threshold
        if self.stats.consecutive_failures >= self.config.failure_threshold:
            return True
        
        # Check slow call rate
        recent_calls = self.stats.call_times[-self.config.minimum_calls:]
        if len(recent_calls) >= self.config.minimum_calls:
            slow_calls = sum(1 for t in recent_calls if t > self.config.slow_call_threshold)
            slow_rate = slow_calls / len(recent_calls)
            
            if slow_rate >= self.config.slow_call_rate_threshold:
                logger.warning("Circuit breaker opening due to slow calls",
                              circuit=self.name,
                              slow_call_rate=slow_rate,
                              threshold=self.config.slow_call_rate_threshold)
                return True
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt to reset from open state"""
        if self.state != CircuitState.OPEN:
            return False
        
        time_since_open = datetime.now() - self.last_state_change
        return time_since_open.total_seconds() >= self.config.timeout_seconds
    
    def _get_failure_rate(self) -> float:
        """Calculate current failure rate"""
        if self.stats.total_calls == 0:
            return 0.0
        return self.stats.failed_calls / self.stats.total_calls
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "slow_calls": self.stats.slow_calls,
            "failure_rate": self._get_failure_rate(),
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "slow_call_threshold": self.config.slow_call_threshold,
                "slow_call_rate_threshold": self.config.slow_call_rate_threshold,
                "minimum_calls": self.config.minimum_calls
            }
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.last_state_change = datetime.now()
        logger.info("Circuit breaker manually reset", circuit=self.name)

class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers"""
        return {
            name: cb.get_stats() 
            for name, cb in self.circuit_breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Convenience function for common circuit breaker configurations
def get_provider_circuit_breaker(provider_name: str) -> CircuitBreaker:
    """Get circuit breaker for payment provider"""
    config = CircuitBreakerConfig(
        failure_threshold=3,        # Open after 3 failures
        success_threshold=2,        # Close after 2 successes  
        timeout_seconds=30,         # Try again after 30 seconds
        slow_call_threshold=10.0,   # 10 seconds is slow for payments
        slow_call_rate_threshold=0.6,  # 60% slow calls triggers opening
        minimum_calls=5             # Need 5 calls to evaluate
    )
    return circuit_breaker_manager.get_circuit_breaker(f"provider_{provider_name}", config)

def get_fraud_detection_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for fraud detection service"""
    config = CircuitBreakerConfig(
        failure_threshold=5,        # More tolerant for fraud service
        success_threshold=3,
        timeout_seconds=60,         # Longer timeout for ML service
        slow_call_threshold=3.0,    # 3 seconds is slow for fraud check
        slow_call_rate_threshold=0.7,
        minimum_calls=10
    )
    return circuit_breaker_manager.get_circuit_breaker("fraud_detection", config)
