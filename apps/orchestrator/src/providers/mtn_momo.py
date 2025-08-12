"""
MTN Mobile Money API client for SyncCash Orchestrator
Implements MTN MoMo Collection and Disbursement APIs
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from decimal import Decimal
import httpx
import structlog
from datetime import datetime, timezone

from .base import (
    BasePaymentProvider, ProviderType, TransactionStatus,
    PaymentRequest, PaymentResponse, RefundRequest, RefundResponse,
    BalanceResponse, ProviderError, InsufficientFundsError,
    InvalidPhoneNumberError, TransactionNotFoundError,
    ProviderUnavailableError, AuthenticationError
)

logger = structlog.get_logger(__name__)

class MTNMoMoProvider(BasePaymentProvider):
    """MTN Mobile Money API provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # MTN MoMo API configuration
        self.subscription_key = config.get("subscription_key")
        self.user_id = config.get("user_id")
        self.api_key = config.get("api_key")
        self.collection_user_id = config.get("collection_user_id")
        self.disbursement_user_id = config.get("disbursement_user_id")
        
        # Environment URLs
        if self.is_sandbox:
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
        else:
            self.base_url = "https://momodeveloper.mtn.com"
        
        # API endpoints
        self.collection_base = f"{self.base_url}/collection"
        self.disbursement_base = f"{self.base_url}/disbursement"
        
        # Authentication tokens
        self._collection_token = None
        self._disbursement_token = None
        self._token_expires_at = None
        
        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_provider_type(self) -> ProviderType:
        return ProviderType.MTN_MOMO
    
    async def authenticate(self) -> bool:
        """Authenticate with MTN MoMo API and get access tokens"""
        try:
            # Get collection token
            collection_token = await self._get_access_token("collection")
            
            # Get disbursement token  
            disbursement_token = await self._get_access_token("disbursement")
            
            if collection_token and disbursement_token:
                self._collection_token = collection_token
                self._disbursement_token = disbursement_token
                self._token_expires_at = datetime.now(timezone.utc).timestamp() + 3600  # 1 hour
                
                self.logger.info("MTN MoMo authentication successful")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("MTN MoMo authentication failed", exc_info=e)
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def _get_access_token(self, product: str) -> Optional[str]:
        """Get access token for specific product (collection/disbursement)"""
        try:
            url = f"{self.base_url}/{product}/token/"
            
            headers = {
                "Authorization": f"Basic {self._get_basic_auth()}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "Content-Type": "application/json"
            }
            
            response = await self.client.post(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                self.logger.error(f"Failed to get {product} token", 
                                status_code=response.status_code,
                                response=response.text)
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting {product} token", exc_info=e)
            return None
    
    def _get_basic_auth(self) -> str:
        """Get basic auth string for token requests"""
        import base64
        auth_string = f"{self.user_id}:{self.api_key}"
        return base64.b64encode(auth_string.encode()).decode()
    
    async def _ensure_authenticated(self, product: str = "collection"):
        """Ensure we have valid authentication tokens"""
        current_time = datetime.now(timezone.utc).timestamp()
        
        if (not self._collection_token or not self._disbursement_token or 
            not self._token_expires_at or current_time >= self._token_expires_at - 300):
            await self.authenticate()
    
    async def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate payment collection from customer"""
        await self._ensure_authenticated("collection")
        
        try:
            # Generate unique transaction reference
            transaction_id = str(uuid.uuid4())
            
            # Format phone number
            phone_number = self.format_phone_number(request.phone_number)
            
            # Validate phone number for MTN network
            if not await self.validate_phone_number(phone_number):
                raise InvalidPhoneNumberError(f"Phone number {phone_number} is not on MTN network")
            
            # Prepare request payload
            payload = {
                "amount": str(request.amount),
                "currency": request.currency,
                "externalId": request.reference,
                "payer": {
                    "partyIdType": "MSISDN",
                    "partyId": phone_number
                },
                "payerMessage": request.description or f"Payment for {request.reference}",
                "payeeNote": f"SyncCash payment {request.reference}"
            }
            
            # API headers
            headers = {
                "Authorization": f"Bearer {self._collection_token}",
                "X-Reference-Id": transaction_id,
                "X-Target-Environment": "sandbox" if self.is_sandbox else "live",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "Content-Type": "application/json"
            }
            
            # Make API call
            url = f"{self.collection_base}/v1_0/requesttopay"
            response = await self.client.post(url, json=payload, headers=headers)
            
            if response.status_code == 202:
                # Payment initiated successfully
                self.logger.info("MTN MoMo payment initiated", 
                               transaction_id=transaction_id,
                               reference=request.reference)
                
                return PaymentResponse(
                    provider_transaction_id=transaction_id,
                    status=TransactionStatus.PENDING,
                    amount=request.amount,
                    currency=request.currency,
                    phone_number=phone_number,
                    reference=request.reference,
                    message="Payment initiated successfully"
                )
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                
                self.logger.error("MTN MoMo payment initiation failed",
                                status_code=response.status_code,
                                error=error_message)
                
                # Map specific MTN errors
                if response.status_code == 400:
                    if "insufficient" in error_message.lower():
                        raise InsufficientFundsError(error_message)
                    else:
                        raise ProviderError(f"Invalid request: {error_message}")
                elif response.status_code == 409:
                    raise ProviderError(f"Duplicate transaction: {error_message}")
                else:
                    raise ProviderError(f"Payment initiation failed: {error_message}")
                    
        except (InsufficientFundsError, InvalidPhoneNumberError, ProviderError):
            raise
        except Exception as e:
            self.logger.error("Unexpected error in payment initiation", exc_info=e)
            raise ProviderError(f"Payment initiation failed: {str(e)}")
    
    async def check_transaction_status(self, transaction_id: str) -> PaymentResponse:
        """Check payment transaction status"""
        await self._ensure_authenticated("collection")
        
        try:
            headers = {
                "Authorization": f"Bearer {self._collection_token}",
                "X-Target-Environment": "sandbox" if self.is_sandbox else "live",
                "Ocp-Apim-Subscription-Key": self.subscription_key
            }
            
            url = f"{self.collection_base}/v1_0/requesttopay/{transaction_id}"
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Map MTN status to our standard status
                mtn_status = data.get("status", "PENDING")
                status = self.map_provider_status(mtn_status)
                
                return PaymentResponse(
                    provider_transaction_id=transaction_id,
                    status=status,
                    amount=Decimal(data.get("amount", "0")),
                    currency=data.get("currency", "GHS"),
                    phone_number=data.get("payer", {}).get("partyId", ""),
                    reference=data.get("externalId", ""),
                    provider_reference=data.get("financialTransactionId"),
                    message=data.get("reason", {}).get("message") if data.get("reason") else None
                )
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
        """Initiate refund via disbursement"""
        await self._ensure_authenticated("disbursement")
        
        try:
            # First get original transaction details
            original_tx = await self.check_transaction_status(request.original_transaction_id)
            
            if original_tx.status != TransactionStatus.SUCCESSFUL:
                raise ProviderError("Can only refund successful transactions")
            
            # Generate refund transaction ID
            refund_id = str(uuid.uuid4())
            
            # Determine refund amount
            refund_amount = request.amount or original_tx.amount
            if refund_amount > original_tx.amount:
                raise ProviderError("Refund amount cannot exceed original transaction amount")
            
            # Prepare disbursement payload
            payload = {
                "amount": str(refund_amount),
                "currency": original_tx.currency,
                "externalId": request.reference,
                "payee": {
                    "partyIdType": "MSISDN",
                    "partyId": original_tx.phone_number
                },
                "payerMessage": f"Refund for transaction {request.original_transaction_id}",
                "payeeNote": request.reason or "Transaction refund"
            }
            
            headers = {
                "Authorization": f"Bearer {self._disbursement_token}",
                "X-Reference-Id": refund_id,
                "X-Target-Environment": "sandbox" if self.is_sandbox else "live",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "Content-Type": "application/json"
            }
            
            url = f"{self.disbursement_base}/v1_0/transfer"
            response = await self.client.post(url, json=payload, headers=headers)
            
            if response.status_code == 202:
                self.logger.info("MTN MoMo refund initiated",
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
        await self._ensure_authenticated("disbursement")
        
        try:
            headers = {
                "Authorization": f"Bearer {self._disbursement_token}",
                "X-Target-Environment": "sandbox" if self.is_sandbox else "live",
                "Ocp-Apim-Subscription-Key": self.subscription_key
            }
            
            url = f"{self.disbursement_base}/v1_0/transfer/{refund_id}"
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                status = self.map_provider_status(data.get("status", "PENDING"))
                
                return RefundResponse(
                    refund_transaction_id=refund_id,
                    original_transaction_id=data.get("externalId", ""),
                    status=status,
                    amount=Decimal(data.get("amount", "0")),
                    currency=data.get("currency", "GHS"),
                    message=data.get("reason", {}).get("message") if data.get("reason") else None
                )
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
        """Get account balance"""
        await self._ensure_authenticated("collection")
        
        try:
            headers = {
                "Authorization": f"Bearer {self._collection_token}",
                "X-Target-Environment": "sandbox" if self.is_sandbox else "live",
                "Ocp-Apim-Subscription-Key": self.subscription_key
            }
            
            url = f"{self.collection_base}/v1_0/account/balance"
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return BalanceResponse(
                    available_balance=Decimal(data.get("availableBalance", "0")),
                    currency=data.get("currency", "GHS"),
                    account_status="active"
                )
            else:
                raise ProviderError(f"Balance check failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error("Error getting balance", exc_info=e)
            raise ProviderError(f"Balance check failed: {str(e)}")
    
    async def validate_phone_number(self, phone_number: str) -> bool:
        """Validate if phone number is on MTN network"""
        # MTN Ghana prefixes: 024, 054, 055, 059
        phone = self.format_phone_number(phone_number)
        
        # Remove country code for prefix check
        if phone.startswith("233"):
            phone = phone[3:]
        
        mtn_prefixes = ["24", "54", "55", "59"]
        return any(phone.startswith(prefix) for prefix in mtn_prefixes)
    
    def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[PaymentResponse]:
        """Process MTN MoMo webhook callback"""
        try:
            # MTN sends webhooks for transaction status updates
            transaction_id = payload.get("referenceId")
            if not transaction_id:
                return None
            
            # Map webhook data to our response format
            status = self.map_provider_status(payload.get("status", "PENDING"))
            
            return PaymentResponse(
                provider_transaction_id=transaction_id,
                status=status,
                amount=Decimal(payload.get("amount", "0")),
                currency=payload.get("currency", "GHS"),
                phone_number=payload.get("payer", {}).get("partyId", ""),
                reference=payload.get("externalId", ""),
                provider_reference=payload.get("financialTransactionId"),
                message=payload.get("reason", {}).get("message") if payload.get("reason") else None
            )
            
        except Exception as e:
            self.logger.error("Error processing MTN webhook", payload=payload, exc_info=e)
            return None
    
    def map_provider_status(self, provider_status: str) -> TransactionStatus:
        """Map MTN MoMo status to standard transaction status"""
        status_mapping = {
            "PENDING": TransactionStatus.PENDING,
            "SUCCESSFUL": TransactionStatus.SUCCESSFUL,
            "FAILED": TransactionStatus.FAILED,
            "TIMEOUT": TransactionStatus.EXPIRED,
            "CANCELLED": TransactionStatus.CANCELLED
        }
        
        return status_mapping.get(provider_status.upper(), TransactionStatus.PENDING)
    
    def get_transaction_limits(self) -> Dict[str, Decimal]:
        """Get MTN MoMo transaction limits"""
        if self.is_sandbox:
            return {
                "min_amount": Decimal("1.00"),
                "max_amount": Decimal("1000.00"),
                "daily_limit": Decimal("5000.00")
            }
        else:
            return {
                "min_amount": Decimal("1.00"),
                "max_amount": Decimal("10000.00"),
                "daily_limit": Decimal("50000.00")
            }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()
