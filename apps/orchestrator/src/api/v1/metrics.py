"""
Metrics API endpoints for Prometheus monitoring
"""
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
import structlog
from src.monitoring.metrics import get_metrics_handler, metrics

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus format for scraping by monitoring systems.
    This endpoint should be called by Prometheus server to collect metrics.
    """
    try:
        metrics_data = get_metrics_handler()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error("Failed to generate metrics", exc_info=e)
        metrics.record_error(
            error_type=type(e).__name__,
            component="metrics_endpoint"
        )
        return Response(
            content="# Failed to generate metrics\n",
            status_code=500,
            media_type="text/plain"
        )

@router.get("/metrics/health")
async def get_metrics_health():
    """
    Metrics system health check
    
    Returns the health status of the metrics collection system.
    """
    try:
        return {
            "status": "healthy",
            "metrics_enabled": True,
            "collectors": [
                "payment_metrics",
                "transaction_metrics", 
                "http_metrics",
                "error_metrics",
                "fraud_metrics",
                "provider_metrics",
                "celery_metrics",
                "system_metrics"
            ]
        }
    except Exception as e:
        logger.error("Metrics health check failed", exc_info=e)
        return {
            "status": "unhealthy",
            "error": str(e)
        }
