"""
Prometheus metrics for SyncCash Orchestrator monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client.core import CollectorRegistry
import time
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)

# Create custom registry for better control
REGISTRY = CollectorRegistry()

# Application Info
app_info = Info(
    'synccash_orchestrator_info',
    'SyncCash Orchestrator application information',
    registry=REGISTRY
)

# Payment Metrics
payment_requests_total = Counter(
    'synccash_payment_requests_total',
    'Total number of payment requests',
    ['status', 'provider', 'risk_level'],
    registry=REGISTRY
)

payment_duration_seconds = Histogram(
    'synccash_payment_duration_seconds',
    'Payment processing duration in seconds',
    ['provider', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY
)

payment_amount_histogram = Histogram(
    'synccash_payment_amount_ghs',
    'Payment amounts in GHS',
    ['provider'],
    buckets=[1, 10, 50, 100, 500, 1000, 5000, 10000, 50000],
    registry=REGISTRY
)

# Transaction Status Metrics
transaction_status_total = Counter(
    'synccash_transaction_status_total',
    'Total transactions by status',
    ['status', 'provider'],
    registry=REGISTRY
)

# System Health Metrics
active_transactions = Gauge(
    'synccash_active_transactions',
    'Number of active transactions',
    registry=REGISTRY
)

database_connections = Gauge(
    'synccash_database_connections',
    'Number of active database connections',
    registry=REGISTRY
)

redis_connections = Gauge(
    'synccash_redis_connections',
    'Number of active Redis connections',
    registry=REGISTRY
)

# API Metrics
http_requests_total = Counter(
    'synccash_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    'synccash_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY
)

# Error Metrics
errors_total = Counter(
    'synccash_errors_total',
    'Total number of errors',
    ['error_type', 'component'],
    registry=REGISTRY
)

# Fraud Detection Metrics
fraud_checks_total = Counter(
    'synccash_fraud_checks_total',
    'Total fraud detection checks',
    ['risk_level', 'service_status'],
    registry=REGISTRY
)

fraud_service_duration_seconds = Histogram(
    'synccash_fraud_service_duration_seconds',
    'Fraud service response time in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=REGISTRY
)

# Provider Metrics
provider_requests_total = Counter(
    'synccash_provider_requests_total',
    'Total requests to payment providers',
    ['provider', 'status'],
    registry=REGISTRY
)

provider_response_time_seconds = Histogram(
    'synccash_provider_response_time_seconds',
    'Provider API response time in seconds',
    ['provider'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=REGISTRY
)

# Celery Task Metrics
celery_tasks_total = Counter(
    'synccash_celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status'],
    registry=REGISTRY
)

celery_task_duration_seconds = Histogram(
    'synccash_celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
    registry=REGISTRY
)

class MetricsCollector:
    """Centralized metrics collection and management"""
    
    def __init__(self):
        self.start_time = time.time()
        self._initialize_app_info()
    
    def _initialize_app_info(self):
        """Initialize application information metrics"""
        app_info.info({
            'version': '1.0.0',
            'service': 'synccash-orchestrator',
            'environment': 'development'  # TODO: Get from config
        })
    
    def record_payment_request(self, status: str, provider: str = "unknown", 
                             risk_level: str = "unknown", duration: float = 0.0,
                             amount: float = 0.0):
        """Record payment request metrics"""
        payment_requests_total.labels(
            status=status, 
            provider=provider, 
            risk_level=risk_level
        ).inc()
        
        if duration > 0:
            payment_duration_seconds.labels(
                provider=provider, 
                status=status
            ).observe(duration)
        
        if amount > 0:
            payment_amount_histogram.labels(provider=provider).observe(amount)
    
    def record_transaction_status(self, status: str, provider: str = "unknown"):
        """Record transaction status change"""
        transaction_status_total.labels(
            status=status, 
            provider=provider
        ).inc()
    
    def record_http_request(self, method: str, endpoint: str, 
                          status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_error(self, error_type: str, component: str):
        """Record error occurrence"""
        errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def record_fraud_check(self, risk_level: str, service_status: str, 
                          duration: float = 0.0):
        """Record fraud detection metrics"""
        fraud_checks_total.labels(
            risk_level=risk_level,
            service_status=service_status
        ).inc()
        
        if duration > 0:
            fraud_service_duration_seconds.observe(duration)
    
    def record_provider_request(self, provider: str, status: str, 
                              duration: float = 0.0):
        """Record provider API request metrics"""
        provider_requests_total.labels(
            provider=provider,
            status=status
        ).inc()
        
        if duration > 0:
            provider_response_time_seconds.labels(provider=provider).observe(duration)
    
    def record_celery_task(self, task_name: str, status: str, 
                          duration: float = 0.0):
        """Record Celery task metrics"""
        celery_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        if duration > 0:
            celery_task_duration_seconds.labels(task_name=task_name).observe(duration)
    
    def update_system_gauges(self, active_txns: int = 0, db_conns: int = 0, 
                           redis_conns: int = 0):
        """Update system health gauges"""
        active_transactions.set(active_txns)
        database_connections.set(db_conns)
        redis_connections.set(redis_conns)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(REGISTRY).decode('utf-8')

# Global metrics collector instance
metrics = MetricsCollector()

def get_metrics_handler():
    """FastAPI endpoint handler for metrics"""
    return metrics.get_metrics()
