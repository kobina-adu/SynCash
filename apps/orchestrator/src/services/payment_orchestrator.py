"""
Payment Orchestrator Service - Core Business Logic
Handles payment workflow orchestration across multiple mobile money providers
"""

import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

from src.models.transaction import (
    Transaction, TransactionStatus, PaymentProvider, 
    TransactionType, TransactionEvent
)
from src.core.database import get_db_session
from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

class PaymentOrchestrator:
    """
    Core payment orchestration service that manages the entire payment lifecycle
    """
    
    def __init__(self):
        self.settings = get_settings()
    
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
            
            if risk_level == "CRITICAL":
                await self._update_transaction_status(
                    transaction, TransactionStatus.FAILED, 
                    error_message="Transaction blocked due to high fraud risk"
                )
                return {"success": False, "error": "Transaction blocked", "transaction_id": str(transaction.id)}
            
            # Step 4: Move to pending status
            await self._update_transaction_status(transaction, TransactionStatus.PENDING)
            
            logger.info(
                "Payment initiated successfully",
                transaction_id=str(transaction.id),
                user_id=user_id
            )
            
            return {
                "success": True,
                "transaction_id": str(transaction.id),
                "status": transaction.status.value,
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }
            
        except Exception as e:
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
