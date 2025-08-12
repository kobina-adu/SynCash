"""
Webhook handlers for payment provider callbacks
Processes status updates from MTN MoMo, AirtelTigo, and Vodafone Cash
"""
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
import structlog

from .factory import get_provider_manager
from .base import ProviderType, PaymentResponse
from src.services.payment_orchestrator import payment_orchestrator

logger = structlog.get_logger(__name__)

class WebhookProcessor:
    """Processes webhooks from payment providers"""
    
    def __init__(self):
        self.logger = structlog.get_logger("webhook_processor")
    
    async def process_mtn_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Process MTN MoMo webhook"""
        try:
            provider_manager = get_provider_manager()
            mtn_provider = provider_manager.get_provider(ProviderType.MTN_MOMO)
            
            if not mtn_provider:
                self.logger.error("MTN provider not available for webhook processing")
                return False
            
            # Process webhook with provider
            payment_response = mtn_provider.process_webhook(payload, headers)
            
            if payment_response:
                # Update transaction in our system
                await self._update_transaction_status(payment_response)
                
                self.logger.info("MTN webhook processed successfully",
                               transaction_id=payment_response.provider_transaction_id,
                               status=payment_response.status)
                return True
            else:
                self.logger.warning("MTN webhook processing returned no response")
                return False
                
        except Exception as e:
            self.logger.error("Error processing MTN webhook", payload=payload, exc_info=e)
            return False
    
    async def process_airteltigo_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Process AirtelTigo Money webhook"""
        try:
            provider_manager = get_provider_manager()
            airteltigo_provider = provider_manager.get_provider(ProviderType.AIRTELTIGO_MONEY)
            
            if not airteltigo_provider:
                self.logger.error("AirtelTigo provider not available for webhook processing")
                return False
            
            # Process webhook with provider
            payment_response = airteltigo_provider.process_webhook(payload, headers)
            
            if payment_response:
                # Update transaction in our system
                await self._update_transaction_status(payment_response)
                
                self.logger.info("AirtelTigo webhook processed successfully",
                               transaction_id=payment_response.provider_transaction_id,
                               status=payment_response.status)
                return True
            else:
                self.logger.warning("AirtelTigo webhook processing returned no response")
                return False
                
        except Exception as e:
            self.logger.error("Error processing AirtelTigo webhook", payload=payload, exc_info=e)
            return False
    
    async def process_vodafone_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Process Vodafone Cash webhook"""
        try:
            provider_manager = get_provider_manager()
            vodafone_provider = provider_manager.get_provider(ProviderType.VODAFONE_CASH)
            
            if not vodafone_provider:
                self.logger.error("Vodafone provider not available for webhook processing")
                return False
            
            # Process webhook with provider
            payment_response = vodafone_provider.process_webhook(payload, headers)
            
            if payment_response:
                # Update transaction in our system
                await self._update_transaction_status(payment_response)
                
                self.logger.info("Vodafone webhook processed successfully",
                               transaction_id=payment_response.provider_transaction_id,
                               status=payment_response.status)
                return True
            else:
                self.logger.warning("Vodafone webhook processing returned no response")
                return False
                
        except Exception as e:
            self.logger.error("Error processing Vodafone webhook", payload=payload, exc_info=e)
            return False
    
    async def _update_transaction_status(self, payment_response: PaymentResponse):
        """Update transaction status in our database"""
        try:
            # Find transaction by provider transaction ID
            from src.core.database import get_db_session
            from src.models.transaction import Transaction
            
            async with get_db_session() as session:
                # Query transaction by provider transaction ID
                from sqlalchemy import select
                stmt = select(Transaction).where(
                    Transaction.provider_transaction_id == payment_response.provider_transaction_id
                )
                result = await session.execute(stmt)
                transaction = result.scalar_one_or_none()
                
                if transaction:
                    # Update transaction status
                    transaction.status = payment_response.status.value
                    transaction.provider_reference = payment_response.provider_reference
                    transaction.status_message = payment_response.message
                    
                    # Update metadata if available
                    if payment_response.metadata:
                        if transaction.metadata:
                            transaction.metadata.update(payment_response.metadata)
                        else:
                            transaction.metadata = payment_response.metadata
                    
                    await session.commit()
                    
                    self.logger.info("Transaction status updated from webhook",
                                   transaction_id=transaction.id,
                                   provider_transaction_id=payment_response.provider_transaction_id,
                                   status=payment_response.status)
                    
                    # Trigger any post-processing (notifications, etc.)
                    await self._post_process_status_update(transaction, payment_response)
                else:
                    self.logger.warning("Transaction not found for webhook update",
                                      provider_transaction_id=payment_response.provider_transaction_id)
                    
        except Exception as e:
            self.logger.error("Error updating transaction status from webhook",
                            provider_transaction_id=payment_response.provider_transaction_id,
                            exc_info=e)
    
    async def _post_process_status_update(self, transaction, payment_response: PaymentResponse):
        """Post-process status update (notifications, events, etc.)"""
        try:
            # Emit transaction status update event
            from src.services.event_emitter import event_emitter
            
            await event_emitter.emit_transaction_status_update(
                transaction_id=transaction.id,
                status=payment_response.status.value,
                provider=transaction.provider,
                amount=float(payment_response.amount),
                currency=payment_response.currency
            )
            
            # Handle specific status updates
            if payment_response.status.value == "successful":
                await self._handle_successful_payment(transaction, payment_response)
            elif payment_response.status.value == "failed":
                await self._handle_failed_payment(transaction, payment_response)
                
        except Exception as e:
            self.logger.error("Error in post-processing status update",
                            transaction_id=transaction.id, exc_info=e)
    
    async def _handle_successful_payment(self, transaction, payment_response: PaymentResponse):
        """Handle successful payment completion"""
        try:
            self.logger.info("Payment completed successfully",
                           transaction_id=transaction.id,
                           amount=payment_response.amount,
                           provider=transaction.provider)
            
            # Could trigger:
            # - Customer notification
            # - Merchant settlement
            # - Analytics update
            # - Loyalty points award
            
        except Exception as e:
            self.logger.error("Error handling successful payment",
                            transaction_id=transaction.id, exc_info=e)
    
    async def _handle_failed_payment(self, transaction, payment_response: PaymentResponse):
        """Handle failed payment"""
        try:
            self.logger.warning("Payment failed",
                              transaction_id=transaction.id,
                              reason=payment_response.message,
                              provider=transaction.provider)
            
            # Could trigger:
            # - Customer notification
            # - Retry logic (if appropriate)
            # - Fraud analysis
            # - Support ticket creation
            
        except Exception as e:
            self.logger.error("Error handling failed payment",
                            transaction_id=transaction.id, exc_info=e)

# Global webhook processor instance
webhook_processor = WebhookProcessor()
