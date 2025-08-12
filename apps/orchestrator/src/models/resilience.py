"""
Database models for resilience services
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from src.models.transaction import Base

class IdempotencyRecord(Base):
    """Idempotency record model"""
    __tablename__ = "idempotency_records"
    
    key = Column(String(255), primary_key=True, index=True)
    status = Column(String(50), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)
    response_data = Column(JSON, nullable=True)
    error_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    attempt_count = Column(Integer, default=1, nullable=False)

class CircuitBreakerRecord(Base):
    """Circuit breaker state persistence"""
    __tablename__ = "circuit_breaker_records"
    
    name = Column(String(255), primary_key=True)
    state = Column(String(50), nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    last_failure_time = Column(DateTime, nullable=True)
    last_success_time = Column(DateTime, nullable=True)
    last_state_change = Column(DateTime, default=datetime.now, nullable=False)
    total_calls = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
