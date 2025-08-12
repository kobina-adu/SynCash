"""
Vodafone Cash API client for SyncCash Orchestrator
Implements Vodafone Cash payment processing APIs
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from decimal import Decimal
import httpx
import structlog
from datetime import datetime, timezone
import hashlib
import base64

from .base import (
    BasePaymentProvider, ProviderType, TransactionStatus,
    PaymentRequest, PaymentResponse, RefundRequest, RefundResponse,
    BalanceResponse, ProviderError, InsufficientFundsError,
    InvalidPhoneNumberError, TransactionNotFoundError,
    ProviderUnavailableError, AuthenticationError
)

logger = structlog.get_logger(__name__)

class VodafoneCashProvider(BasePaymentProvider):
    """Vodafone Cash API provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Vodafone Cash API configuration
        self.merchant_id = config.get("merchant_id")
        self.api_username = config.get("api_username")
        self.api_password = config.get("api_password")
        self.api_key = config.get("api_key")
        self.secret_key = config.get("secret_key")
        
        # Environment URLs
        if self.is_sandbox:
            self.base_url = "https://sandbox-api.vodafone.com.gh/v2"
        else:
            self.base_url = "https://api.vodafone.com.gh/v2"
        
        # Authentication session
        self._session_token = None
        self._token_expires_at = None
        
        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_provider_type(self) -> ProviderType:
        return ProviderType.VODAFONE_CASH
    
    async def authenticate(self) -> bool:
        """Authenticate with Vodafone Cash API"""
        try:
            url = f"{self.base_url}/auth/login"
            
            # Create authentication payload
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            auth_string = f"{self.api_username}:{self.api_password}:{timestamp}"
            auth_hash = hashlib.sha256(auth_string.encode()).hexdigest()
            
            payload = {
                "username": self.api_username,
                "timestamp": timestamp,
                "hash": auth_hash,
                "merchant_id": self.merchant_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-API-Key": self.api_key
            }
            
            response = await self.client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self._session_token = data.get("session_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now(timezone.utc).timestamp() + expires_in
                    
                    self.logger.info("Vodafone Cash authentication successful")
                    return True
                else:
                    self.logger.error("Vodafone Cash authentication failed",
                                    message=data.get("message"))
                    return False
            else:
                self.logger.error("Vodafone Cash authentication failed",
                                status_code=response.status_code,
                                response=response.text)
                return False
                
        except Exception as e:
            self.logger.error("Vodafone Cash authentication error", exc_info=e)
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def _ensure_authenticated(self):
        """Ensure we have valid authentication token"""
        current_time = datetime.now(timezone.utc).timestamp()
        
        if (not self._session_token or not self._token_expires_at or 
            current_time >= self._token_expires_at - 300):
            await self.authenticate()
    
    def _generate_request_hash(self, payload: Dict[str, Any], timestamp: str) -> str:
        """Generate request hash for API security"""
        import json
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        hash_string = f"{payload_str}{timestamp}{self.secret_key}"
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate payment collection from customer"""
        await self._ensure_authenticated()
        
        try:
            # Generate unique transaction reference
            transaction_id = str(uuid.uuid4())
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            
            # Format phone number
            phone_number = self.format_phone_number(request.phone_number)
            
            # Validate phone number for Vodafone network
            if not await self.validate_phone_number(phone_number):
                raise InvalidPhoneNumberError(f"Phone number {phone_number} is not on Vodafone network")
            
            # Prepare request payload
            payload = {
                "merchant_id": self.merchant_id,
                "transaction_id": transaction_id,
                "external_reference": request.reference,
                "amount": str(request.amount),
                "currency": request.currency,
                "customer_msisdn": phone_number,
                "description": request.description or f"Payment for {request.reference}",
                "callback_url": request.callback_url,
                "timestamp": timestamp
            }
            
            # Generate request hash
            request_hash = self._generate_request_hash(payload, timestamp)
            
            # API headers
            headers = {
                "Authorization": f"Bearer {self._session_token}",
                "X-API-Key": self.api_key,
                "X-Request-Hash": request_hash,
                "X-Timestamp": timestamp,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Make API call
            url = f"{self.base_url}/payments/collect"
            response = await self.client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    self.logger.info("Vodafone Cash payment initiated",
                                   transaction_id=transaction_id,
                                   reference=request.reference)
                    
                    return PaymentResponse(
                        provider_transaction_id=transaction_id,
                        status=TransactionStatus.PENDING,
                        amount=request.amount,
                        currency=request.currency,
                        phone_number=phone_number,
                        reference=request.reference,
                        provider_reference=data.get("vodafone_reference"),
                        message="Payment initiated successfully"
                    )
                else:
                    error_message = data.get("message", "Payment initiation failed")
                    error_code = data.get("error_code")
                    
                    # Map specific Vodafone errors
                    if error_code == "INSUFFICIENT_BALANCE":
                        raise InsufficientFundsError(error_message)
                    elif error_code == "INVALID_MSISDN":
                        raise InvalidPhoneNumberError(error_message)
                    else:
                        raise ProviderError(error_message)
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                
                self.logger.error("Vodafone Cash payment initiation failed",
                                status_code=response.status_code,
                                error=error_message)
                
                if response.status_code == 401:
                    raise AuthenticationError("Authentication failed")
                else:
                    raise ProviderError(f"Payment initiation failed: {error_message}")
                    
        except (InsufficientFundsError, InvalidPhoneNumberError, ProviderError, AuthenticationError):
            raise
        except Exception as e:
            self.logger.error("Unexpected error in payment initiation", exc_info=e)
            raise ProviderError(f"Payment initiation failed: {str(e)}")
    
    async def check_transaction_status(self, transaction_id: str) -> PaymentResponse:
        """Check payment transaction status"""
        await self._ensure_authenticated()
        
        try:
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            
            # Create query payload for hash generation
            query_payload = {
                "transaction_id": transaction_id,
                "merchant_id": self.merchant_id,
                "timestamp": timestamp
            }
            
            request_hash = self._generate_request_hash(query_payload, timestamp)
            
            headers = {
                "Authorization": f"Bearer {self._session_token}",
                "X-API-Key": self.api_key,
                "X-Request-Hash": request_hash,
                "X-Timestamp": timestamp,
                "Accept": "application/json"
            }
            
            url = f"{self.base_url}/payments/status/{transaction_id}"
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    transaction_data = data.get("transaction", {})
                    
                    # Map Vodafone status to our standard status
                    provider_status = transaction_data.get("status", "PENDING")
                    status = self.map_provider_status(provider_status)
                    
                    return PaymentResponse(
                        provider_transaction_id=transaction_id,
                        status=status,
                        amount=Decimal(transaction_data.get("amount", "0")),
                        currency=transaction_data.get("currency", "GHS"),
                        phone_number=transaction_data.get("customer_msisdn", ""),
                        reference=transaction_data.get("external_reference", ""),
                        provider_reference=transaction_data.get("vodafone_reference"),
                        message=transaction_data.get("status_message")
                    )
                else:
                    error_message = data.get("message", "Status check failed")
                    if "not found" in error_message.lower():
                        raise TransactionNotFoundError(f"Transaction {transaction_id} not found")
                    else:
                        raise ProviderError(error_message)
            elif response.status_code == 404:
                raise TransactionNotFoundError(f"Transaction {transaction_id} not found")
            else:
                error_message = f"Status check failed: HTTP {response.status_code}"
                raise ProviderError(error_message)
                
        except TransactionNotFoundError:
            raise
        except Exception as e:
            self.logger.error("Error checking transaction status",
                            transaction_id=transaction_id, exc_info=e)
            raise ProviderError(f"Status check failed: {str(e)}")
    
    async def initiate_refund(self, request: RefundRequest) -> RefundResponse:
        """Initiate refund transaction"""
        await self._ensure_authenticated()
        
        try:
            # First get original transaction details
            original_tx = await self.check_transaction_status(request.original_transaction_id)
            
            if original_tx.status != TransactionStatus.SUCCESSFUL:
                raise ProviderError("Can only refund successful transactions")
            
            # Generate refund transaction ID
            refund_id = str(uuid.uuid4())
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            
            # Determine refund amount
            refund_amount = request.amount or original_tx.amount
            if refund_amount > original_tx.amount:
                raise ProviderError("Refund amount cannot exceed original transaction amount")
            
            # Prepare refund payload
            payload = {
                "merchant_id": self.merchant_id,
                "refund_id": refund_id,
                "original_transaction_id": request.original_transaction_id,
                "external_reference": request.reference,
                "amount": str(refund_amount),
                "currency": original_tx.currency,
                "reason": request.reason or "Transaction refund",
                "timestamp": timestamp
            }
            
            request_hash = self._generate_request_hash(payload, timestamp)
            
            headers = {
                "Authorization": f"Bearer {self._session_token}",
                "X-API-Key": self.api_key,
                "X-Request-Hash": request_hash,
                "X-Timestamp": timestamp,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            url = f"{self.base_url}/payments/refund"
            response = await self.client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    self.logger.info("Vodafone Cash refund initiated",
                                   refund_id=refund_id,
                                   original_transaction_id=request.original_transaction_id)
                    
                    return RefundResponse(
                        refund_transaction_id=refund_id,
                        original_transaction_id=request.original_transaction_id,
                        status=TransactionStatus.PENDING,
                        amount=refund_amount,
                        currency=original_tx.currency,
                        message="Refund initiated successfully"
                    )
                else:
                    error_message = data.get("message", "Refund initiation failed")
                    raise ProviderError(error_message)
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                raise ProviderError(f"Refund initiation failed: {error_message}")
                
        except ProviderError:
            raise
        except Exception as e:
            self.logger.error("Error initiating refund", exc_info=e)
            raise ProviderError(f"Refund initiation failed: {str(e)}")
    
    async def check_refund_status(self, refund_id: str) -> RefundResponse:
        """Check refund transaction status"""
        await self._ensure_authenticated()
        
        try:
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            
            query_payload = {
                "refund_id": refund_id,
                "merchant_id": self.merchant_id,
                "timestamp": timestamp
            }
            
            request_hash = self._generate_request_hash(query_payload, timestamp)
            
            headers = {
                "Authorization": f"Bearer {self._session_token}",
                "X-API-Key": self.api_key,
                "X-Request-Hash": request_hash,
                "X-Timestamp": timestamp,
                "Accept": "application/json"
            }
            
            url = f"{self.base_url}/payments/refund/status/{refund_id}"
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    refund_data = data.get("refund", {})
                    
                    status = self.map_provider_status(refund_data.get("status", "PENDING"))
                    
                    return RefundResponse(
                        refund_transaction_id=refund_id,
                        original_transaction_id=refund_data.get("original_transaction_id", ""),
                        status=status,
                        amount=Decimal(refund_data.get("amount", "0")),
                        currency=refund_data.get("currency", "GHS"),
                        message=refund_data.get("status_message")
                    )
                else:
                    error_message = data.get("message", "Refund status check failed")
                    if "not found" in error_message.lower():
                        raise TransactionNotFoundError(f"Refund {refund_id} not found")
                    else:
                        raise ProviderError(error_message)
            elif response.status_code == 404:
                raise TransactionNotFoundError(f"Refund {refund_id} not found")
            else:
                raise ProviderError(f"Refund status check failed: HTTP {response.status_code}")
                
        except TransactionNotFoundError:
            raise
        except Exception as e:
            self.logger.error("Error checking refund status", refund_id=refund_id, exc_info=e)
            raise ProviderError(f"Refund status check failed: {str(e)}")
    
    async def get_balance(self) -> BalanceResponse:
        """Get merchant account balance"""
        await self._ensure_authenticated()
        
        try:
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            
            query_payload = {
                "merchant_id": self.merchant_id,
                "timestamp": timestamp
            }
            
            request_hash = self._generate_request_hash(query_payload, timestamp)
            
            headers = {
                "Authorization": f"Bearer {self._session_token}",
                "X-API-Key": self.api_key,
                "X-Request-Hash": request_hash,
                "X-Timestamp": timestamp,
                "Accept": "application/json"
            }
            
            url = f"{self.base_url}/merchant/balance"
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    balance_data = data.get("balance", {})
                    return BalanceResponse(
                        available_balance=Decimal(balance_data.get("available", "0")),
                        currency=balance_data.get("currency", "GHS"),
                        account_status=balance_data.get("status", "active")
                    )
                else:
                    raise ProviderError(data.get("message", "Balance check failed"))
            else:
                raise ProviderError(f"Balance check failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error("Error getting balance", exc_info=e)
            raise ProviderError(f"Balance check failed: {str(e)}")
    
    async def validate_phone_number(self, phone_number: str) -> bool:
        """Validate if phone number is on Vodafone network"""
        # Vodafone Ghana prefixes: 020, 050
        phone = self.format_phone_number(phone_number)
        
        # Remove country code for prefix check
        if phone.startswith("233"):
            phone = phone[3:]
        
        vodafone_prefixes = ["20", "50"]
        return any(phone.startswith(prefix) for prefix in vodafone_prefixes)
    
    def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[PaymentResponse]:
        """Process Vodafone Cash webhook callback"""
        try:
            # Verify webhook signature
            signature = headers.get("X-Request-Hash")
            timestamp = headers.get("X-Timestamp")
            
            if signature and timestamp:
                expected_signature = self._generate_request_hash(payload, timestamp)
                
                if signature != expected_signature:
                    self.logger.warning("Invalid webhook signature")
                    return None
            
            # Process webhook data
            transaction_id = payload.get("transaction_id")
            if not transaction_id:
                return None
            
            status = self.map_provider_status(payload.get("status", "PENDING"))
            
            return PaymentResponse(
                provider_transaction_id=transaction_id,
                status=status,
                amount=Decimal(payload.get("amount", "0")),
                currency=payload.get("currency", "GHS"),
                phone_number=payload.get("customer_msisdn", ""),
                reference=payload.get("external_reference", ""),
                provider_reference=payload.get("vodafone_reference"),
                message=payload.get("status_message")
            )
            
        except Exception as e:
            self.logger.error("Error processing Vodafone webhook", payload=payload, exc_info=e)
            return None
    
    def map_provider_status(self, provider_status: str) -> TransactionStatus:
        """Map Vodafone status to standard transaction status"""
        status_mapping = {
            "PENDING": TransactionStatus.PENDING,
            "PROCESSING": TransactionStatus.PROCESSING,
            "SUCCESS": TransactionStatus.SUCCESSFUL,
            "SUCCESSFUL": TransactionStatus.SUCCESSFUL,
            "COMPLETED": TransactionStatus.SUCCESSFUL,
            "FAILED": TransactionStatus.FAILED,
            "ERROR": TransactionStatus.FAILED,
            "TIMEOUT": TransactionStatus.EXPIRED,
            "EXPIRED": TransactionStatus.EXPIRED,
            "CANCELLED": TransactionStatus.CANCELLED,
            "REFUNDED": TransactionStatus.REFUNDED
        }
        
        return status_mapping.get(provider_status.upper(), TransactionStatus.PENDING)
    
    def get_transaction_limits(self) -> Dict[str, Decimal]:
        """Get Vodafone Cash transaction limits"""
        if self.is_sandbox:
            return {
                "min_amount": Decimal("1.00"),
                "max_amount": Decimal("1000.00"),
                "daily_limit": Decimal("3000.00")
            }
        else:
            return {
                "min_amount": Decimal("1.00"),
                "max_amount": Decimal("6000.00"),
                "daily_limit": Decimal("30000.00")
            }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()
