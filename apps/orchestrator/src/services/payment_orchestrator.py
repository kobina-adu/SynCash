"""
Payment Orchestrator Service - Core Business Logic
Handles payment workflow orchestration across multiple mobile money providers
"""

import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import time

from src.models.transaction import (
    Transaction, TransactionStatus, PaymentProvider, 
    TransactionType, TransactionEvent
)
from src.core.database import get_db_session
from src.config.settings import get_settings
from src.core.metrics import get_metrics_collector

logger = structlog.get_logger(__name__)

class PaymentOrchestrator:
    """
    Core payment orchestration service that manages the entire payment lifecycle
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.metrics = get_metrics_collector()
    
    async def initiate_payment(
        self,
        user_id: str,
        amount: float,
        recipient_phone: str,
        recipient_name: str,
        description: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Initiate a new payment transaction
        
        Args:
            user_id: User initiating the payment
            amount: Payment amount
            recipient_phone: Recipient phone number
            recipient_name: Recipient name
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            Transaction details
        """
        # Start metrics tracking
        start_time = time.time()
        
        logger.info(
            "Initiating payment",
            user_id=user_id,
            amount=amount,
            recipient_phone=recipient_phone
        )
        
        try:
            # Step 1: Validate input parameters
            await self._validate_payment_request(user_id, amount, recipient_phone)
            
            # Step 2: Create transaction record
            transaction = await self._create_transaction(
                user_id=user_id,
                amount=amount,
                recipient_phone=recipient_phone,
                recipient_name=recipient_name,
                description=description,
                metadata=metadata or {}
            )
            
            # Step 3: Basic fraud check (simplified for now)
            risk_level = await self._basic_fraud_check(transaction)
            transaction.risk_level = risk_level
            
            # Record fraud check metrics
            self.metrics.record_fraud_check(risk_level, "completed", transaction.fraud_score)
            
            if risk_level == "CRITICAL":
                self.metrics.record_blocked_transaction("fraud_risk", risk_level)
                await self._update_transaction_status(
                    transaction, TransactionStatus.FAILED, 
                    error_message="Transaction blocked due to high fraud risk"
                )
                return {"success": False, "error": "Transaction blocked", "transaction_id": str(transaction.id)}
            
            # Step 4: Select provider (for now, pick MTN for demo; can randomize or use logic)
            from src.models.transaction import PaymentProvider
            provider = PaymentProvider.MTN
            transaction.primary_provider = provider

            # Step 5: Provider call (simulate or real)
            provider_result = None
            from src.services.provider_simulation import simulate_provider_payment
            if self.settings.provider_simulation:
                try:
                    provider_result = await simulate_provider_payment(provider, amount, recipient_phone, metadata)
                    if provider_result['status'] == 'confirmed':
                        await self._update_transaction_status(transaction, TransactionStatus.CONFIRMED)
                        logger.info("Simulated provider success", provider=provider.value, ref=provider_result['provider_ref'])
                        self.metrics.record_provider_api_call(provider.value, "success")
                        return {
                            "success": True,
                            "transaction_id": str(transaction.id),
                            "status": TransactionStatus.CONFIRMED.value,
                            "provider_ref": provider_result['provider_ref'],
                            "message": provider_result['message']
                        }
                    elif provider_result['status'] == 'failed':
                        await self._update_transaction_status(transaction, TransactionStatus.FAILED, error_message=provider_result['error'])
                        logger.warning("Simulated provider failure", provider=provider.value, error=provider_result['error'])
                        self.metrics.record_provider_api_call(provider.value, "failed")
                        return {
                            "success": False,
                            "transaction_id": str(transaction.id),
                            "status": TransactionStatus.FAILED.value,
                            "error": provider_result['error']
                        }
                except Exception as e:
                    # Simulated timeout or error
                    await self._update_transaction_status(transaction, TransactionStatus.PENDING, error_message=str(e))
                    logger.error("Simulated provider timeout/error", provider=provider.value, error=str(e))
                    self.metrics.record_provider_api_call(provider.value, "timeout")
                    return {
                        "success": False,
                        "transaction_id": str(transaction.id),
                        "status": TransactionStatus.PENDING.value,
                        "error": str(e)
                    }
            else:
                # Placeholder for real provider integration
                # TODO: Integrate with real provider APIs when ready
                await self._update_transaction_status(transaction, TransactionStatus.PENDING)
                logger.info("Real provider integration not yet implemented", provider=provider.value)
                return {
                    "success": True,
                    "transaction_id": str(transaction.id),
                    "status": TransactionStatus.PENDING.value,
                    "message": "Real provider integration coming soon."
                }

            # Fallback (should not reach here)
            return {
                "success": False,
                "transaction_id": str(transaction.id),
                "status": transaction.status.value,
                "error": "Unknown provider outcome"
            }

            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            self.metrics.record_payment_duration(duration, "failed", "unknown", "unknown")
            self.metrics.record_application_error(type(e).__name__, "payment_orchestrator", "error")
            
            logger.error("Payment initiation failed", exc_info=e, user_id=user_id)
            return {"success": False, "error": str(e)}
    
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get current transaction status"""
        async with get_db_session() as session:
            transaction = await session.get(Transaction, uuid.UUID(transaction_id))
            if not transaction:
                return {"success": False, "error": "Transaction not found"}
            
            return {
                "success": True,
                "transaction": transaction.to_dict()
            }
    
    async def cancel_transaction(self, transaction_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel a pending transaction"""
        async with get_db_session() as session:
            transaction = await session.get(Transaction, uuid.UUID(transaction_id))
            if not transaction:
                return {"success": False, "error": "Transaction not found"}
            
            if transaction.user_id != user_id:
                return {"success": False, "error": "Unauthorized"}
            
            if transaction.is_final_state:
                return {"success": False, "error": "Transaction cannot be cancelled"}
            
            await self._update_transaction_status(
                transaction, TransactionStatus.CANCELLED,
                updated_by=user_id
            )
            
            return {"success": True, "status": "cancelled"}
    
    async def _validate_payment_request(self, user_id: str, amount: float, recipient_phone: str):
        """Validate payment request parameters"""
        if not user_id:
            raise ValueError("User ID is required")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if amount < self.settings.min_transaction_amount:
            raise ValueError(f"Amount below minimum: {self.settings.min_transaction_amount}")
        
        if amount > self.settings.max_transaction_amount:
            raise ValueError(f"Amount exceeds maximum: {self.settings.max_transaction_amount}")
        
        if not recipient_phone:
            raise ValueError("Recipient phone is required")
    
    async def _create_transaction(self, **kwargs) -> Transaction:
        """Create a new transaction record"""
        transaction = Transaction(
            external_reference=f"TXN_{uuid.uuid4().hex[:12].upper()}",
            expires_at=datetime.utcnow() + timedelta(seconds=self.settings.transaction_timeout_seconds),
            **kwargs
        )
        
        async with get_db_session() as session:
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
        
        return transaction
    
    async def _basic_fraud_check(self, transaction: Transaction) -> str:
        """Basic fraud detection (simplified)"""
        # Simple rules-based fraud detection
        risk_score = 0.0
        
        # Large amount check
        if transaction.amount > self.settings.suspicious_amount_threshold:
            risk_score += 0.5
        
        # Very large amounts
        if transaction.amount > self.settings.suspicious_amount_threshold * 2:
            risk_score += 0.3
        
        # Determine risk level
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.3:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _update_transaction_status(
        self, 
        transaction: Transaction, 
        new_status: TransactionStatus,
        error_message: str = None,
        updated_by: str = None
    ):
        """Update transaction status and log event"""
        old_status = transaction.status
        transaction.status = new_status
        transaction.updated_at = datetime.utcnow()
        
        if updated_by:
            transaction.updated_by = updated_by
        
        # Record status change metrics
        self.metrics.record_status_change(
            old_status.value if old_status else "none",
            new_status.value,
            transaction.primary_provider.value if transaction.primary_provider else "unknown"
        )
        
        # Create event log
        event = TransactionEvent(
            transaction_id=transaction.id,
            event_type="status_change",
            from_status=old_status,
            to_status=new_status,
            error_message=error_message,
            created_by=updated_by
        )
        
        async with get_db_session() as session:
            session.add(event)
            await session.commit()
        
        logger.info(
            "Transaction status updated",
            transaction_id=str(transaction.id),
            from_status=old_status.value if old_status else None,
            to_status=new_status.value,
            error_message=error_message
        )
