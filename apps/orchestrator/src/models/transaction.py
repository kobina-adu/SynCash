"""
Transaction models for SyncCash Orchestrator
"""

from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class TransactionStatus(str, Enum):
    """Transaction status enumeration"""
    INITIATED = "initiated"
    VALIDATING = "validating"
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentProvider(str, Enum):
    """Payment provider enumeration"""
    MTN = "mtn"
    AIRTEL = "airtel"
    TELECEL = "telecel"

class TransactionType(str, Enum):
    """Transaction type enumeration"""
    PAYMENT = "payment"
    REFUND = "refund"
    TRANSFER = "transfer"
    DEBIT = "debit"
    CASH_OUT = "cash_out"

class Transaction(Base):
    """Main transaction model"""
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transaction details
    external_reference = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="GHS", nullable=False)
    description = Column(Text)
    
    # Transaction type and status
    transaction_type = Column(SQLEnum(TransactionType), default=TransactionType.PAYMENT)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.INITIATED, index=True)
    
    # Provider information
    primary_provider = Column(SQLEnum(PaymentProvider))
    providers_used = Column(JSONB)  # List of providers and amounts
    
    # Recipient information
    recipient_phone = Column(String(20))
    recipient_name = Column(String(255))
    recipient_provider = Column(SQLEnum(PaymentProvider))
    
    # Transaction metadata
    transaction_metadata = Column(JSONB, default=dict)
    fraud_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="LOW")
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    confirmed_at = Column(DateTime(timezone=True))
    
    # Retry information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_at = Column(DateTime(timezone=True))
    
    # Fees and charges
    total_fees = Column(Float, default=0.0)
    provider_fees = Column(JSONB, default=dict)
    
    # Audit trail
    created_by = Column(String(255))
    updated_by = Column(String(255))
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, status={self.status}, amount={self.amount})>"
    
    @property
    def is_final_state(self) -> bool:
        """Check if transaction is in a final state"""
        return self.status in [
            TransactionStatus.CONFIRMED,
            TransactionStatus.FAILED,
            TransactionStatus.EXPIRED,
            TransactionStatus.REFUNDED,
            TransactionStatus.CANCELLED
        ]
    
    @property
    def can_retry(self) -> bool:
        """Check if transaction can be retried"""
        return (
            self.status == TransactionStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary"""
        return {
            "id": str(self.id),
            "external_reference": self.external_reference,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "transaction_type": self.transaction_type.value if self.transaction_type else None,
            "status": self.status.value if self.status else None,
            "primary_provider": self.primary_provider.value if self.primary_provider else None,
            "providers_used": self.providers_used,
            "recipient_phone": self.recipient_phone,
            "recipient_name": self.recipient_name,
            "recipient_provider": self.recipient_provider.value if self.recipient_provider else None,
            "metadata": self.transaction_metadata,
            "fraud_score": self.fraud_score,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "total_fees": self.total_fees,
            "provider_fees": self.provider_fees
        }

class TransactionEvent(Base):
    """Transaction event log for audit trail"""
    __tablename__ = "transaction_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)
    from_status = Column(SQLEnum(TransactionStatus))
    to_status = Column(SQLEnum(TransactionStatus))
    
    # Event data
    event_data = Column(JSONB, default=dict)
    error_message = Column(Text)
    provider = Column(SQLEnum(PaymentProvider))
    
    # Timing and attribution
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))
    
    def __repr__(self):
        return f"<TransactionEvent(id={self.id}, type={self.event_type})>"

class ProviderTransaction(Base):
    """Provider-specific transaction details"""
    __tablename__ = "provider_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Provider details
    provider = Column(SQLEnum(PaymentProvider), nullable=False)
    provider_transaction_id = Column(String(255))
    provider_reference = Column(String(255))
    
    # Amount and fees
    amount = Column(Float, nullable=False)
    provider_fee = Column(Float, default=0.0)
    
    # Status
    status = Column(String(50), nullable=False)
    provider_status = Column(String(50))
    
    # Provider response
    provider_response = Column(JSONB, default=dict)
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ProviderTransaction(id={self.id}, provider={self.provider})>"
