"""
Idempotency Service for SyncCash Orchestrator
Prevents duplicate request processing with idempotency keys
"""
import asyncio
import hashlib
import json
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import structlog

from src.core.redis_client import get_redis_client
from src.core.database import get_db_session
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class IdempotencyStatus(Enum):
    """Idempotency operation status"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class IdempotencyRecord:
    """Idempotency record structure"""
    key: str
    status: IdempotencyStatus
    request_hash: str
    response_data: Optional[Dict[str, Any]] = None
    error_data: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    expires_at: datetime = None
    attempt_count: int = 1
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(hours=24)  # Default 24h expiry

class IdempotencyResult:
    """Result of idempotency check"""
    
    def __init__(self, is_duplicate: bool, record: Optional[IdempotencyRecord] = None,
                 should_process: bool = True, cached_response: Optional[Any] = None):
        self.is_duplicate = is_duplicate
        self.record = record
        self.should_process = should_process
        self.cached_response = cached_response

class IdempotencyService:
    """Service for handling request idempotency"""
    
    def __init__(self):
        self.redis_prefix = "idempotency:"
        self.default_ttl_seconds = 86400  # 24 hours
        self.processing_timeout_seconds = 300  # 5 minutes
    
    def generate_request_hash(self, request_data: Dict[str, Any]) -> str:
        """Generate hash of request data for comparison"""
        # Sort keys to ensure consistent hashing
        sorted_data = json.dumps(request_data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    async def check_idempotency(
        self,
        idempotency_key: str,
        request_data: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> IdempotencyResult:
        """Check if request is idempotent and return appropriate result"""
        
        if not idempotency_key:
            # No idempotency key provided, allow processing
            return IdempotencyResult(is_duplicate=False, should_process=True)
        
        ttl = ttl_seconds or self.default_ttl_seconds
        request_hash = self.generate_request_hash(request_data)
        
        try:
            # Try to get existing record from Redis first (faster)
            redis_record = await self._get_redis_record(idempotency_key)
            
            if redis_record:
                # Validate request consistency
                if redis_record.request_hash != request_hash:
                    logger.warning("Idempotency key reused with different request data",
                                 idempotency_key=idempotency_key,
                                 existing_hash=redis_record.request_hash,
                                 new_hash=request_hash)
                    
                    metrics.record_counter("idempotency_key_conflict")
                    raise ValueError("Idempotency key conflict: same key with different request data")
                
                # Check record status
                if redis_record.status == IdempotencyStatus.COMPLETED:
                    logger.info("Returning cached response for idempotent request",
                               idempotency_key=idempotency_key)
                    
                    metrics.record_counter("idempotency_cache_hit")
                    return IdempotencyResult(
                        is_duplicate=True,
                        record=redis_record,
                        should_process=False,
                        cached_response=redis_record.response_data
                    )
                
                elif redis_record.status == IdempotencyStatus.PROCESSING:
                    # Check if processing has timed out
                    if self._is_processing_timeout(redis_record):
                        logger.warning("Idempotent request processing timeout, allowing retry",
                                     idempotency_key=idempotency_key,
                                     created_at=redis_record.created_at)
                        
                        # Update attempt count and allow processing
                        redis_record.attempt_count += 1
                        await self._store_redis_record(idempotency_key, redis_record, ttl)
                        
                        metrics.record_counter("idempotency_processing_timeout")
                        return IdempotencyResult(
                            is_duplicate=True,
                            record=redis_record,
                            should_process=True
                        )
                    else:
                        logger.info("Request already being processed",
                                   idempotency_key=idempotency_key)
                        
                        metrics.record_counter("idempotency_already_processing")
                        return IdempotencyResult(
                            is_duplicate=True,
                            record=redis_record,
                            should_process=False
                        )
                
                elif redis_record.status == IdempotencyStatus.FAILED:
                    logger.info("Retrying previously failed idempotent request",
                               idempotency_key=idempotency_key)
                    
                    # Allow retry of failed requests
                    redis_record.attempt_count += 1
                    redis_record.status = IdempotencyStatus.PROCESSING
                    await self._store_redis_record(idempotency_key, redis_record, ttl)
                    
                    metrics.record_counter("idempotency_retry_failed")
                    return IdempotencyResult(
                        is_duplicate=True,
                        record=redis_record,
                        should_process=True
                    )
            
            # No existing record, create new processing record
            new_record = IdempotencyRecord(
                key=idempotency_key,
                status=IdempotencyStatus.PROCESSING,
                request_hash=request_hash,
                expires_at=datetime.now() + timedelta(seconds=ttl)
            )
            
            await self._store_redis_record(idempotency_key, new_record, ttl)
            await self._store_database_record(new_record)
            
            logger.info("Created new idempotency record",
                       idempotency_key=idempotency_key)
            
            metrics.record_counter("idempotency_new_request")
            return IdempotencyResult(
                is_duplicate=False,
                record=new_record,
                should_process=True
            )
            
        except Exception as e:
            logger.error("Idempotency check failed",
                        idempotency_key=idempotency_key,
                        exc_info=e)
            
            metrics.record_error("idempotency_check_error", "idempotency_service")
            
            # On error, allow processing to avoid blocking legitimate requests
            return IdempotencyResult(is_duplicate=False, should_process=True)
    
    async def store_success_response(
        self,
        idempotency_key: str,
        response_data: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ):
        """Store successful response for idempotent request"""
        
        if not idempotency_key:
            return
        
        ttl = ttl_seconds or self.default_ttl_seconds
        
        try:
            record = await self._get_redis_record(idempotency_key)
            if record:
                record.status = IdempotencyStatus.COMPLETED
                record.response_data = response_data
                record.completed_at = datetime.now()
                
                await self._store_redis_record(idempotency_key, record, ttl)
                await self._update_database_record(record)
                
                logger.info("Stored successful response for idempotent request",
                           idempotency_key=idempotency_key)
                
                metrics.record_counter("idempotency_success_stored")
            
        except Exception as e:
            logger.error("Failed to store idempotency success response",
                        idempotency_key=idempotency_key,
                        exc_info=e)
            
            metrics.record_error("idempotency_store_success_error", "idempotency_service")
    
    async def store_failure_response(
        self,
        idempotency_key: str,
        error_data: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ):
        """Store failure response for idempotent request"""
        
        if not idempotency_key:
            return
        
        ttl = ttl_seconds or self.default_ttl_seconds
        
        try:
            record = await self._get_redis_record(idempotency_key)
            if record:
                record.status = IdempotencyStatus.FAILED
                record.error_data = error_data
                record.completed_at = datetime.now()
                
                await self._store_redis_record(idempotency_key, record, ttl)
                await self._update_database_record(record)
                
                logger.info("Stored failure response for idempotent request",
                           idempotency_key=idempotency_key)
                
                metrics.record_counter("idempotency_failure_stored")
            
        except Exception as e:
            logger.error("Failed to store idempotency failure response",
                        idempotency_key=idempotency_key,
                        exc_info=e)
            
            metrics.record_error("idempotency_store_failure_error", "idempotency_service")
    
    async def _get_redis_record(self, idempotency_key: str) -> Optional[IdempotencyRecord]:
        """Get idempotency record from Redis"""
        try:
            redis_client = await get_redis_client()
            redis_key = f"{self.redis_prefix}{idempotency_key}"
            
            data = await redis_client.get(redis_key)
            if data:
                record_dict = json.loads(data)
                
                # Convert datetime strings back to datetime objects
                if record_dict.get('created_at'):
                    record_dict['created_at'] = datetime.fromisoformat(record_dict['created_at'])
                if record_dict.get('completed_at'):
                    record_dict['completed_at'] = datetime.fromisoformat(record_dict['completed_at'])
                if record_dict.get('expires_at'):
                    record_dict['expires_at'] = datetime.fromisoformat(record_dict['expires_at'])
                
                # Convert status string to enum
                record_dict['status'] = IdempotencyStatus(record_dict['status'])
                
                return IdempotencyRecord(**record_dict)
            
            return None
            
        except Exception as e:
            logger.error("Failed to get Redis idempotency record",
                        idempotency_key=idempotency_key,
                        exc_info=e)
            return None
    
    async def _store_redis_record(
        self,
        idempotency_key: str,
        record: IdempotencyRecord,
        ttl_seconds: int
    ):
        """Store idempotency record in Redis"""
        try:
            redis_client = await get_redis_client()
            redis_key = f"{self.redis_prefix}{idempotency_key}"
            
            # Convert record to dict and handle datetime serialization
            record_dict = asdict(record)
            for key, value in record_dict.items():
                if isinstance(value, datetime):
                    record_dict[key] = value.isoformat()
                elif isinstance(value, IdempotencyStatus):
                    record_dict[key] = value.value
            
            data = json.dumps(record_dict)
            await redis_client.setex(redis_key, ttl_seconds, data)
            
        except Exception as e:
            logger.error("Failed to store Redis idempotency record",
                        idempotency_key=idempotency_key,
                        exc_info=e)
            raise
    
    async def _store_database_record(self, record: IdempotencyRecord):
        """Store idempotency record in database for persistence"""
        try:
            async with get_db_session() as session:
                await session.execute(
                    """
                    INSERT INTO idempotency_records 
                    (key, status, request_hash, response_data, error_data, 
                     created_at, completed_at, expires_at, attempt_count)
                    VALUES (:key, :status, :request_hash, :response_data, :error_data,
                            :created_at, :completed_at, :expires_at, :attempt_count)
                    ON CONFLICT (key) DO UPDATE SET
                        status = EXCLUDED.status,
                        response_data = EXCLUDED.response_data,
                        error_data = EXCLUDED.error_data,
                        completed_at = EXCLUDED.completed_at,
                        attempt_count = EXCLUDED.attempt_count
                    """,
                    {
                        "key": record.key,
                        "status": record.status.value,
                        "request_hash": record.request_hash,
                        "response_data": json.dumps(record.response_data) if record.response_data else None,
                        "error_data": json.dumps(record.error_data) if record.error_data else None,
                        "created_at": record.created_at,
                        "completed_at": record.completed_at,
                        "expires_at": record.expires_at,
                        "attempt_count": record.attempt_count
                    }
                )
                await session.commit()
                
        except Exception as e:
            logger.error("Failed to store database idempotency record",
                        idempotency_key=record.key,
                        exc_info=e)
            # Don't raise - Redis storage is primary
    
    async def _update_database_record(self, record: IdempotencyRecord):
        """Update idempotency record in database"""
        try:
            async with get_db_session() as session:
                await session.execute(
                    """
                    UPDATE idempotency_records 
                    SET status = :status,
                        response_data = :response_data,
                        error_data = :error_data,
                        completed_at = :completed_at,
                        attempt_count = :attempt_count
                    WHERE key = :key
                    """,
                    {
                        "key": record.key,
                        "status": record.status.value,
                        "response_data": json.dumps(record.response_data) if record.response_data else None,
                        "error_data": json.dumps(record.error_data) if record.error_data else None,
                        "completed_at": record.completed_at,
                        "attempt_count": record.attempt_count
                    }
                )
                await session.commit()
                
        except Exception as e:
            logger.error("Failed to update database idempotency record",
                        idempotency_key=record.key,
                        exc_info=e)
    
    def _is_processing_timeout(self, record: IdempotencyRecord) -> bool:
        """Check if processing has timed out"""
        if record.status != IdempotencyStatus.PROCESSING:
            return False
        
        time_since_created = (datetime.now() - record.created_at).total_seconds()
        return time_since_created > self.processing_timeout_seconds
    
    async def cleanup_expired_records(self):
        """Clean up expired idempotency records"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    "DELETE FROM idempotency_records WHERE expires_at < NOW()"
                )
                await session.commit()
                
                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info("Cleaned up expired idempotency records",
                               deleted_count=deleted_count)
                    
                    metrics.record_counter("idempotency_records_cleaned", deleted_count)
                
        except Exception as e:
            logger.error("Failed to cleanup expired idempotency records", exc_info=e)
    
    async def get_record_stats(self) -> Dict[str, Any]:
        """Get idempotency record statistics"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(attempt_count) as avg_attempts
                    FROM idempotency_records 
                    WHERE expires_at > NOW()
                    GROUP BY status
                    """
                )
                
                stats = {}
                total_records = 0
                
                for row in result:
                    status, count, avg_attempts = row
                    stats[status] = {
                        "count": count,
                        "avg_attempts": float(avg_attempts) if avg_attempts else 0
                    }
                    total_records += count
                
                return {
                    "total_active_records": total_records,
                    "by_status": stats,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to get idempotency stats", exc_info=e)
            return {"error": "Failed to retrieve statistics"}

# Global idempotency service
idempotency_service = IdempotencyService()
