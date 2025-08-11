"""
Payment API endpoints for SyncCash Orchestrator
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import structlog

from src.services.payment_orchestrator import PaymentOrchestrator

logger = structlog.get_logger(__name__)
router = APIRouter()

# Pydantic models for request/response validation
class PaymentRequest(BaseModel):
    """Payment initiation request"""
    amount: float = Field(..., gt=0, description="Payment amount in GHS")
    recipient_phone: str = Field(..., min_length=10, max_length=15, description="Recipient phone number")
    recipient_name: str = Field(..., min_length=2, max_length=100, description="Recipient name")
    description: Optional[str] = Field(None, max_length=500, description="Payment description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    user_id: str = Field(..., description="User ID initiating the payment")
    
    @validator('recipient_phone')
    def validate_phone(cls, v):
        # Basic phone validation for Ghana
        if not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, +, -, and spaces')
        return v.strip()
    
    @validator('amount')
    def validate_amount(cls, v):
        if v > 50000:  # Max transaction limit
            raise ValueError('Amount exceeds maximum transaction limit')
        return round(v, 2)

class PaymentResponse(BaseModel):
    """Payment response"""
    success: bool
    transaction_id: Optional[str] = None
    status: Optional[str] = None
    estimated_completion: Optional[str] = None
    error: Optional[str] = None

class TransactionStatusResponse(BaseModel):
    """Transaction status response"""
    success: bool
    transaction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Initialize orchestrator
orchestrator = PaymentOrchestrator()

@router.post("/payments/initiate", response_model=PaymentResponse)
async def initiate_payment(payment_request: PaymentRequest):
    """
    Initiate a new payment transaction
    
    This endpoint starts the payment orchestration process:
    1. Validates the payment request
    2. Performs basic fraud detection
    3. Creates transaction record
    4. Returns transaction details
    """
    try:
        logger.info(
            "Payment initiation request",
            user_id=payment_request.user_id,
            amount=payment_request.amount,
            recipient=payment_request.recipient_phone
        )
        
        # Call orchestrator service
        result = await orchestrator.initiate_payment(
            user_id=payment_request.user_id,
            amount=payment_request.amount,
            recipient_phone=payment_request.recipient_phone,
            recipient_name=payment_request.recipient_name,
            description=payment_request.description,
            metadata=payment_request.metadata
        )
        
        if result["success"]:
            return PaymentResponse(**result)
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Payment initiation failed")
            )
            
    except ValueError as e:
        logger.warning("Payment validation failed", error=str(e), user_id=payment_request.user_id)
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error("Payment initiation error", exc_info=e, user_id=payment_request.user_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/payments/{transaction_id}/status", response_model=TransactionStatusResponse)
async def get_payment_status(transaction_id: str):
    """
    Get current status of a payment transaction
    
    Returns detailed information about the transaction including:
    - Current status
    - Provider information
    - Timestamps
    - Error details (if any)
    """
    try:
        logger.info("Payment status request", transaction_id=transaction_id)
        
        result = await orchestrator.get_transaction_status(transaction_id)
        
        if result["success"]:
            return TransactionStatusResponse(**result)
        else:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Transaction not found")
            )
            
    except Exception as e:
        logger.error("Payment status error", exc_info=e, transaction_id=transaction_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/payments/{transaction_id}/cancel")
async def cancel_payment(transaction_id: str, user_id: str):
    """
    Cancel a pending payment transaction
    
    Only the user who initiated the transaction can cancel it.
    Transactions in final states cannot be cancelled.
    """
    try:
        logger.info("Payment cancellation request", transaction_id=transaction_id, user_id=user_id)
        
        result = await orchestrator.cancel_transaction(transaction_id, user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Cannot cancel transaction")
            )
            
    except Exception as e:
        logger.error("Payment cancellation error", exc_info=e, transaction_id=transaction_id)
        raise HTTPException(status_code=500, detail="Internal server error")
