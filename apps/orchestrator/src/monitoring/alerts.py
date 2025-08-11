"""
Alerting system for SyncCash Orchestrator
"""
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import structlog
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class AlertManager:
    """Manages alerts and notifications for the orchestrator"""
    
    def __init__(self):
        self.alert_rules = self._load_alert_rules()
        self.active_alerts = {}
        self.alert_history = []
    
    def _load_alert_rules(self) -> Dict[str, Dict]:
        """Load alert rules configuration"""
        return {
            "high_error_rate": {
                "condition": "error_rate > 0.05",  # 5% error rate
                "severity": "critical",
                "description": "High error rate detected",
                "cooldown": 300  # 5 minutes
            },
            "payment_processing_slow": {
                "condition": "avg_payment_duration > 30",  # 30 seconds
                "severity": "warning", 
                "description": "Payment processing is slow",
                "cooldown": 600  # 10 minutes
            },
            "database_unhealthy": {
                "condition": "db_health == 'unhealthy'",
                "severity": "critical",
                "description": "Database connection issues",
                "cooldown": 180  # 3 minutes
            },
            "redis_unhealthy": {
                "condition": "redis_health == 'unhealthy'",
                "severity": "critical", 
                "description": "Redis connection issues",
                "cooldown": 180  # 3 minutes
            },
            "fraud_service_down": {
                "condition": "fraud_service_errors > 10",
                "severity": "warning",
                "description": "Fraud detection service issues",
                "cooldown": 300  # 5 minutes
            },
            "high_transaction_volume": {
                "condition": "active_transactions > 1000",
                "severity": "info",
                "description": "High transaction volume detected",
                "cooldown": 1800  # 30 minutes
            }
        }
    
    async def check_alerts(self, system_metrics: Dict[str, Any]):
        """Check all alert conditions and trigger alerts if needed"""
        current_time = datetime.now()
        
        for alert_name, rule in self.alert_rules.items():
            try:
                if self._evaluate_condition(rule["condition"], system_metrics):
                    await self._trigger_alert(alert_name, rule, current_time)
                else:
                    # Clear alert if condition is no longer met
                    if alert_name in self.active_alerts:
                        await self._clear_alert(alert_name, current_time)
                        
            except Exception as e:
                logger.error("Alert evaluation failed", 
                           alert_name=alert_name, 
                           error=str(e))
    
    def _evaluate_condition(self, condition: str, metrics: Dict[str, Any]) -> bool:
        """Evaluate alert condition against current metrics"""
        try:
            # Simple condition evaluation (in production, use proper expression parser)
            if "error_rate >" in condition:
                threshold = float(condition.split(">")[1].strip())
                error_rate = metrics.get("error_rate", 0)
                return error_rate > threshold
            
            elif "avg_payment_duration >" in condition:
                threshold = float(condition.split(">")[1].strip())
                avg_duration = metrics.get("avg_payment_duration", 0)
                return avg_duration > threshold
            
            elif "db_health ==" in condition:
                expected_status = condition.split("==")[1].strip().strip("'\"")
                db_health = metrics.get("db_health", "healthy")
                return db_health == expected_status
            
            elif "redis_health ==" in condition:
                expected_status = condition.split("==")[1].strip().strip("'\"")
                redis_health = metrics.get("redis_health", "healthy")
                return redis_health == expected_status
            
            elif "fraud_service_errors >" in condition:
                threshold = int(condition.split(">")[1].strip())
                fraud_errors = metrics.get("fraud_service_errors", 0)
                return fraud_errors > threshold
            
            elif "active_transactions >" in condition:
                threshold = int(condition.split(">")[1].strip())
                active_txns = metrics.get("active_transactions", 0)
                return active_txns > threshold
            
            return False
            
        except Exception as e:
            logger.error("Condition evaluation error", 
                        condition=condition, 
                        error=str(e))
            return False
    
    async def _trigger_alert(self, alert_name: str, rule: Dict, current_time: datetime):
        """Trigger an alert if not in cooldown period"""
        # Check if alert is in cooldown
        if alert_name in self.active_alerts:
            last_triggered = self.active_alerts[alert_name]["last_triggered"]
            cooldown_period = timedelta(seconds=rule["cooldown"])
            
            if current_time - last_triggered < cooldown_period:
                return  # Still in cooldown
        
        # Create alert
        alert = {
            "name": alert_name,
            "severity": rule["severity"],
            "description": rule["description"],
            "triggered_at": current_time,
            "last_triggered": current_time,
            "count": self.active_alerts.get(alert_name, {}).get("count", 0) + 1
        }
        
        self.active_alerts[alert_name] = alert
        self.alert_history.append(alert.copy())
        
        # Send notification
        await self._send_notification(alert)
        
        logger.warning("Alert triggered", 
                      alert_name=alert_name,
                      severity=rule["severity"],
                      description=rule["description"])
        
        # Record alert metric
        metrics.record_error(
            error_type="alert_triggered",
            component=f"alerting_{alert_name}"
        )
    
    async def _clear_alert(self, alert_name: str, current_time: datetime):
        """Clear an active alert"""
        if alert_name in self.active_alerts:
            alert = self.active_alerts[alert_name]
            alert["cleared_at"] = current_time
            
            logger.info("Alert cleared", 
                       alert_name=alert_name,
                       duration=(current_time - alert["triggered_at"]).total_seconds())
            
            del self.active_alerts[alert_name]
    
    async def _send_notification(self, alert: Dict[str, Any]):
        """Send alert notification (implement actual notification logic)"""
        # TODO: Implement actual notification sending
        # This could be:
        # - Slack webhook
        # - Email notification  
        # - PagerDuty integration
        # - SMS alerts
        # - Discord webhook
        
        logger.info("Alert notification sent", 
                   alert_name=alert["name"],
                   severity=alert["severity"])
        
        # For now, just log the alert
        print(f"🚨 ALERT: {alert['name']} - {alert['description']} [{alert['severity']}]")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        return self.alert_history[-limit:]

# Global alert manager instance
alert_manager = AlertManager()

async def run_alert_checks():
    """Background task to run alert checks periodically"""
    while True:
        try:
            # TODO: Collect actual system metrics
            system_metrics = {
                "error_rate": 0.02,  # 2%
                "avg_payment_duration": 15,  # 15 seconds
                "db_health": "healthy",
                "redis_health": "healthy", 
                "fraud_service_errors": 2,
                "active_transactions": 50
            }
            
            await alert_manager.check_alerts(system_metrics)
            
        except Exception as e:
            logger.error("Alert check failed", exc_info=e)
        
        # Check every 60 seconds
        await asyncio.sleep(60)
