"""
Provider factory and manager for SyncCash payment providers
Handles provider instantiation, selection, and management
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
import structlog

from .base import BasePaymentProvider, ProviderType, ProviderError
from .mtn_momo import MTNMoMoProvider
from .airteltigo_money import AirtelTigoProvider
from .vodafone_cash import VodafoneCashProvider

logger = structlog.get_logger(__name__)

class ProviderFactory:
    """Factory for creating payment provider instances"""
    
    _provider_classes = {
        ProviderType.MTN_MOMO: MTNMoMoProvider,
        ProviderType.AIRTELTIGO_MONEY: AirtelTigoProvider,
        ProviderType.VODAFONE_CASH: VodafoneCashProvider
    }
    
    @classmethod
    def create_provider(cls, provider_type: ProviderType, config: Dict[str, Any]) -> BasePaymentProvider:
        """Create a provider instance"""
        if provider_type not in cls._provider_classes:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        provider_class = cls._provider_classes[provider_type]
        return provider_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[ProviderType]:
        """Get list of supported provider types"""
        return list(cls._provider_classes.keys())

class ProviderManager:
    """Manages multiple payment providers and handles provider selection"""
    
    def __init__(self, provider_configs: Dict[str, Dict[str, Any]]):
        self.providers: Dict[ProviderType, BasePaymentProvider] = {}
        self.provider_health: Dict[ProviderType, bool] = {}
        self.logger = structlog.get_logger("provider_manager")
        
        # Initialize providers
        for provider_name, config in provider_configs.items():
            try:
                provider_type = ProviderType(provider_name.lower())
                provider = ProviderFactory.create_provider(provider_type, config)
                self.providers[provider_type] = provider
                self.provider_health[provider_type] = True
                
                self.logger.info("Provider initialized", provider=provider_type)
            except Exception as e:
                self.logger.error("Failed to initialize provider", 
                                provider=provider_name, exc_info=e)
    
    async def authenticate_all(self) -> Dict[ProviderType, bool]:
        """Authenticate all providers"""
        results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                success = await provider.authenticate()
                results[provider_type] = success
                self.provider_health[provider_type] = success
                
                if success:
                    self.logger.info("Provider authenticated", provider=provider_type)
                else:
                    self.logger.warning("Provider authentication failed", provider=provider_type)
            except Exception as e:
                self.logger.error("Provider authentication error", 
                                provider=provider_type, exc_info=e)
                results[provider_type] = False
                self.provider_health[provider_type] = False
        
        return results
    
    def get_provider(self, provider_type: ProviderType) -> Optional[BasePaymentProvider]:
        """Get specific provider instance"""
        return self.providers.get(provider_type)
    
    def get_provider_for_phone(self, phone_number: str) -> Optional[BasePaymentProvider]:
        """Get the appropriate provider for a phone number"""
        # Format phone number
        phone = self._format_phone_number(phone_number)
        
        # Check each provider to see if they support this number
        for provider_type, provider in self.providers.items():
            if not self.provider_health.get(provider_type, False):
                continue
                
            try:
                # Use synchronous validation for provider selection
                if self._validate_phone_for_provider(phone, provider_type):
                    self.logger.info("Provider selected for phone", 
                                   phone=phone[:6] + "****", provider=provider_type)
                    return provider
            except Exception as e:
                self.logger.warning("Error validating phone for provider",
                                  provider=provider_type, exc_info=e)
                continue
        
        self.logger.warning("No provider found for phone number", phone=phone[:6] + "****")
        return None
    
    def _validate_phone_for_provider(self, phone_number: str, provider_type: ProviderType) -> bool:
        """Validate phone number for specific provider (synchronous)"""
        # Remove country code for prefix check
        phone = phone_number
        if phone.startswith("233"):
            phone = phone[3:]
        
        # Provider-specific prefix mapping
        provider_prefixes = {
            ProviderType.MTN_MOMO: ["24", "54", "55", "59"],
            ProviderType.AIRTELTIGO_MONEY: ["26", "27", "56", "57"],
            ProviderType.VODAFONE_CASH: ["20", "50"]
        }
        
        prefixes = provider_prefixes.get(provider_type, [])
        return any(phone.startswith(prefix) for prefix in prefixes)
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number consistently"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone_number))
        
        # Handle Ghana phone numbers
        if phone.startswith('0'):
            phone = '233' + phone[1:]
        elif not phone.startswith('233'):
            phone = '233' + phone
            
        return phone
    
    def get_healthy_providers(self) -> List[ProviderType]:
        """Get list of healthy providers"""
        return [provider_type for provider_type, healthy in self.provider_health.items() if healthy]
    
    def get_provider_by_preference(self, phone_number: str, 
                                 preferred_providers: Optional[List[ProviderType]] = None) -> Optional[BasePaymentProvider]:
        """Get provider based on phone number and preference order"""
        # First try to get the natural provider for the phone number
        natural_provider = self.get_provider_for_phone(phone_number)
        if natural_provider and natural_provider.provider_type in self.get_healthy_providers():
            return natural_provider
        
        # If preferred providers specified, try them in order
        if preferred_providers:
            for provider_type in preferred_providers:
                if (provider_type in self.providers and 
                    self.provider_health.get(provider_type, False)):
                    return self.providers[provider_type]
        
        # Fallback to any healthy provider
        healthy_providers = self.get_healthy_providers()
        if healthy_providers:
            return self.providers[healthy_providers[0]]
        
        return None
    
    async def health_check_all(self) -> Dict[ProviderType, Dict[str, Any]]:
        """Perform health check on all providers"""
        results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                health_data = await provider.health_check()
                results[provider_type] = health_data
                
                # Update provider health status
                self.provider_health[provider_type] = health_data.get("status") == "healthy"
                
            except Exception as e:
                self.logger.error("Provider health check failed", 
                                provider=provider_type, exc_info=e)
                results[provider_type] = {
                    "provider": provider_type,
                    "status": "unhealthy",
                    "error": str(e)
                }
                self.provider_health[provider_type] = False
        
        return results
    
    def get_provider_limits(self, provider_type: ProviderType) -> Optional[Dict[str, Decimal]]:
        """Get transaction limits for specific provider"""
        provider = self.providers.get(provider_type)
        if provider:
            return provider.get_transaction_limits()
        return None
    
    def get_all_provider_limits(self) -> Dict[ProviderType, Dict[str, Decimal]]:
        """Get transaction limits for all providers"""
        limits = {}
        for provider_type, provider in self.providers.items():
            limits[provider_type] = provider.get_transaction_limits()
        return limits
    
    def mark_provider_unhealthy(self, provider_type: ProviderType, reason: str = ""):
        """Mark a provider as unhealthy"""
        self.provider_health[provider_type] = False
        self.logger.warning("Provider marked unhealthy", 
                          provider=provider_type, reason=reason)
    
    def mark_provider_healthy(self, provider_type: ProviderType):
        """Mark a provider as healthy"""
        self.provider_health[provider_type] = True
        self.logger.info("Provider marked healthy", provider=provider_type)
    
    async def close_all(self):
        """Close all provider connections"""
        for provider_type, provider in self.providers.items():
            try:
                if hasattr(provider, 'client') and provider.client:
                    await provider.client.aclose()
                self.logger.info("Provider connection closed", provider=provider_type)
            except Exception as e:
                self.logger.error("Error closing provider connection", 
                                provider=provider_type, exc_info=e)

# Global provider manager instance (will be initialized in main app)
provider_manager: Optional[ProviderManager] = None

def get_provider_manager() -> ProviderManager:
    """Get the global provider manager instance"""
    if provider_manager is None:
        raise RuntimeError("Provider manager not initialized")
    return provider_manager

def initialize_provider_manager(provider_configs: Dict[str, Dict[str, Any]]) -> ProviderManager:
    """Initialize the global provider manager"""
    global provider_manager
    provider_manager = ProviderManager(provider_configs)
    return provider_manager
