"""
Provider Selection Service for SyncCash Orchestrator
Handles intelligent provider selection based on multiple criteria
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import structlog

from src.models.transaction import PaymentProvider, Transaction
from src.core.database import get_db_session
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class ProviderHealthStatus:
    """Track provider health and availability"""
    
    def __init__(self):
        self.provider_status = {
            PaymentProvider.MTN_MOMO: {"healthy": True, "last_check": datetime.now(), "error_count": 0},
            PaymentProvider.AIRTELTIGO: {"healthy": True, "last_check": datetime.now(), "error_count": 0},
            PaymentProvider.VODAFONE: {"healthy": True, "last_check": datetime.now(), "error_count": 0}
        }
        self.max_error_threshold = 5
        self.health_check_interval = timedelta(minutes=5)
    
    async def check_provider_health(self, provider: PaymentProvider) -> bool:
        """Check if provider is healthy and available"""
        status = self.provider_status.get(provider)
        if not status:
            return False
        
        # Check if health check is recent
        if datetime.now() - status["last_check"] > self.health_check_interval:
            # TODO: Implement actual provider health check API call
            status["last_check"] = datetime.now()
        
        return status["healthy"] and status["error_count"] < self.max_error_threshold
    
    def record_provider_error(self, provider: PaymentProvider):
        """Record provider error for health tracking"""
        if provider in self.provider_status:
            self.provider_status[provider]["error_count"] += 1
            
            # Mark as unhealthy if too many errors
            if self.provider_status[provider]["error_count"] >= self.max_error_threshold:
                self.provider_status[provider]["healthy"] = False
                logger.warning("Provider marked as unhealthy", provider=provider.value)
    
    def record_provider_success(self, provider: PaymentProvider):
        """Record provider success - reset error count"""
        if provider in self.provider_status:
            self.provider_status[provider]["error_count"] = 0
            self.provider_status[provider]["healthy"] = True

class ProviderSelector:
    """Intelligent provider selection based on multiple criteria"""
    
    def __init__(self):
        self.health_tracker = ProviderHealthStatus()
        
        # Provider configuration
        self.provider_config = {
            PaymentProvider.MTN_MOMO: {
                "max_amount": Decimal("10000.00"),
                "fee_percentage": Decimal("0.01"),  # 1%
                "processing_time": 30,  # seconds
                "priority": 1
            },
            PaymentProvider.AIRTELTIGO: {
                "max_amount": Decimal("5000.00"),
                "fee_percentage": Decimal("0.015"),  # 1.5%
                "processing_time": 45,  # seconds
                "priority": 2
            },
            PaymentProvider.VODAFONE: {
                "max_amount": Decimal("8000.00"),
                "fee_percentage": Decimal("0.012"),  # 1.2%
                "processing_time": 35,  # seconds
                "priority": 3
            }
        }
    
    async def select_provider(self, amount: Decimal, user_preferences: Optional[Dict] = None) -> PaymentProvider:
        """
        Select best provider based on amount, health, fees, and user preferences
        """
        try:
            # Get available providers
            available_providers = await self._get_available_providers(amount)
            
            if not available_providers:
                raise ValueError("No available providers for this transaction")
            
            # Apply user preferences if provided
            if user_preferences and user_preferences.get("preferred_provider"):
                preferred = PaymentProvider(user_preferences["preferred_provider"])
                if preferred in available_providers:
                    logger.info("Using user preferred provider", provider=preferred.value)
                    return preferred
            
            # Select best provider based on criteria
            best_provider = await self._select_optimal_provider(available_providers, amount)
            
            logger.info("Provider selected", 
                       provider=best_provider.value,
                       amount=float(amount),
                       criteria="optimal_selection")
            
            return best_provider
            
        except Exception as e:
            logger.error("Provider selection failed", exc_info=e, amount=float(amount))
            metrics.record_error("provider_selection_error", "provider_selector")
            raise
    
    async def select_providers_for_split_payment(self, amount: Decimal, max_providers: int = 2) -> List[Tuple[PaymentProvider, Decimal]]:
        """
        Select multiple providers for split payment
        Returns list of (provider, amount) tuples
        """
        try:
            available_providers = await self._get_available_providers(amount)
            
            if not available_providers:
                raise ValueError("No available providers for split payment")
            
            # Sort providers by priority and capacity
            sorted_providers = sorted(
                available_providers,
                key=lambda p: (
                    self.provider_config[p]["priority"],
                    -float(self.provider_config[p]["max_amount"])
                )
            )
            
            # Split amount across providers
            split_payments = []
            remaining_amount = amount
            
            for provider in sorted_providers[:max_providers]:
                if remaining_amount <= 0:
                    break
                
                max_amount = self.provider_config[provider]["max_amount"]
                provider_amount = min(remaining_amount, max_amount)
                
                split_payments.append((provider, provider_amount))
                remaining_amount -= provider_amount
            
            if remaining_amount > 0:
                raise ValueError(f"Cannot split payment: {remaining_amount} remaining")
            
            logger.info("Split payment providers selected",
                       providers=[p.value for p, _ in split_payments],
                       amounts=[float(a) for _, a in split_payments])
            
            return split_payments
            
        except Exception as e:
            logger.error("Split payment provider selection failed", exc_info=e)
            metrics.record_error("split_payment_selection_error", "provider_selector")
            raise
    
    async def _get_available_providers(self, amount: Decimal) -> List[PaymentProvider]:
        """Get list of available providers for given amount"""
        available = []
        
        for provider, config in self.provider_config.items():
            # Check health status
            if not await self.health_tracker.check_provider_health(provider):
                logger.debug("Provider unhealthy", provider=provider.value)
                continue
            
            # Check amount limits
            if amount > config["max_amount"]:
                logger.debug("Amount exceeds provider limit", 
                           provider=provider.value,
                           amount=float(amount),
                           limit=float(config["max_amount"]))
                continue
            
            # TODO: Check provider balance/availability via API
            
            available.append(provider)
        
        return available
    
    async def _select_optimal_provider(self, providers: List[PaymentProvider], amount: Decimal) -> PaymentProvider:
        """Select optimal provider based on fees, speed, and reliability"""
        if len(providers) == 1:
            return providers[0]
        
        # Calculate scores for each provider
        provider_scores = {}
        
        for provider in providers:
            config = self.provider_config[provider]
            
            # Fee score (lower fees = higher score)
            fee_amount = amount * config["fee_percentage"]
            fee_score = 100 - float(fee_amount)
            
            # Speed score (faster = higher score)
            speed_score = 100 - config["processing_time"]
            
            # Priority score (higher priority = higher score)
            priority_score = 100 - (config["priority"] * 10)
            
            # Health score
            health_status = self.health_tracker.provider_status[provider]
            health_score = 100 - (health_status["error_count"] * 10)
            
            # Combined score
            total_score = (fee_score * 0.3) + (speed_score * 0.3) + (priority_score * 0.2) + (health_score * 0.2)
            provider_scores[provider] = total_score
            
            logger.debug("Provider scoring",
                        provider=provider.value,
                        fee_score=fee_score,
                        speed_score=speed_score,
                        priority_score=priority_score,
                        health_score=health_score,
                        total_score=total_score)
        
        # Select provider with highest score
        best_provider = max(provider_scores.keys(), key=lambda p: provider_scores[p])
        
        return best_provider
    
    def get_provider_fee(self, provider: PaymentProvider, amount: Decimal) -> Decimal:
        """Calculate provider fee for given amount"""
        config = self.provider_config.get(provider)
        if not config:
            return Decimal("0")
        
        return amount * config["fee_percentage"]
    
    def get_estimated_processing_time(self, provider: PaymentProvider) -> int:
        """Get estimated processing time in seconds"""
        config = self.provider_config.get(provider)
        return config["processing_time"] if config else 60

# Global provider selector instance
provider_selector = ProviderSelector()
