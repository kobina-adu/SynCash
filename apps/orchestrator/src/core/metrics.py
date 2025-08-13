"""
Prometheus Metrics for SyncCash Orchestrator
Comprehensive monitoring and observability for payment processing
"""

from prometheus_client import Counter, Histogram, Gauge, Enum, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
import time
from typing import Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

# Create custom registry for better control
REGISTRY = CollectorRegistry()

# =============================================================================
# PAYMENT PROCESSING METRICS
# =============================================================================

# Payment request counters
payment_requests_total = Counter(
    'synccash_payment_requests_total',
    'Total number of payment requests received',
    ['user_id', 'status', 'provider', 'risk_level'],
    registry=REGISTRY
)

payment_processing_duration = Histogram(
    'synccash_payment_processing_duration_seconds',
    'Time spent processing payment requests',
    ['status', 'provider', 'risk_level'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY
)

# Transaction lifecycle metrics
transaction_status_changes = Counter(
    'synccash_transaction_status_changes_total',
    'Total number of transaction status changes',
    ['from_status', 'to_status', 'provider'],
    registry=REGISTRY
)

transaction_amounts = Histogram(
    'synccash_transaction_amounts_ghs',
    'Distribution of transaction amounts in GHS',
    ['provider', 'status'],
    buckets=[1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000],
    registry=REGISTRY
)

# =============================================================================
# FRAUD DETECTION METRICS
# =============================================================================

fraud_detection_checks = Counter(
    'synccash_fraud_checks_total',
    'Total number of fraud detection checks performed',
    ['risk_level', 'result'],
    registry=REGISTRY
)

fraud_scores = Histogram(
    'synccash_fraud_scores',
    'Distribution of fraud risk scores',
    ['risk_level'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=REGISTRY
)

blocked_transactions = Counter(
    'synccash_blocked_transactions_total',
    'Total number of transactions blocked due to fraud',
    ['reason', 'risk_level'],
    registry=REGISTRY
)

# =============================================================================
# PROVIDER METRICS
# =============================================================================

provider_requests = Counter(
    'synccash_provider_requests_total',
    'Total requests sent to payment providers',
    ['provider', 'status', 'operation'],
    registry=REGISTRY
)

provider_response_time = Histogram(
    'synccash_provider_response_time_seconds',
    'Response time from payment providers',
    ['provider', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=REGISTRY
)

provider_errors = Counter(
    'synccash_provider_errors_total',
    'Total number of provider errors',
    ['provider', 'error_type', 'error_code'],
    registry=REGISTRY
)

# =============================================================================
# SYSTEM HEALTH METRICS
# =============================================================================

active_transactions = Gauge(
    'synccash_active_transactions',
    'Number of currently active transactions',
    ['status'],
    registry=REGISTRY
)

database_connections = Gauge(
    'synccash_database_connections',
    'Number of active database connections',
    ['pool_status'],
    registry=REGISTRY
)

redis_operations = Counter(
    'synccash_redis_operations_total',
    'Total Redis operations performed',
    ['operation', 'status'],
    registry=REGISTRY
)

# =============================================================================
# API METRICS
# =============================================================================

http_requests_total = Counter(
    'synccash_http_requests_total',
    'Total HTTP requests received',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

http_request_duration = Histogram(
    'synccash_http_request_duration_seconds',
    'HTTP request processing time',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=REGISTRY
)

# =============================================================================
# BUSINESS METRICS
# =============================================================================

daily_transaction_volume = Gauge(
    'synccash_daily_transaction_volume_ghs',
    'Total transaction volume for current day in GHS',
    ['provider'],
    registry=REGISTRY
)

daily_transaction_count = Gauge(
    'synccash_daily_transaction_count',
    'Total number of transactions for current day',
    ['provider', 'status'],
    registry=REGISTRY
)

success_rate = Gauge(
    'synccash_success_rate_percentage',
    'Transaction success rate percentage',
    ['provider', 'time_window'],
    registry=REGISTRY
)

# =============================================================================
# ERROR TRACKING
# =============================================================================

application_errors = Counter(
    'synccash_application_errors_total',
    'Total application errors',
    ['error_type', 'component', 'severity'],
    registry=REGISTRY
)

validation_errors = Counter(
    'synccash_validation_errors_total',
    'Total validation errors',
    ['field', 'error_type'],
    registry=REGISTRY
)

# =============================================================================
# RETRY AND RESILIENCE METRICS
# =============================================================================

retry_attempts = Counter(
    'synccash_retry_attempts_total',
    'Total number of retry attempts',
    ['operation', 'provider', 'attempt_number'],
    registry=REGISTRY
)

circuit_breaker_state = Enum(
    'synccash_circuit_breaker_state',
    'Current state of circuit breakers',
    ['service'],
    states=['closed', 'open', 'half_open'],
    registry=REGISTRY
)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

class MetricsCollector:
    """Centralized metrics collection and management"""
    
    def __init__(self):
        self.start_time = time.time()
        logger.info("Metrics collector initialized")
    
    def record_payment_request(self, user_id: str, amount: float, provider: str = "unknown", 
                             status: str = "initiated", risk_level: str = "low"):
        """Record a payment request"""
        payment_requests_total.labels(
            user_id=user_id[:8] + "***",  # Anonymize user ID
            status=status,
            provider=provider,
            risk_level=risk_level
        ).inc()
        
        transaction_amounts.labels(
            provider=provider,
            status=status
        ).observe(amount)
    
    def record_payment_duration(self, duration: float, status: str, provider: str = "unknown", 
                              risk_level: str = "low"):
        """Record payment processing duration"""
        payment_processing_duration.labels(
            status=status,
            provider=provider,
            risk_level=risk_level
        ).observe(duration)
    
    def record_status_change(self, from_status: str, to_status: str, provider: str = "unknown"):
        """Record transaction status change"""
        transaction_status_changes.labels(
            from_status=from_status,
            to_status=to_status,
            provider=provider
        ).inc()
    
    def record_fraud_check(self, risk_level: str, result: str, score: float = 0.0):
        """Record fraud detection check"""
        fraud_detection_checks.labels(
            risk_level=risk_level,
            result=result
        ).inc()
        
        fraud_scores.labels(risk_level=risk_level).observe(score)
    
    def record_blocked_transaction(self, reason: str, risk_level: str):
        """Record blocked transaction"""
        blocked_transactions.labels(
            reason=reason,
            risk_level=risk_level
        ).inc()
    
    def record_provider_request(self, provider: str, status: str, operation: str, 
                              response_time: float = 0.0):
        """Record provider API request"""
        provider_requests.labels(
            provider=provider,
            status=status,
            operation=operation
        ).inc()
        
        if response_time > 0:
            provider_response_time.labels(
                provider=provider,
                status=status
            ).observe(response_time)
    
    def record_provider_error(self, provider: str, error_type: str, error_code: str = "unknown"):
        """Record provider error"""
        provider_errors.labels(
            provider=provider,
            error_type=error_type,
            error_code=error_code
        ).inc()
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        http_request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).observe(duration)
    
    def record_application_error(self, error_type: str, component: str, severity: str = "error"):
        """Record application error"""
        application_errors.labels(
            error_type=error_type,
            component=component,
            severity=severity
        ).inc()
    
    def record_validation_error(self, field: str, error_type: str):
        """Record validation error"""
        validation_errors.labels(
            field=field,
            error_type=error_type
        ).inc()
    
    def update_active_transactions(self, status: str, count: int):
        """Update active transaction count"""
        active_transactions.labels(status=status).set(count)
    
    def update_database_connections(self, pool_status: str, count: int):
        """Update database connection count"""
        database_connections.labels(pool_status=pool_status).set(count)
    
    def record_redis_operation(self, operation: str, status: str):
        """Record Redis operation"""
        redis_operations.labels(
            operation=operation,
            status=status
        ).inc()
    
    def update_daily_metrics(self, provider: str, volume: float, count: int, status: str):
        """Update daily business metrics"""
        daily_transaction_volume.labels(provider=provider).set(volume)
        daily_transaction_count.labels(provider=provider, status=status).set(count)
    
    def update_success_rate(self, provider: str, time_window: str, rate: float):
        """Update success rate percentage"""
        success_rate.labels(provider=provider, time_window=time_window).set(rate)
    
    def record_retry_attempt(self, operation: str, provider: str, attempt_number: int):
        """Record retry attempt"""
        retry_attempts.labels(
            operation=operation,
            provider=provider,
            attempt_number=str(attempt_number)
        ).inc()
    
    def set_circuit_breaker_state(self, service: str, state: str):
        """Set circuit breaker state"""
        circuit_breaker_state.labels(service=service).state(state)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(REGISTRY)
    
    def get_content_type(self) -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector
