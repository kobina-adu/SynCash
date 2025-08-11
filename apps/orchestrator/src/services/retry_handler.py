"""
Retry and Fallback Logic for SyncCash Orchestrator
Handles failed payment attempts with exponential backoff and provider switching
"""
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from decimal import Decimal
from datetime import datetime, timedelta
import structlog

from src.models.transaction import Transaction, TransactionStatus, PaymentProvider
from src.core.database import get_db_session
from src.monitoring.metrics import metrics
from src.services.provider_selector import provider_selector

logger = structlog.get_logger(__name__)

class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0  # seconds
        self.exponential_base = 2
        self.jitter = True
        
        # Provider-specific retry limits
        self.provider_retry_limits = {
            PaymentProvider.MTN_MOMO: 3,
            PaymentProvider.AIRTELTIGO: 2,
            PaymentProvider.VODAFONE: 3
        }
        
        # Retryable error types
        self.retryable_errors = {
            "NETWORK_ERROR",
            "TIMEOUT",
            "TEMPORARY_UNAVAILABLE",
            "RATE_LIMITED",
            "PROVIDER_BUSY"
        }
        
        # Non-retryable errors
        self.non_retryable_errors = {
            "INSUFFICIENT_FUNDS",
            "INVALID_ACCOUNT",
            "FRAUD_DETECTED",
            "ACCOUNT_BLOCKED",
            "INVALID_AMOUNT"
        }

class RetryHandler:
    """Handles retry logic with exponential backoff and fallback providers"""
    
    def __init__(self):
        self.config = RetryConfig()
        self.active_retries = {}  # Track ongoing retry attempts
    
    async def execute_with_retry(
        self,
        transaction: Transaction,
        operation: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute operation with retry logic and fallback providers
        """
        transaction_id = str(transaction.id)
        
        try:
            # Initialize retry tracking
            if transaction_id not in self.active_retries:
                self.active_retries[transaction_id] = {
                    "attempt_count": 0,
                    "provider_attempts": {},
                    "start_time": datetime.now(),
                    "original_provider": transaction.provider
                }
            
            retry_info = self.active_retries[transaction_id]
            current_provider = transaction.provider
            
            # Try current provider first
            result = await self._attempt_with_provider(
                transaction, current_provider, operation, retry_info, *args, **kwargs
            )
            
            if result["success"]:
                # Clean up retry tracking on success
                self._cleanup_retry_tracking(transaction_id)
                return result
            
            # If current provider failed, try fallback providers
            fallback_result = await self._try_fallback_providers(
                transaction, operation, retry_info, *args, **kwargs
            )
            
            # Clean up retry tracking
            self._cleanup_retry_tracking(transaction_id)
            
            return fallback_result
            
        except Exception as e:
            logger.error("Retry execution failed", 
                        exc_info=e, 
                        transaction_id=transaction_id)
            
            self._cleanup_retry_tracking(transaction_id)
            metrics.record_error("retry_execution_error", "retry_handler")
            
            return {
                "success": False,
                "error": f"Retry execution failed: {str(e)}",
                "retry_exhausted": True
            }
    
    async def _attempt_with_provider(
        self,
        transaction: Transaction,
        provider: PaymentProvider,
        operation: Callable,
        retry_info: Dict,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Attempt operation with specific provider and retry logic"""
        
        provider_key = provider.value
        max_retries = self.config.provider_retry_limits.get(provider, self.config.max_retries)
        
        # Initialize provider attempt tracking
        if provider_key not in retry_info["provider_attempts"]:
            retry_info["provider_attempts"][provider_key] = {
                "count": 0,
                "last_error": None,
                "last_attempt": None
            }
        
        provider_attempts = retry_info["provider_attempts"][provider_key]
        
        for attempt in range(max_retries):
            try:
                provider_attempts["count"] += 1
                provider_attempts["last_attempt"] = datetime.now()
                retry_info["attempt_count"] += 1
                
                logger.info("Attempting payment with provider",
                           transaction_id=str(transaction.id),
                           provider=provider.value,
                           attempt=attempt + 1,
                           max_retries=max_retries)
                
                # Execute the operation
                start_time = time.time()
                result = await operation(transaction, provider, *args, **kwargs)
                duration = time.time() - start_time
                
                # Record metrics
                metrics.record_provider_request(
                    provider=provider.value,
                    status="success" if result.get("success") else "error",
                    duration=duration
                )
                
                if result.get("success"):
                    logger.info("Payment successful with provider",
                               transaction_id=str(transaction.id),
                               provider=provider.value,
                               attempt=attempt + 1)
                    
                    # Record provider success
                    provider_selector.health_tracker.record_provider_success(provider)
                    
                    return result
                
                # Check if error is retryable
                error_type = result.get("error_type", "UNKNOWN")
                if not self._is_retryable_error(error_type):
                    logger.warning("Non-retryable error encountered",
                                  transaction_id=str(transaction.id),
                                  provider=provider.value,
                                  error_type=error_type)
                    
                    provider_attempts["last_error"] = result.get("error")
                    return result
                
                # Record retryable error
                provider_attempts["last_error"] = result.get("error")
                provider_selector.health_tracker.record_provider_error(provider)
                
                # Calculate delay for next attempt
                if attempt < max_retries - 1:  # Don't delay after last attempt
                    delay = self._calculate_delay(attempt)
                    logger.info("Retrying after delay",
                               transaction_id=str(transaction.id),
                               provider=provider.value,
                               delay=delay,
                               next_attempt=attempt + 2)
                    
                    await asyncio.sleep(delay)
                
            except Exception as e:
                provider_attempts["last_error"] = str(e)
                provider_selector.health_tracker.record_provider_error(provider)
                
                logger.error("Provider attempt failed with exception",
                            exc_info=e,
                            transaction_id=str(transaction.id),
                            provider=provider.value,
                            attempt=attempt + 1)
                
                if attempt < max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted for this provider
        logger.warning("All retries exhausted for provider",
                      transaction_id=str(transaction.id),
                      provider=provider.value,
                      attempts=max_retries)
        
        return {
            "success": False,
            "error": provider_attempts["last_error"] or "All retries exhausted",
            "provider_exhausted": True,
            "attempts": max_retries
        }
    
    async def _try_fallback_providers(
        self,
        transaction: Transaction,
        operation: Callable,
        retry_info: Dict,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Try alternative providers as fallback"""
        
        original_provider = transaction.provider
        transaction_amount = Decimal(str(transaction.amount))
        
        try:
            # Get alternative providers
            available_providers = await provider_selector._get_available_providers(transaction_amount)
            
            # Remove original provider from alternatives
            fallback_providers = [p for p in available_providers if p != original_provider]
            
            if not fallback_providers:
                logger.warning("No fallback providers available",
                              transaction_id=str(transaction.id),
                              original_provider=original_provider.value)
                
                return {
                    "success": False,
                    "error": "No fallback providers available",
                    "retry_exhausted": True
                }
            
            logger.info("Attempting fallback providers",
                       transaction_id=str(transaction.id),
                       original_provider=original_provider.value,
                       fallback_providers=[p.value for p in fallback_providers])
            
            # Try each fallback provider
            for fallback_provider in fallback_providers:
                # Update transaction provider
                transaction.provider = fallback_provider
                
                result = await self._attempt_with_provider(
                    transaction, fallback_provider, operation, retry_info, *args, **kwargs
                )
                
                if result["success"]:
                    logger.info("Fallback provider successful",
                               transaction_id=str(transaction.id),
                               fallback_provider=fallback_provider.value,
                               original_provider=original_provider.value)
                    
                    return result
            
            # All fallback providers failed
            logger.error("All fallback providers failed",
                        transaction_id=str(transaction.id),
                        tried_providers=[p.value for p in fallback_providers])
            
            return {
                "success": False,
                "error": "All providers failed",
                "retry_exhausted": True,
                "fallback_exhausted": True
            }
            
        except Exception as e:
            logger.error("Fallback provider attempt failed", 
                        exc_info=e,
                        transaction_id=str(transaction.id))
            
            return {
                "success": False,
                "error": f"Fallback failed: {str(e)}",
                "retry_exhausted": True
            }
    
    def _is_retryable_error(self, error_type: str) -> bool:
        """Check if error type is retryable"""
        if error_type in self.config.non_retryable_errors:
            return False
        
        return error_type in self.config.retryable_errors or error_type == "UNKNOWN"
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.config.jitter:
            import random
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter
        
        return delay
    
    def _cleanup_retry_tracking(self, transaction_id: str):
        """Clean up retry tracking for completed transaction"""
        if transaction_id in self.active_retries:
            retry_info = self.active_retries[transaction_id]
            total_duration = (datetime.now() - retry_info["start_time"]).total_seconds()
            
            logger.info("Retry session completed",
                       transaction_id=transaction_id,
                       total_attempts=retry_info["attempt_count"],
                       duration=total_duration)
            
            del self.active_retries[transaction_id]
    
    def get_retry_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get current retry status for transaction"""
        return self.active_retries.get(transaction_id)
    
    async def ensure_idempotency(self, transaction: Transaction) -> bool:
        """Ensure transaction idempotency to avoid duplicate charges"""
        try:
            async with get_db_session() as session:
                # Check for existing successful transactions with same idempotency key
                # This would typically use a unique business identifier
                existing = await session.execute(
                    "SELECT id FROM transactions WHERE user_id = :user_id AND amount = :amount "
                    "AND recipient_phone = :phone AND status = 'confirmed' "
                    "AND created_at > :recent_time",
                    {
                        "user_id": transaction.user_id,
                        "amount": transaction.amount,
                        "phone": transaction.recipient_phone,
                        "recent_time": datetime.now() - timedelta(minutes=5)
                    }
                )
                
                if existing.fetchone():
                    logger.warning("Duplicate transaction detected",
                                  transaction_id=str(transaction.id),
                                  user_id=transaction.user_id)
                    return False
                
                return True
                
        except Exception as e:
            logger.error("Idempotency check failed", exc_info=e)
            return True  # Allow transaction to proceed if check fails

# Global retry handler instance
retry_handler = RetryHandler()
