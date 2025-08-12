"""
Payment API endpoints for SyncCash Orchestrator
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import structlog

from src.services.payment_orchestrator import PaymentOrchestrator
from src.middleware.auth import (
    get_current_user, get_verified_user, require_permissions, 
    require_mfa_for_amount, Permissions, RequireMFAForLargePayments
)

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

class RefundRequest(BaseModel):
    """Refund request"""
    reason: str = Field(..., min_length=5, max_length=500, description="Reason for refund")
    amount: Optional[float] = Field(None, gt=0, description="Partial refund amount (optional)")
    
class RefundResponse(BaseModel):
    """Refund response"""
    success: bool
    refund_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None

# Initialize orchestrator
orchestrator = PaymentOrchestrator()

@router.post("/payments/initiate", response_model=PaymentResponse)
async def initiate_payment(
    request: PaymentRequest,
    current_user: Dict[str, Any] = Depends(RequireMFAForLargePayments)
):
    """
    Initiate a new payment transaction
    
    This endpoint creates a new payment transaction and begins the orchestration process.
    The payment will be validated, risk-assessed, and routed to the appropriate provider.
    
    Returns:
    - transaction_id: Unique identifier for tracking
    - status: Current transaction status
    - estimated_completion: Expected completion time
    """
    try:
        user_id = current_user["user_id"]
        
        logger.info("Payment initiation request", 
                   amount=request.amount, 
                   user_id=user_id,
                   recipient=request.recipient_phone[:4] + "****")
        
        result = await orchestrator.initiate_payment(
            user_id=user_id,
            amount=request.amount,
            recipient_phone=request.recipient_phone,
            recipient_name=request.recipient_name,
            description=request.description,
            metadata=request.metadata
        )
        
        if result["success"]:
            return PaymentResponse(**result)
        else:
            error_msg = result.get("error", "Payment initiation failed")
            # Check if it's a validation error
            if "Amount" in error_msg or "positive" in error_msg or "minimum" in error_msg or "maximum" in error_msg:
                raise HTTPException(status_code=400, detail=error_msg)
            elif "phone" in error_msg.lower() or "format" in error_msg.lower():
                raise HTTPException(status_code=400, detail=error_msg)
            else:
                raise HTTPException(status_code=422, detail=error_msg)
            
    except HTTPException:
        raise
    except ValueError as e:
        # Validation errors should return 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Payment initiation error", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/payments/{transaction_id}/status", response_model=TransactionStatusResponse)
async def get_payment_status(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(require_permissions(Permissions.PAYMENT_STATUS))
):
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
        
        # Validate UUID format
        try:
            import uuid
            uuid.UUID(transaction_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid transaction ID format"
            )
        
        result = await orchestrator.get_transaction_status(transaction_id)
        
        if result["success"]:
            return TransactionStatusResponse(**result)
        else:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Transaction not found")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Payment status error", exc_info=e, transaction_id=transaction_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/payments/{transaction_id}/cancel")
async def cancel_payment(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_verified_user)
):
    """
    Cancel a pending payment transaction
    
    Only the user who initiated the transaction can cancel it.
    Transactions in final states cannot be cancelled.
    """
    try:
        user_id = current_user["user_id"]
        
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

@router.post("/payments/{transaction_id}/refund", response_model=RefundResponse)
async def refund_payment(
    transaction_id: str,
    request: RefundRequest,
    current_user: Dict[str, Any] = Depends(require_permissions(Permissions.PAYMENT_REFUND))
):
    """
    Initiate a refund for a completed payment transaction
    
    Requires PAYMENT_REFUND permission. Only completed transactions can be refunded.
    Supports both full and partial refunds.
    """
    try:
        user_id = current_user["user_id"]
        
        logger.info("Refund request initiated", 
                   transaction_id=transaction_id,
                   user_id=user_id,
                   reason=request.reason[:50] + "..." if len(request.reason) > 50 else request.reason)
        
        # Validate UUID format
        try:
            import uuid
            uuid.UUID(transaction_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid transaction ID format"
            )
        
        result = await orchestrator.initiate_refund(
            transaction_id=transaction_id,
            user_id=user_id,
            reason=request.reason,
            amount=request.amount
        )
        
        if result["success"]:
            return RefundResponse(**result)
        else:
            error_msg = result.get("error", "Refund initiation failed")
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            elif "cannot refund" in error_msg.lower() or "invalid state" in error_msg.lower():
                raise HTTPException(status_code=400, detail=error_msg)
            else:
                raise HTTPException(status_code=422, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Refund initiation error", exc_info=e, transaction_id=transaction_id)
        raise HTTPException(status_code=500, detail="Internal server error")
