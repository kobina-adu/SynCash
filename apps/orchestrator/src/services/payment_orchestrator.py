"""
Payment Orchestrator Service - Core Business Logic
Handles payment workflow orchestration across multiple mobile money providers
"""

import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import time
from decimal import Decimal
import asyncio

from src.models.transaction import (
    Transaction, TransactionStatus, PaymentProvider, 
    TransactionType, TransactionEvent
)
from src.core.database import get_db_session
from src.monitoring.metrics import metrics
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
            
            # Step 3: Call external fraud detection service
            fraud_start_time = time.time()
            risk_level = await self._call_fraud_detection_service(transaction)
            fraud_duration = time.time() - fraud_start_time
            transaction.risk_level = risk_level
            
            # Record fraud detection metrics
            metrics.record_fraud_check(
                risk_level=risk_level,
                service_status="success",
                duration=fraud_duration
            )
            
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
        try:
            async with get_db_session() as session:
                transaction = await session.get(Transaction, uuid.UUID(transaction_id))
                if not transaction:
                    return {"success": False, "error": "Transaction not found"}
                
                return {
                    "success": True,
                    "transaction": transaction.to_dict()
                }
        except Exception as e:
            logger.error("Failed to get transaction status", exc_info=e, transaction_id=transaction_id)
            return {"success": False, "error": "Database error occurred"}
    
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
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if amount < self.settings.min_transaction_amount:
            raise ValueError(f"Amount below minimum: {self.settings.min_transaction_amount}")
        
        if amount > self.settings.max_transaction_amount:
            raise ValueError(f"Amount exceeds maximum: {self.settings.max_transaction_amount}")
        
        if not recipient_phone or not recipient_phone.strip():
            raise ValueError("Recipient phone is required")
        
        # Basic phone number validation
        phone_clean = recipient_phone.replace('+', '').replace('-', '').replace(' ', '')
        if not phone_clean.isdigit() or len(phone_clean) < 10:
            raise ValueError("Invalid phone number format")
    
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
    
    async def _call_fraud_detection_service(self, transaction: Transaction) -> str:
        """Call external fraud detection ML service"""
        try:
            # TODO: Replace with actual fraud detection service API call
            # For now, return LOW risk as default until fraud service is implemented
            fraud_payload = {
                "transaction_id": str(transaction.id),
                "user_id": transaction.user_id,
                "amount": float(transaction.amount),
                "recipient_phone": transaction.recipient_phone,
                "timestamp": transaction.created_at.isoformat(),
                "provider": transaction.provider.value if transaction.provider else None
            }
            
            # This would be an HTTP call to fraud detection microservice
            # response = await httpx.post(f"{FRAUD_SERVICE_URL}/assess", json=fraud_payload)
            # risk_level = response.json()["risk_level"]
            
            logger.info("Fraud detection service call", transaction_id=str(transaction.id), payload=fraud_payload)
            
            # Default to LOW risk until fraud service is integrated
            return "LOW"
            
        except Exception as e:
            logger.error("Fraud detection service call failed", exc_info=e, transaction_id=str(transaction.id))
            # Default to MEDIUM risk if fraud service is unavailable
            return "MEDIUM"
    
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
