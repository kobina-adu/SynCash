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
from src.services.fraud_detection_service import EnhancedFraudDetectionService

logger = structlog.get_logger(__name__)

class PaymentOrchestrator:
    """
    Core payment orchestration service that manages the entire payment lifecycle
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.metrics = get_metrics_collector()
        # Initialize fraud detection service - MANDATORY for all transactions
        self.fraud_detector = EnhancedFraudDetectionService()
    
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
        Initiate a new payment transaction with MANDATORY fraud detection
        
        This method ensures EVERY transaction goes through:
        1. Input validation
        2. Transaction creation
        3. ML MODEL + RULES FRAUD DETECTION (MANDATORY)
        4. UI response generation for popup display
        5. Provider processing (if safe) or blocking (if fraud)
        
        Returns:
            Dict containing transaction details and UI response for popup display
        """
        # Start metrics tracking
        start_time = time.time()
        
        logger.info(
            "Initiating payment with mandatory fraud detection",
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
            
            # Step 3: MANDATORY FRAUD DETECTION - ML MODEL + RULES
            # This is where your ML model gets integrated!
            logger.info("Running ML model fraud detection", transaction_id=str(transaction.id))
            
            fraud_result = await self.fraud_detector.validate_transaction(transaction)
            
            # Update transaction with fraud detection results
            transaction.fraud_score = fraud_result.risk_score
            transaction.risk_level = fraud_result.risk_level
            transaction.fraud_checked_at = datetime.utcnow()
            transaction.is_fraudulent = fraud_result.is_fraud
            
            # Store detailed fraud detection data
            transaction.fraud_detection_data = {
                "ml_confidence": fraud_result.confidence,
                "reasons": fraud_result.reasons,
                "detection_timestamp": datetime.utcnow().isoformat(),
                "model_version": "anti_fraud_model_pipeline.pkl"
            }
            
            # Record fraud check metrics
            self.metrics.record_fraud_check(fraud_result.risk_level.lower(), "completed", fraud_result.risk_score)
            
            # Step 4: Handle fraud detection result and generate UI response
            if fraud_result.is_fraud:
                # HIGH-RISK OR CRITICAL: Block transaction or require OTP
                self.metrics.record_blocked_transaction("fraud_detected", fraud_result.risk_level)
                
                if fraud_result.risk_level == "CRITICAL":
                    # CRITICAL RISK: Block transaction immediately
                    await self._update_transaction_status(
                        transaction, TransactionStatus.FRAUD_DETECTED, 
                        error_message=f"Transaction blocked due to critical fraud risk: {fraud_result.risk_level}"
                    )
                    
                    logger.warning(
                        "CRITICAL FRAUD DETECTED - Transaction blocked",
                        transaction_id=str(transaction.id),
                        risk_score=fraud_result.risk_score,
                        reasons=fraud_result.reasons
                    )
                    
                    # Return UI response for BLOCKED transaction popup
                    return {
                        "success": False, 
                        "transaction_id": str(transaction.id),
                        "fraud_detected": True,
                        "blocked": True,
                        "ui_response": {
                            "type": "transaction_blocked",
                            "title": "🚫 TRANSACTION BLOCKED",
                            "message": "This transaction has been blocked due to critical security concerns.",
                            "warning_text": "CRITICAL RISK DETECTED",
                            "reasons": fraud_result.reasons,
                            "actions": [
                                {
                                    "text": "Contact Support",
                                    "style": "primary",
                                    "action": "contact_support"
                                },
                                {
                                    "text": "Close",
                                    "style": "secondary",
                                    "action": "close_modal"
                                }
                            ],
                            "color": "red",
                            "show_popup": True,
                            "require_confirmation": True
                        },
                        "risk_level": fraud_result.risk_level,
                        "reasons": fraud_result.reasons
                    }
                else:
                    # HIGH RISK: Allow with OTP verification
                    await self._update_transaction_status(
                        transaction, TransactionStatus.FRAUD_DETECTED, 
                        error_message=f"Transaction flagged for fraud verification: {fraud_result.risk_level} risk"
                    )
                    
                    logger.warning(
                        "HIGH FRAUD RISK - OTP verification required",
                        transaction_id=str(transaction.id),
                        risk_score=fraud_result.risk_score,
                        reasons=fraud_result.reasons
                    )
                    
                    # Return UI response for HIGH-RISK transaction popup (RED WARNING + OTP)
                    return {
                        "success": False, 
                        "transaction_id": str(transaction.id),
                        "fraud_detected": True,
                        "blocked": False,
                        "ui_response": fraud_result.ui_response,  # This contains the red warning popup
                        "risk_level": fraud_result.risk_level,
                        "reasons": fraud_result.reasons
                    }
            
            # Step 5: SAFE TRANSACTION - Proceed with provider processing
            logger.info(
                "Transaction passed fraud detection - proceeding",
                transaction_id=str(transaction.id),
                risk_level=fraud_result.risk_level,
                risk_score=fraud_result.risk_score
            )
            
            # Select provider and process
            provider = PaymentProvider.MTN  # Default provider
            transaction.primary_provider = provider
            
            # Process with provider (simulate or real)
            if self.settings.provider_simulation:
                from src.services.provider_simulation import simulate_provider_payment
                provider_result = await simulate_provider_payment(
                    provider, amount, recipient_phone, {"fraud_cleared": True}
                )
                
                if provider_result['status'] == 'confirmed':
                    await self._update_transaction_status(transaction, TransactionStatus.CONFIRMED)
                    
                    logger.info(
                        "Safe transaction completed successfully", 
                        transaction_id=str(transaction.id),
                        provider_ref=provider_result.get('provider_ref')
                    )
                    
                    # Return SUCCESS with SAFE transaction popup (GREEN PROCEED)
                    return {
                        "success": True,
                        "transaction_id": str(transaction.id),
                        "status": transaction.status.value,
                        "estimated_completion": "2-5 minutes",
                        "provider": provider.value,
                        "provider_reference": provider_result.get('provider_ref'),
                        "ui_response": fraud_result.ui_response,  # This contains the green proceed popup
                        "fraud_check": {
                            "risk_level": fraud_result.risk_level,
                            "risk_score": fraud_result.risk_score,
                            "confidence": fraud_result.confidence,
                            "ml_model_used": True
                        }
                    }
                else:
                    # Provider failed
                    await self._update_transaction_status(
                        transaction, TransactionStatus.FAILED, 
                        error_message=provider_result.get('error')
                    )
                    return {
                        "success": False, 
                        "error": f"Provider processing failed: {provider_result.get('error')}",
                        "transaction_id": str(transaction.id)
                    }
            else:
                # Real provider integration would go here
                logger.warning("Real provider integration not implemented")
                return {"success": False, "error": "Provider integration not available"}
                
        except ValueError as e:
            logger.warning("Payment validation failed", error=str(e), user_id=user_id)
            return {"success": False, "error": str(e)}
        
        except Exception as e:
            logger.error("Payment initiation error", exc_info=e, user_id=user_id)
            
            # Even on system error, return fraud detection error UI
            return {
                "success": False,
                "error": "System error during payment processing",
                "ui_response": {
                    "type": "system_error",
                    "title": "⚠️ SECURITY CHECK REQUIRED",
                    "message": "Unable to verify transaction security. Please try again or contact support.",
                    "warning_text": "CAUTION: Security verification failed",
                    "actions": [
                        {
                            "text": "Retry Transaction",
                            "style": "primary",
                            "action": "retry_transaction"
                        },
                        {
                            "text": "Cancel",
                            "style": "danger",
                            "action": "cancel_transaction"
                        }
                    ],
                    "color": "red",
                    "show_popup": True,
                    "require_confirmation": True
                }
            }
        
        finally:
            # Record processing time
            processing_time = time.time() - start_time
            self.metrics.record_payment_processing_time(processing_time)
    
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
