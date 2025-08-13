"""
Metrics API endpoints for Prometheus monitoring
"""

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
import structlog
from typing import Dict, Any
import time
from datetime import datetime, timedelta

from src.core.metrics import get_metrics_collector
from src.core.database import get_db_session
from src.core.redis_client import get_redis_client
from src.models.transaction import Transaction, TransactionStatus

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns all application metrics in Prometheus format for scraping.
    This endpoint is called by Prometheus to collect metrics data.
    """
    try:
        # Update real-time metrics before serving
        await _update_realtime_metrics()
        
        metrics_collector = get_metrics_collector()
        metrics_data = metrics_collector.get_metrics()
        
        logger.debug("Metrics endpoint accessed", metrics_size=len(metrics_data))
        
        return Response(
            content=metrics_data,
            media_type=metrics_collector.get_content_type()
        )
        
    except Exception as e:
        logger.error("Failed to generate metrics", exc_info=e)
        # Return empty metrics rather than failing
        return Response(
            content="# Metrics temporarily unavailable\n",
            media_type="text/plain"
        )

@router.get("/metrics/health")
async def metrics_health_check():
    """
    Health check for metrics system
    """
    try:
        metrics_collector = get_metrics_collector()
        
        return {
            "status": "healthy",
            "metrics_system": "operational",
            "timestamp": time.time(),
            "collector_uptime": time.time() - metrics_collector.start_time
        }
        
    except Exception as e:
        logger.error("Metrics health check failed", exc_info=e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Human-readable metrics summary for debugging and monitoring
    """
    try:
        summary = await _generate_metrics_summary()
        return {
            "status": "success",
            "timestamp": time.time(),
            "summary": summary
        }
        
    except Exception as e:
        logger.error("Failed to generate metrics summary", exc_info=e)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

async def _update_realtime_metrics():
    """Update real-time metrics before serving to Prometheus"""
    try:
        metrics_collector = get_metrics_collector()
        
        # Update active transaction counts
        await _update_active_transaction_metrics(metrics_collector)
        
        # Update database connection metrics
        await _update_database_metrics(metrics_collector)
        
        # Update daily business metrics
        await _update_daily_business_metrics(metrics_collector)
        
    except Exception as e:
        logger.warning("Failed to update real-time metrics", exc_info=e)

async def _update_active_transaction_metrics(metrics_collector):
    """Update active transaction counts by status"""
    try:
        async with get_db_session() as session:
            # Count transactions by status
            for status in TransactionStatus:
                result = await session.execute(
                    f"SELECT COUNT(*) FROM transactions WHERE status = '{status.value}'"
                )
                count = result.scalar() or 0
                metrics_collector.update_active_transactions(status.value, count)
                
    except Exception as e:
        logger.warning("Failed to update active transaction metrics", exc_info=e)

async def _update_database_metrics(metrics_collector):
    """Update database connection pool metrics"""
    try:
        # This would need to be implemented based on your connection pool
        # For now, we'll set placeholder values
        metrics_collector.update_database_connections("active", 5)
        metrics_collector.update_database_connections("idle", 3)
        
    except Exception as e:
        logger.warning("Failed to update database metrics", exc_info=e)

async def _update_daily_business_metrics(metrics_collector):
    """Update daily business metrics"""
    try:
        today = datetime.utcnow().date()
        
        async with get_db_session() as session:
            # Daily transaction volume and count by provider
            providers = ["mtn", "airtel", "telecel", "unknown"]
            
            for provider in providers:
                # Volume query
                volume_result = await session.execute(f"""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM transactions 
                    WHERE DATE(created_at) = '{today}' 
                    AND (primary_provider = '{provider}' OR primary_provider IS NULL)
                """)
                volume = volume_result.scalar() or 0.0
                
                # Count by status
                for status in ["confirmed", "failed", "pending"]:
                    count_result = await session.execute(f"""
                        SELECT COUNT(*) 
                        FROM transactions 
                        WHERE DATE(created_at) = '{today}' 
                        AND status = '{status}'
                        AND (primary_provider = '{provider}' OR primary_provider IS NULL)
                    """)
                    count = count_result.scalar() or 0
                    
                    metrics_collector.update_daily_metrics(provider, volume, count, status)
                
                # Calculate success rate for last hour
                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                success_result = await session.execute(f"""
                    SELECT 
                        COUNT(CASE WHEN status = 'confirmed' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(*), 0) as success_rate
                    FROM transactions 
                    WHERE created_at >= '{one_hour_ago}'
                    AND (primary_provider = '{provider}' OR primary_provider IS NULL)
                """)
                success_rate = success_result.scalar() or 0.0
                metrics_collector.update_success_rate(provider, "1h", success_rate)
                
    except Exception as e:
        logger.warning("Failed to update daily business metrics", exc_info=e)

async def _generate_metrics_summary() -> Dict[str, Any]:
    """Generate human-readable metrics summary"""
    try:
        summary = {
            "system_health": {},
            "transaction_stats": {},
            "provider_stats": {},
            "error_stats": {}
        }
        
        # Get basic system health
        async with get_db_session() as session:
            # Total transactions today
            today = datetime.utcnow().date()
            total_today_result = await session.execute(f"""
                SELECT COUNT(*) FROM transactions WHERE DATE(created_at) = '{today}'
            """)
            total_today = total_today_result.scalar() or 0
            
            # Success rate today
            success_today_result = await session.execute(f"""
                SELECT 
                    COUNT(CASE WHEN status = 'confirmed' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(*), 0) as success_rate
                FROM transactions 
                WHERE DATE(created_at) = '{today}'
            """)
            success_rate_today = success_today_result.scalar() or 0.0
            
            # Average transaction amount today
            avg_amount_result = await session.execute(f"""
                SELECT AVG(amount) FROM transactions WHERE DATE(created_at) = '{today}'
            """)
            avg_amount = avg_amount_result.scalar() or 0.0
            
            summary["transaction_stats"] = {
                "total_today": total_today,
                "success_rate_today": round(success_rate_today, 2),
                "average_amount_today": round(avg_amount, 2)
            }
        
        # Check Redis connectivity
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"
        
        summary["system_health"] = {
            "database": "healthy",  # If we got here, DB is working
            "redis": redis_status,
            "timestamp": datetime.now(datetime.timezone.utc).isoformat()
        }
        
        return summary
        
    except Exception as e:
        logger.error("Failed to generate metrics summary", exc_info=e)
        return {"error": str(e)}
