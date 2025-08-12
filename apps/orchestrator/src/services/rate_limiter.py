"""
Rate Limiting Service for SyncCash Orchestrator
Advanced rate limiting with multiple algorithms and abuse protection
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import structlog
from collections import defaultdict, deque

from src.core.redis_client import get_redis_client
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"

class RateLimitScope(Enum):
    """Rate limit scope"""
    USER = "user"
    IP = "ip"
    API_KEY = "api_key"
    GLOBAL = "global"
    ENDPOINT = "endpoint"

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_window: int = 100
    window_seconds: int = 60
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.USER
    burst_allowance: int = 10  # Additional requests allowed in burst
    block_duration_seconds: int = 300  # Block duration when limit exceeded

class RateLimitResult:
    """Rate limit check result"""
    
    def __init__(self, allowed: bool, remaining: int = 0, reset_time: Optional[datetime] = None,
                 retry_after: Optional[int] = None, reason: str = ""):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after
        self.reason = reason

class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket"""
        async with self._lock:
            now = time.time()
            
            # Refill tokens based on time elapsed
            time_passed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def get_remaining(self) -> int:
        """Get remaining tokens"""
        return int(self.tokens)

class SlidingWindowCounter:
    """Sliding window rate limiter implementation"""
    
    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def is_allowed(self) -> tuple[bool, int]:
        """Check if request is allowed"""
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old requests outside window
            while self.requests and self.requests[0] <= cutoff:
                self.requests.popleft()
            
            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True, self.max_requests - len(self.requests)
            
            return False, 0

class RateLimiterService:
    """Advanced rate limiting service"""
    
    def __init__(self):
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.blocked_keys: Dict[str, datetime] = {}
        self.rate_limit_configs: Dict[str, RateLimitConfig] = {}
        
        # Default configurations
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default rate limit configurations"""
        
        # API endpoint limits
        self.rate_limit_configs.update({
            "payments_initiate": RateLimitConfig(
                requests_per_window=10,
                window_seconds=60,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.USER,
                burst_allowance=3,
                block_duration_seconds=300
            ),
            "payments_status": RateLimitConfig(
                requests_per_window=100,
                window_seconds=60,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.USER,
                burst_allowance=20,
                block_duration_seconds=60
            ),
            "refund_requests": RateLimitConfig(
                requests_per_window=5,
                window_seconds=300,  # 5 minutes
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.USER,
                burst_allowance=1,
                block_duration_seconds=600
            ),
            "health_checks": RateLimitConfig(
                requests_per_window=1000,
                window_seconds=60,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.IP,
                burst_allowance=100,
                block_duration_seconds=60
            ),
            "global_api": RateLimitConfig(
                requests_per_window=10000,
                window_seconds=60,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.GLOBAL,
                burst_allowance=1000,
                block_duration_seconds=300
            )
        })
    
    async def check_rate_limit(
        self,
        key: str,
        endpoint: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> RateLimitResult:
        """Check if request is within rate limits"""
        
        config = self.rate_limit_configs.get(endpoint)
        if not config:
            # No rate limit configured, allow request
            return RateLimitResult(allowed=True)
        
        # Build rate limit key based on scope
        rate_limit_key = self._build_rate_limit_key(key, endpoint, config.scope, user_id, ip_address)
        
        # Check if key is currently blocked
        if await self._is_blocked(rate_limit_key):
            return RateLimitResult(
                allowed=False,
                reason="Rate limit exceeded, currently blocked",
                retry_after=self._get_block_remaining_time(rate_limit_key)
            )
        
        # Apply rate limiting algorithm
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            result = await self._check_token_bucket(rate_limit_key, config)
        elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            result = await self._check_sliding_window(rate_limit_key, config)
        else:
            # Default to sliding window
            result = await self._check_sliding_window(rate_limit_key, config)
        
        # Record metrics
        if result.allowed:
            metrics.record_counter(f"rate_limit_allowed_{endpoint}")
        else:
            metrics.record_counter(f"rate_limit_blocked_{endpoint}")
            
            # Block key if limit exceeded
            await self._block_key(rate_limit_key, config.block_duration_seconds)
            
            logger.warning("Rate limit exceeded",
                          endpoint=endpoint,
                          rate_limit_key=rate_limit_key,
                          config=config.__dict__)
        
        return result
    
    def _build_rate_limit_key(
        self,
        base_key: str,
        endpoint: str,
        scope: RateLimitScope,
        user_id: Optional[str],
        ip_address: Optional[str]
    ) -> str:
        """Build rate limit key based on scope"""
        
        if scope == RateLimitScope.USER and user_id:
            return f"rate_limit:user:{user_id}:{endpoint}"
        elif scope == RateLimitScope.IP and ip_address:
            return f"rate_limit:ip:{ip_address}:{endpoint}"
        elif scope == RateLimitScope.GLOBAL:
            return f"rate_limit:global:{endpoint}"
        elif scope == RateLimitScope.ENDPOINT:
            return f"rate_limit:endpoint:{endpoint}"
        else:
            return f"rate_limit:key:{base_key}:{endpoint}"
    
    async def _check_token_bucket(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using token bucket algorithm"""
        
        if key not in self.token_buckets:
            capacity = config.requests_per_window + config.burst_allowance
            refill_rate = config.requests_per_window / config.window_seconds
            self.token_buckets[key] = TokenBucket(capacity, refill_rate)
        
        bucket = self.token_buckets[key]
        allowed = await bucket.consume(1)
        remaining = bucket.get_remaining()
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reason="Token bucket limit" if not allowed else ""
        )
    
    async def _check_sliding_window(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using sliding window algorithm"""
        
        if key not in self.sliding_windows:
            max_requests = config.requests_per_window + config.burst_allowance
            self.sliding_windows[key] = SlidingWindowCounter(config.window_seconds, max_requests)
        
        window = self.sliding_windows[key]
        allowed, remaining = await window.is_allowed()
        
        reset_time = datetime.now() + timedelta(seconds=config.window_seconds)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            reason="Sliding window limit" if not allowed else ""
        )
    
    async def _is_blocked(self, key: str) -> bool:
        """Check if key is currently blocked"""
        if key in self.blocked_keys:
            if datetime.now() < self.blocked_keys[key]:
                return True
            else:
                # Block expired, remove it
                del self.blocked_keys[key]
        return False
    
    async def _block_key(self, key: str, duration_seconds: int):
        """Block key for specified duration"""
        block_until = datetime.now() + timedelta(seconds=duration_seconds)
        self.blocked_keys[key] = block_until
        
        metrics.record_counter("rate_limit_key_blocked")
        logger.info("Key blocked due to rate limit",
                   key=key,
                   block_duration=duration_seconds,
                   block_until=block_until.isoformat())
    
    def _get_block_remaining_time(self, key: str) -> Optional[int]:
        """Get remaining block time in seconds"""
        if key in self.blocked_keys:
            remaining = (self.blocked_keys[key] - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return None
    
    async def reset_rate_limit(self, key: str, endpoint: str):
        """Reset rate limit for specific key and endpoint"""
        rate_limit_key = f"rate_limit:key:{key}:{endpoint}"
        
        # Remove from all tracking structures
        self.token_buckets.pop(rate_limit_key, None)
        self.sliding_windows.pop(rate_limit_key, None)
        self.blocked_keys.pop(rate_limit_key, None)
        
        logger.info("Rate limit reset", key=key, endpoint=endpoint)
    
    async def get_rate_limit_status(self, key: str, endpoint: str) -> Dict[str, Any]:
        """Get current rate limit status"""
        config = self.rate_limit_configs.get(endpoint)
        if not config:
            return {"error": "No rate limit configured for endpoint"}
        
        rate_limit_key = f"rate_limit:key:{key}:{endpoint}"
        
        status = {
            "endpoint": endpoint,
            "key": key,
            "config": {
                "requests_per_window": config.requests_per_window,
                "window_seconds": config.window_seconds,
                "algorithm": config.algorithm.value,
                "burst_allowance": config.burst_allowance
            },
            "blocked": await self._is_blocked(rate_limit_key),
            "block_remaining_seconds": self._get_block_remaining_time(rate_limit_key)
        }
        
        # Add algorithm-specific status
        if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET and rate_limit_key in self.token_buckets:
            bucket = self.token_buckets[rate_limit_key]
            status["tokens_remaining"] = bucket.get_remaining()
        
        elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW and rate_limit_key in self.sliding_windows:
            window = self.sliding_windows[rate_limit_key]
            status["requests_in_window"] = len(window.requests)
            status["requests_remaining"] = window.max_requests - len(window.requests)
        
        return status
    
    def add_rate_limit_config(self, endpoint: str, config: RateLimitConfig):
        """Add custom rate limit configuration"""
        self.rate_limit_configs[endpoint] = config
        logger.info("Rate limit configuration added",
                   endpoint=endpoint,
                   config=config.__dict__)
    
    async def cleanup_expired_data(self):
        """Cleanup expired rate limit data"""
        now = datetime.now()
        
        # Remove expired blocks
        expired_blocks = [key for key, expiry in self.blocked_keys.items() if now >= expiry]
        for key in expired_blocks:
            del self.blocked_keys[key]
        
        if expired_blocks:
            logger.debug("Cleaned up expired rate limit blocks", count=len(expired_blocks))
        
        metrics.record_gauge("rate_limit_active_blocks", len(self.blocked_keys))
        metrics.record_gauge("rate_limit_active_buckets", len(self.token_buckets))
        metrics.record_gauge("rate_limit_active_windows", len(self.sliding_windows))

# Global rate limiter service
rate_limiter = RateLimiterService()
