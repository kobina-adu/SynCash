"""
Base provider interface for SyncCash payment providers
Defines the contract that all payment providers must implement
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel
from decimal import Decimal
import structlog

logger = structlog.get_logger(__name__)

class ProviderType(str, Enum):
    """Supported payment provider types"""
    MTN_MOMO = "mtn_momo"
    AIRTELTIGO_MONEY = "airteltigo_money"
    VODAFONE_CASH = "vodafone_cash"

class TransactionStatus(str, Enum):
    """Standard transaction status across all providers"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"

class PaymentRequest(BaseModel):
    """Standardized payment request"""
    amount: Decimal
    currency: str = "GHS"
    phone_number: str
    reference: str
    description: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PaymentResponse(BaseModel):
    """Standardized payment response"""
    provider_transaction_id: str
    status: TransactionStatus
    amount: Decimal
    currency: str
    phone_number: str
    reference: str
    provider_reference: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RefundRequest(BaseModel):
    """Standardized refund request"""
    original_transaction_id: str
    amount: Optional[Decimal] = None  # None means full refund
    reason: Optional[str] = None
    reference: str

class RefundResponse(BaseModel):
    """Standardized refund response"""
    refund_transaction_id: str
    original_transaction_id: str
    status: TransactionStatus
    amount: Decimal
    currency: str
    message: Optional[str] = None

class BalanceResponse(BaseModel):
    """Account balance response"""
    available_balance: Decimal
    currency: str
    account_status: str

class ProviderError(Exception):
    """Base provider error"""
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 provider_response: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.provider_response = provider_response
        super().__init__(message)

class InsufficientFundsError(ProviderError):
    """Insufficient funds error"""
    pass

class InvalidPhoneNumberError(ProviderError):
    """Invalid phone number error"""
    pass

class TransactionNotFoundError(ProviderError):
    """Transaction not found error"""
    pass

class ProviderUnavailableError(ProviderError):
    """Provider service unavailable"""
    pass

class AuthenticationError(ProviderError):
    """Authentication failed"""
    pass

class BasePaymentProvider(ABC):
    """Base class for all payment providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_type = self._get_provider_type()
        self.is_sandbox = config.get("sandbox", True)
        self.logger = structlog.get_logger(f"provider.{self.provider_type}")
    
    @abstractmethod
    def _get_provider_type(self) -> ProviderType:
        """Return the provider type"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the provider API"""
        pass
    
    @abstractmethod
    async def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate a payment transaction"""
        pass
    
    @abstractmethod
    async def check_transaction_status(self, transaction_id: str) -> PaymentResponse:
        """Check the status of a transaction"""
        pass
    
    @abstractmethod
    async def initiate_refund(self, request: RefundRequest) -> RefundResponse:
        """Initiate a refund transaction"""
        pass
    
    @abstractmethod
    async def check_refund_status(self, refund_id: str) -> RefundResponse:
        """Check the status of a refund"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> BalanceResponse:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def validate_phone_number(self, phone_number: str) -> bool:
        """Validate if phone number is supported by this provider"""
        pass
    
    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[PaymentResponse]:
        """Process webhook callback from provider"""
        pass
    
    @abstractmethod
    def map_provider_status(self, provider_status: str) -> TransactionStatus:
        """Map provider-specific status to standard status"""
        pass
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        return ["GHS"]  # Default to Ghana Cedis
    
    def get_transaction_limits(self) -> Dict[str, Decimal]:
        """Get transaction limits for this provider"""
        return {
            "min_amount": Decimal("1.00"),
            "max_amount": Decimal("10000.00"),
            "daily_limit": Decimal("50000.00")
        }
    
    def format_phone_number(self, phone_number: str) -> str:
        """Format phone number for this provider"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone_number))
        
        # Handle Ghana phone numbers
        if phone.startswith('0'):
            phone = '233' + phone[1:]
        elif not phone.startswith('233'):
            phone = '233' + phone
            
        return phone
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform provider health check"""
        try:
            auth_result = await self.authenticate()
            balance_result = await self.get_balance()
            
            return {
                "provider": self.provider_type,
                "status": "healthy",
                "authenticated": auth_result,
                "balance_check": balance_result is not None,
                "sandbox_mode": self.is_sandbox
            }
        except Exception as e:
            self.logger.error("Provider health check failed", exc_info=e)
            return {
                "provider": self.provider_type,
                "status": "unhealthy",
                "error": str(e),
                "sandbox_mode": self.is_sandbox
            }
