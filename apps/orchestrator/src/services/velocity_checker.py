"""
Velocity Checks Service for SyncCash Orchestrator
Implements transaction velocity monitoring and limits
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

from src.core.database import get_db_session
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class VelocityLimits:
    """Velocity limit configurations"""
    
    def __init__(self):
        # Transaction count limits
        self.transaction_limits = {
            "per_minute": 5,
            "per_hour": 50,
            "per_day": 200
        }
        
        # Amount limits (in GHS)
        self.amount_limits = {
            "per_hour": Decimal("10000.00"),
            "per_day": Decimal("50000.00"),
            "per_week": Decimal("200000.00")
        }
        
        # Provider-specific limits
        self.provider_limits = {
            "MTN_MOMO": {
                "daily_amount": Decimal("20000.00"),
                "daily_count": 100
            },
            "AIRTELTIGO": {
                "daily_amount": Decimal("15000.00"),
                "daily_count": 80
            },
            "VODAFONE": {
                "daily_amount": Decimal("18000.00"),
                "daily_count": 90
            }
        }

class VelocityChecker:
    """Monitors and enforces transaction velocity limits"""
    
    def __init__(self):
        self.limits = VelocityLimits()
        self.user_activity_cache = defaultdict(list)
    
    async def check_velocity_limits(
        self,
        user_id: str,
        amount: Decimal,
        provider: str = None
    ) -> Dict[str, Any]:
        """Check if transaction violates velocity limits"""
        
        try:
            current_time = datetime.now()
            
            # Get user transaction history
            user_history = await self._get_user_transaction_history(user_id)
            
            # Check transaction count limits
            count_check = self._check_transaction_count_limits(user_history, current_time)
            if not count_check["allowed"]:
                return count_check
            
            # Check amount limits
            amount_check = self._check_amount_limits(user_history, current_time, amount)
            if not amount_check["allowed"]:
                return amount_check
            
            # Check provider-specific limits
            if provider:
                provider_check = self._check_provider_limits(user_history, current_time, amount, provider)
                if not provider_check["allowed"]:
                    return provider_check
            
            return {"allowed": True, "message": "Velocity checks passed"}
            
        except Exception as e:
            logger.error("Velocity check failed", exc_info=e, user_id=user_id)
            metrics.record_error("velocity_check_error", "velocity_checker")
            
            # Default to allowing transaction on error
            return {"allowed": True, "message": "Velocity check unavailable"}
    
    def _check_transaction_count_limits(
        self,
        user_history: List[Dict],
        current_time: datetime
    ) -> Dict[str, Any]:
        """Check transaction count velocity limits"""
        
        # Check per-minute limit
        minute_ago = current_time - timedelta(minutes=1)
        recent_minute = [t for t in user_history if t["created_at"] > minute_ago]
        
        if len(recent_minute) >= self.limits.transaction_limits["per_minute"]:
            return {
                "allowed": False,
                "reason": f"Exceeded {self.limits.transaction_limits['per_minute']} transactions per minute",
                "limit_type": "transaction_count_minute"
            }
        
        # Check per-hour limit
        hour_ago = current_time - timedelta(hours=1)
        recent_hour = [t for t in user_history if t["created_at"] > hour_ago]
        
        if len(recent_hour) >= self.limits.transaction_limits["per_hour"]:
            return {
                "allowed": False,
                "reason": f"Exceeded {self.limits.transaction_limits['per_hour']} transactions per hour",
                "limit_type": "transaction_count_hour"
            }
        
        # Check per-day limit
        day_ago = current_time - timedelta(days=1)
        recent_day = [t for t in user_history if t["created_at"] > day_ago]
        
        if len(recent_day) >= self.limits.transaction_limits["per_day"]:
            return {
                "allowed": False,
                "reason": f"Exceeded {self.limits.transaction_limits['per_day']} transactions per day",
                "limit_type": "transaction_count_day"
            }
        
        return {"allowed": True}
    
    def _check_amount_limits(
        self,
        user_history: List[Dict],
        current_time: datetime,
        new_amount: Decimal
    ) -> Dict[str, Any]:
        """Check amount velocity limits"""
        
        # Check per-hour amount limit
        hour_ago = current_time - timedelta(hours=1)
        recent_hour = [t for t in user_history if t["created_at"] > hour_ago]
        hour_total = sum(Decimal(str(t["amount"])) for t in recent_hour)
        
        if hour_total + new_amount > self.limits.amount_limits["per_hour"]:
            return {
                "allowed": False,
                "reason": f"Would exceed {self.limits.amount_limits['per_hour']} GHS per hour limit",
                "current_total": float(hour_total),
                "limit_type": "amount_hour"
            }
        
        # Check per-day amount limit
        day_ago = current_time - timedelta(days=1)
        recent_day = [t for t in user_history if t["created_at"] > day_ago]
        day_total = sum(Decimal(str(t["amount"])) for t in recent_day)
        
        if day_total + new_amount > self.limits.amount_limits["per_day"]:
            return {
                "allowed": False,
                "reason": f"Would exceed {self.limits.amount_limits['per_day']} GHS per day limit",
                "current_total": float(day_total),
                "limit_type": "amount_day"
            }
        
        # Check per-week amount limit
        week_ago = current_time - timedelta(weeks=1)
        recent_week = [t for t in user_history if t["created_at"] > week_ago]
        week_total = sum(Decimal(str(t["amount"])) for t in recent_week)
        
        if week_total + new_amount > self.limits.amount_limits["per_week"]:
            return {
                "allowed": False,
                "reason": f"Would exceed {self.limits.amount_limits['per_week']} GHS per week limit",
                "current_total": float(week_total),
                "limit_type": "amount_week"
            }
        
        return {"allowed": True}
    
    def _check_provider_limits(
        self,
        user_history: List[Dict],
        current_time: datetime,
        new_amount: Decimal,
        provider: str
    ) -> Dict[str, Any]:
        """Check provider-specific velocity limits"""
        
        provider_config = self.limits.provider_limits.get(provider)
        if not provider_config:
            return {"allowed": True}
        
        # Filter transactions for this provider
        day_ago = current_time - timedelta(days=1)
        provider_transactions = [
            t for t in user_history 
            if t["created_at"] > day_ago and t.get("provider") == provider
        ]
        
        # Check daily count limit
        if len(provider_transactions) >= provider_config["daily_count"]:
            return {
                "allowed": False,
                "reason": f"Exceeded {provider_config['daily_count']} daily transactions for {provider}",
                "limit_type": f"provider_count_{provider}"
            }
        
        # Check daily amount limit
        provider_total = sum(Decimal(str(t["amount"])) for t in provider_transactions)
        if provider_total + new_amount > provider_config["daily_amount"]:
            return {
                "allowed": False,
                "reason": f"Would exceed {provider_config['daily_amount']} GHS daily limit for {provider}",
                "current_total": float(provider_total),
                "limit_type": f"provider_amount_{provider}"
            }
        
        return {"allowed": True}
    
    async def _get_user_transaction_history(self, user_id: str) -> List[Dict]:
        """Get user transaction history for velocity checking"""
        
        try:
            # Look back 7 days for comprehensive velocity checking
            lookback_date = datetime.now() - timedelta(days=7)
            
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT id, amount, provider, created_at, status
                    FROM transactions 
                    WHERE user_id = :user_id 
                    AND created_at > :lookback_date
                    AND status IN ('confirmed', 'pending', 'initiated')
                    ORDER BY created_at DESC
                    """,
                    {
                        "user_id": user_id,
                        "lookback_date": lookback_date
                    }
                )
                
                transactions = []
                for row in result:
                    transactions.append({
                        "id": row[0],
                        "amount": row[1],
                        "provider": row[2],
                        "created_at": row[3],
                        "status": row[4]
                    })
                
                return transactions
                
        except Exception as e:
            logger.error("Failed to get user transaction history", exc_info=e, user_id=user_id)
            return []
    
    async def get_user_velocity_status(self, user_id: str) -> Dict[str, Any]:
        """Get current velocity status for user"""
        
        try:
            current_time = datetime.now()
            user_history = await self._get_user_transaction_history(user_id)
            
            # Calculate current usage
            hour_ago = current_time - timedelta(hours=1)
            day_ago = current_time - timedelta(days=1)
            week_ago = current_time - timedelta(weeks=1)
            
            hour_transactions = [t for t in user_history if t["created_at"] > hour_ago]
            day_transactions = [t for t in user_history if t["created_at"] > day_ago]
            week_transactions = [t for t in user_history if t["created_at"] > week_ago]
            
            hour_amount = sum(Decimal(str(t["amount"])) for t in hour_transactions)
            day_amount = sum(Decimal(str(t["amount"])) for t in day_transactions)
            week_amount = sum(Decimal(str(t["amount"])) for t in week_transactions)
            
            return {
                "current_usage": {
                    "hour": {
                        "count": len(hour_transactions),
                        "amount": float(hour_amount),
                        "count_limit": self.limits.transaction_limits["per_hour"],
                        "amount_limit": float(self.limits.amount_limits["per_hour"])
                    },
                    "day": {
                        "count": len(day_transactions),
                        "amount": float(day_amount),
                        "count_limit": self.limits.transaction_limits["per_day"],
                        "amount_limit": float(self.limits.amount_limits["per_day"])
                    },
                    "week": {
                        "count": len(week_transactions),
                        "amount": float(week_amount),
                        "amount_limit": float(self.limits.amount_limits["per_week"])
                    }
                },
                "remaining_capacity": {
                    "hour_count": max(0, self.limits.transaction_limits["per_hour"] - len(hour_transactions)),
                    "hour_amount": float(max(0, self.limits.amount_limits["per_hour"] - hour_amount)),
                    "day_count": max(0, self.limits.transaction_limits["per_day"] - len(day_transactions)),
                    "day_amount": float(max(0, self.limits.amount_limits["per_day"] - day_amount))
                }
            }
            
        except Exception as e:
            logger.error("Failed to get velocity status", exc_info=e, user_id=user_id)
            return {"error": "Unable to retrieve velocity status"}

# Global velocity checker instance
velocity_checker = VelocityChecker()
