"""
Refund and Reversal Handling for SyncCash Orchestrator
Manages refund requests, eligibility verification, and reversal processing
"""
import asyncio
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import structlog

from src.models.transaction import Transaction, TransactionStatus, PaymentProvider, TransactionType
from src.core.database import get_db_session
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class RefundReason(Enum):
    """Refund reason codes"""
    USER_REQUEST = "user_request"
    MERCHANT_REFUND = "merchant_refund"
    FRAUD_DETECTED = "fraud_detected"
    SYSTEM_ERROR = "system_error"
    DUPLICATE_PAYMENT = "duplicate_payment"
    CHARGEBACK = "chargeback"

class RefundEligibility(Enum):
    """Refund eligibility status"""
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    PARTIAL_ELIGIBLE = "partial_eligible"
    REQUIRES_APPROVAL = "requires_approval"

class RefundHandler:
    """Handles refund and reversal operations"""
    
    def __init__(self):
        # Refund policy configuration
        self.refund_policy = {
            "max_refund_window_days": 30,
            "auto_refund_threshold": Decimal("1000.00"),  # Auto-approve refunds below this amount
            "partial_refund_allowed": True,
            "refund_fee_percentage": Decimal("0.005"),  # 0.5% refund processing fee
            "min_refund_amount": Decimal("1.00")
        }
        
        # Provider-specific refund capabilities
        self.provider_refund_support = {
            PaymentProvider.MTN_MOMO: {
                "supports_refund": True,
                "max_refund_window_hours": 24,
                "requires_approval": False
            },
            PaymentProvider.AIRTELTIGO: {
                "supports_refund": True,
                "max_refund_window_hours": 48,
                "requires_approval": True
            },
            PaymentProvider.VODAFONE: {
                "supports_refund": True,
                "max_refund_window_hours": 72,
                "requires_approval": False
            }
        }
    
    async def process_refund_request(
        self,
        original_transaction_id: str,
        refund_amount: Optional[Decimal] = None,
        reason: RefundReason = RefundReason.USER_REQUEST,
        requester_id: str = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a refund request for an existing transaction
        """
        try:
            # Get original transaction
            original_transaction = await self._get_transaction(original_transaction_id)
            if not original_transaction:
                return {
                    "success": False,
                    "error": "Original transaction not found",
                    "error_code": "TRANSACTION_NOT_FOUND"
                }
            
            # Determine refund amount
            if refund_amount is None:
                refund_amount = original_transaction.amount
            
            # Check refund eligibility
            eligibility_result = await self._check_refund_eligibility(
                original_transaction, refund_amount, reason
            )
            
            if eligibility_result["status"] != RefundEligibility.ELIGIBLE:
                return {
                    "success": False,
                    "error": eligibility_result["reason"],
                    "eligibility_status": eligibility_result["status"].value,
                    "requires_approval": eligibility_result["status"] == RefundEligibility.REQUIRES_APPROVAL
                }
            
            # Create refund transaction
            refund_transaction = await self._create_refund_transaction(
                original_transaction, refund_amount, reason, requester_id, notes
            )
            
            # Process refund through provider
            refund_result = await self._execute_refund(original_transaction, refund_transaction)
            
            if refund_result["success"]:
                # Update transaction statuses
                await self._update_refund_status(
                    original_transaction, refund_transaction, TransactionStatus.CONFIRMED
                )
                
                logger.info("Refund processed successfully",
                           original_transaction_id=original_transaction_id,
                           refund_transaction_id=str(refund_transaction.id),
                           refund_amount=float(refund_amount),
                           reason=reason.value)
                
                return {
                    "success": True,
                    "refund_transaction_id": str(refund_transaction.id),
                    "refund_amount": float(refund_amount),
                    "status": "confirmed",
                    "processing_time": refund_result.get("processing_time")
                }
            else:
                # Update refund as failed
                await self._update_refund_status(
                    original_transaction, refund_transaction, TransactionStatus.FAILED
                )
                
                return {
                    "success": False,
                    "error": refund_result.get("error", "Refund processing failed"),
                    "refund_transaction_id": str(refund_transaction.id)
                }
                
        except Exception as e:
            logger.error("Refund processing failed", 
                        exc_info=e, 
                        original_transaction_id=original_transaction_id)
            
            metrics.record_error("refund_processing_error", "refund_handler")
            
            return {
                "success": False,
                "error": f"Refund processing failed: {str(e)}",
                "error_code": "PROCESSING_ERROR"
            }
    
    async def _check_refund_eligibility(
        self,
        original_transaction: Transaction,
        refund_amount: Decimal,
        reason: RefundReason
    ) -> Dict[str, Any]:
        """Check if transaction is eligible for refund"""
        
        # Check transaction status
        if original_transaction.status != TransactionStatus.CONFIRMED:
            return {
                "status": RefundEligibility.INELIGIBLE,
                "reason": "Transaction not confirmed"
            }
        
        # Check refund window
        transaction_age = datetime.now() - original_transaction.created_at
        max_window = timedelta(days=self.refund_policy["max_refund_window_days"])
        
        if transaction_age > max_window:
            return {
                "status": RefundEligibility.INELIGIBLE,
                "reason": f"Transaction older than {self.refund_policy['max_refund_window_days']} days"
            }
        
        # Check provider-specific refund window
        provider_config = self.provider_refund_support.get(original_transaction.provider)
        if provider_config:
            provider_window = timedelta(hours=provider_config["max_refund_window_hours"])
            if transaction_age > provider_window:
                return {
                    "status": RefundEligibility.REQUIRES_APPROVAL,
                    "reason": "Outside provider automatic refund window"
                }
        
        # Check refund amount
        if refund_amount > original_transaction.amount:
            return {
                "status": RefundEligibility.INELIGIBLE,
                "reason": "Refund amount exceeds original transaction amount"
            }
        
        if refund_amount < self.refund_policy["min_refund_amount"]:
            return {
                "status": RefundEligibility.INELIGIBLE,
                "reason": f"Refund amount below minimum: {self.refund_policy['min_refund_amount']}"
            }
        
        # Check for existing refunds
        existing_refunds = await self._get_existing_refunds(original_transaction.id)
        total_refunded = sum(r.amount for r in existing_refunds if r.status == TransactionStatus.CONFIRMED)
        
        if total_refunded + refund_amount > original_transaction.amount:
            return {
                "status": RefundEligibility.INELIGIBLE,
                "reason": "Total refund amount would exceed original transaction"
            }
        
        # Check if requires approval based on amount or reason
        if (refund_amount > self.refund_policy["auto_refund_threshold"] or 
            reason in [RefundReason.FRAUD_DETECTED, RefundReason.CHARGEBACK]):
            
            provider_config = self.provider_refund_support.get(original_transaction.provider)
            if provider_config and provider_config["requires_approval"]:
                return {
                    "status": RefundEligibility.REQUIRES_APPROVAL,
                    "reason": "Refund requires manual approval"
                }
        
        return {
            "status": RefundEligibility.ELIGIBLE,
            "reason": "Transaction eligible for refund"
        }
    
    async def _create_refund_transaction(
        self,
        original_transaction: Transaction,
        refund_amount: Decimal,
        reason: RefundReason,
        requester_id: Optional[str],
        notes: Optional[str]
    ) -> Transaction:
        """Create refund transaction record"""
        
        async with get_db_session() as session:
            refund_transaction = Transaction(
                user_id=original_transaction.user_id,
                amount=refund_amount,
                recipient_phone=original_transaction.user_id,  # Refund back to original user
                recipient_name="Refund",
                description=f"Refund for transaction {original_transaction.id}",
                transaction_type=TransactionType.REFUND,
                provider=original_transaction.provider,
                status=TransactionStatus.INITIATED,
                transaction_metadata={
                    "original_transaction_id": str(original_transaction.id),
                    "refund_reason": reason.value,
                    "requester_id": requester_id,
                    "notes": notes,
                    "refund_fee": float(self._calculate_refund_fee(refund_amount))
                }
            )
            
            session.add(refund_transaction)
            await session.commit()
            await session.refresh(refund_transaction)
            
            return refund_transaction
    
    async def _execute_refund(
        self,
        original_transaction: Transaction,
        refund_transaction: Transaction
    ) -> Dict[str, Any]:
        """Execute refund through payment provider"""
        
        try:
            provider = original_transaction.provider
            
            # TODO: Implement actual provider refund API calls
            # For now, simulate refund processing
            
            logger.info("Processing refund with provider",
                       provider=provider.value,
                       original_transaction_id=str(original_transaction.id),
                       refund_transaction_id=str(refund_transaction.id),
                       amount=float(refund_transaction.amount))
            
            # Simulate provider API call
            await asyncio.sleep(2)  # Simulate processing time
            
            # Record provider metrics
            metrics.record_provider_request(
                provider=provider.value,
                status="success",
                duration=2.0
            )
            
            return {
                "success": True,
                "provider_reference": f"REF_{refund_transaction.id}",
                "processing_time": 2.0
            }
            
        except Exception as e:
            logger.error("Provider refund execution failed",
                        exc_info=e,
                        provider=provider.value,
                        refund_transaction_id=str(refund_transaction.id))
            
            metrics.record_provider_request(
                provider=provider.value,
                status="error",
                duration=0
            )
            
            return {
                "success": False,
                "error": f"Provider refund failed: {str(e)}"
            }
    
    async def _update_refund_status(
        self,
        original_transaction: Transaction,
        refund_transaction: Transaction,
        status: TransactionStatus
    ):
        """Update refund transaction status"""
        
        async with get_db_session() as session:
            refund_transaction.status = status
            refund_transaction.updated_at = datetime.now()
            
            # If refund confirmed, update original transaction metadata
            if status == TransactionStatus.CONFIRMED:
                if not original_transaction.transaction_metadata:
                    original_transaction.transaction_metadata = {}
                
                original_transaction.transaction_metadata["refund_status"] = "partial_refunded"
                original_transaction.transaction_metadata["refunded_amount"] = float(refund_transaction.amount)
            
            await session.commit()
    
    async def _get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        async with get_db_session() as session:
            return await session.get(Transaction, transaction_id)
    
    async def _get_existing_refunds(self, original_transaction_id: str) -> List[Transaction]:
        """Get existing refunds for a transaction"""
        async with get_db_session() as session:
            result = await session.execute(
                """
                SELECT * FROM transactions 
                WHERE transaction_metadata->>'original_transaction_id' = :original_id 
                AND transaction_type = 'refund'
                """,
                {"original_id": str(original_transaction_id)}
            )
            return result.fetchall()
    
    def _calculate_refund_fee(self, refund_amount: Decimal) -> Decimal:
        """Calculate refund processing fee"""
        return refund_amount * self.refund_policy["refund_fee_percentage"]
    
    async def get_refund_history(self, transaction_id: str) -> List[Dict[str, Any]]:
        """Get refund history for a transaction"""
        try:
            refunds = await self._get_existing_refunds(transaction_id)
            
            return [
                {
                    "refund_id": str(refund.id),
                    "amount": float(refund.amount),
                    "status": refund.status.value,
                    "reason": refund.transaction_metadata.get("refund_reason"),
                    "created_at": refund.created_at.isoformat(),
                    "requester_id": refund.transaction_metadata.get("requester_id")
                }
                for refund in refunds
            ]
            
        except Exception as e:
            logger.error("Failed to get refund history", exc_info=e)
            return []

# Global refund handler instance
refund_handler = RefundHandler()
