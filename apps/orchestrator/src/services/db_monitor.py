"""
Database Health Monitoring Service for SyncCash Orchestrator
Provides continuous monitoring and optimization of database connections
"""
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from src.core.database import (
    test_db_connection, 
    get_connection_pool_stats, 
    optimize_connection_pool,
    get_db_session
)
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class DatabaseHealthMonitor:
    """Monitors database health and optimizes connections"""
    
    def __init__(self):
        self.monitoring_active = False
        self.health_history = []
        self.alert_thresholds = {
            "response_time_ms": 1000,
            "consecutive_failures": 3,
            "connection_pool_utilization": 0.8
        }
        self.last_optimization = None
        
    async def start_monitoring(self, check_interval: int = 30):
        """Start continuous database health monitoring"""
        if self.monitoring_active:
            logger.warning("Database monitoring already active")
            return
            
        self.monitoring_active = True
        logger.info("Starting database health monitoring", check_interval=check_interval)
        
        while self.monitoring_active:
            try:
                await self._perform_health_check()
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error("Database monitoring error", exc_info=e)
                await asyncio.sleep(check_interval)
    
    async def stop_monitoring(self):
        """Stop database health monitoring"""
        self.monitoring_active = False
        logger.info("Database health monitoring stopped")
    
    async def _perform_health_check(self):
        """Perform comprehensive health check"""
        try:
            # Get database health
            db_result = await test_db_connection()
            pool_stats = await get_connection_pool_stats()
            
            # Create health record
            health_record = {
                "timestamp": datetime.now(),
                "healthy": db_result["healthy"],
                "response_time_ms": db_result["response_time_ms"],
                "connection_test": db_result["connection_test"],
                "transaction_test": db_result["transaction_test"],
                "table_access_test": db_result["table_access_test"],
                "pool_stats": pool_stats,
                "error": db_result.get("error")
            }
            
            # Store in history (keep last 100 records)
            self.health_history.append(health_record)
            if len(self.health_history) > 100:
                self.health_history.pop(0)
            
            # Record metrics
            metrics.record_gauge("db_health_response_time", db_result["response_time_ms"])
            metrics.record_gauge("db_connection_pool_size", pool_stats.get("pool_size", 0))
            metrics.record_gauge("db_connections_checked_out", pool_stats.get("checked_out", 0))
            metrics.record_gauge("db_connections_overflow", pool_stats.get("overflow", 0))
            
            if db_result["healthy"]:
                metrics.record_counter("db_health_check_success")
            else:
                metrics.record_counter("db_health_check_failure")
                metrics.record_error("db_health_check_failed", "db_monitor")
            
            # Check for optimization needs
            await self._check_optimization_needs(health_record)
            
            # Log health status
            if db_result["healthy"]:
                logger.debug("Database health check passed",
                           response_time_ms=db_result["response_time_ms"],
                           pool_utilization=self._calculate_pool_utilization(pool_stats))
            else:
                logger.warning("Database health check failed",
                             error=db_result.get("error"),
                             consecutive_failures=pool_stats.get("consecutive_failures", 0))
                
        except Exception as e:
            logger.error("Health check execution failed", exc_info=e)
            metrics.record_error("db_health_check_error", "db_monitor")
    
    async def _check_optimization_needs(self, health_record: Dict[str, Any]):
        """Check if database optimization is needed"""
        try:
            pool_stats = health_record["pool_stats"]
            
            # Check if optimization is needed
            needs_optimization = False
            reasons = []
            
            # High response time
            if health_record["response_time_ms"] > self.alert_thresholds["response_time_ms"]:
                needs_optimization = True
                reasons.append(f"High response time: {health_record['response_time_ms']}ms")
            
            # Too many consecutive failures
            consecutive_failures = pool_stats.get("consecutive_failures", 0)
            if consecutive_failures >= self.alert_thresholds["consecutive_failures"]:
                needs_optimization = True
                reasons.append(f"Consecutive failures: {consecutive_failures}")
            
            # High pool utilization
            pool_utilization = self._calculate_pool_utilization(pool_stats)
            if pool_utilization > self.alert_thresholds["connection_pool_utilization"]:
                needs_optimization = True
                reasons.append(f"High pool utilization: {pool_utilization:.2%}")
            
            # Perform optimization if needed and not done recently
            if needs_optimization:
                now = datetime.now()
                if (self.last_optimization is None or 
                    now - self.last_optimization > timedelta(minutes=5)):
                    
                    logger.info("Database optimization triggered", reasons=reasons)
                    await optimize_connection_pool()
                    self.last_optimization = now
                    metrics.record_counter("db_optimization_triggered")
                    
        except Exception as e:
            logger.error("Optimization check failed", exc_info=e)
    
    def _calculate_pool_utilization(self, pool_stats: Dict[str, Any]) -> float:
        """Calculate connection pool utilization percentage"""
        try:
            pool_size = pool_stats.get("pool_size", 0)
            checked_out = pool_stats.get("checked_out", 0)
            
            if pool_size == 0:
                return 0.0
                
            return checked_out / pool_size
            
        except Exception:
            return 0.0
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        try:
            if not self.health_history:
                return {"error": "No health data available"}
            
            # Get recent records (last 10 minutes)
            recent_cutoff = datetime.now() - timedelta(minutes=10)
            recent_records = [
                r for r in self.health_history 
                if r["timestamp"] > recent_cutoff
            ]
            
            if not recent_records:
                recent_records = self.health_history[-5:]  # Last 5 records
            
            # Calculate statistics
            healthy_count = sum(1 for r in recent_records if r["healthy"])
            total_count = len(recent_records)
            avg_response_time = sum(r["response_time_ms"] for r in recent_records) / total_count
            
            latest_record = self.health_history[-1]
            
            return {
                "current_status": {
                    "healthy": latest_record["healthy"],
                    "response_time_ms": latest_record["response_time_ms"],
                    "last_check": latest_record["timestamp"].isoformat(),
                    "error": latest_record.get("error")
                },
                "recent_performance": {
                    "health_rate": healthy_count / total_count,
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "total_checks": total_count,
                    "healthy_checks": healthy_count
                },
                "connection_pool": latest_record["pool_stats"],
                "optimization": {
                    "last_optimization": self.last_optimization.isoformat() if self.last_optimization else None,
                    "monitoring_active": self.monitoring_active
                }
            }
            
        except Exception as e:
            logger.error("Failed to generate health summary", exc_info=e)
            return {"error": f"Health summary generation failed: {str(e)}"}
    
    async def force_optimization(self) -> Dict[str, Any]:
        """Force database optimization"""
        try:
            logger.info("Manual database optimization triggered")
            await optimize_connection_pool()
            self.last_optimization = datetime.now()
            
            # Perform immediate health check
            db_result = await test_db_connection()
            
            return {
                "optimization_completed": True,
                "timestamp": self.last_optimization.isoformat(),
                "post_optimization_health": {
                    "healthy": db_result["healthy"],
                    "response_time_ms": db_result["response_time_ms"]
                }
            }
            
        except Exception as e:
            logger.error("Manual optimization failed", exc_info=e)
            return {
                "optimization_completed": False,
                "error": str(e)
            }
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive database diagnostics"""
        try:
            logger.info("Running database diagnostics")
            
            # Test various database operations
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "tests": {}
            }
            
            # Test 1: Basic connectivity
            db_result = await test_db_connection()
            diagnostics["tests"]["connectivity"] = db_result
            
            # Test 2: Connection pool stats
            pool_stats = await get_connection_pool_stats()
            diagnostics["tests"]["connection_pool"] = pool_stats
            
            # Test 3: Transaction performance
            transaction_start = datetime.now()
            try:
                from sqlalchemy import text
                async with get_db_session() as session:
                    await session.execute(text("SELECT pg_sleep(0.1)"))  # 100ms test
                    await session.commit()
                
                transaction_time = (datetime.now() - transaction_start).total_seconds() * 1000
                diagnostics["tests"]["transaction_performance"] = {
                    "success": True,
                    "duration_ms": round(transaction_time, 2)
                }
            except Exception as e:
                diagnostics["tests"]["transaction_performance"] = {
                    "success": False,
                    "error": str(e)
                }
            
            # Test 4: Concurrent connections
            concurrent_start = datetime.now()
            try:
                tasks = []
                for i in range(5):
                    tasks.append(self._test_concurrent_connection())
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful = sum(1 for r in results if r is True)
                
                concurrent_time = (datetime.now() - concurrent_start).total_seconds() * 1000
                diagnostics["tests"]["concurrent_connections"] = {
                    "success": successful == 5,
                    "successful_connections": successful,
                    "total_attempts": 5,
                    "duration_ms": round(concurrent_time, 2)
                }
            except Exception as e:
                diagnostics["tests"]["concurrent_connections"] = {
                    "success": False,
                    "error": str(e)
                }
            
            return diagnostics
            
        except Exception as e:
            logger.error("Database diagnostics failed", exc_info=e)
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"Diagnostics failed: {str(e)}"
            }
    
    async def _test_concurrent_connection(self) -> bool:
        """Test individual concurrent connection"""
        try:
            from sqlalchemy import text
            async with get_db_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

# Global database health monitor instance
db_health_monitor = DatabaseHealthMonitor()
