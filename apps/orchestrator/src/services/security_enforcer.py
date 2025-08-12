"""
Security Enforcement Service for SyncCash Orchestrator
Handles MFA, JWT validation, input sanitization, and security policies
"""
import re
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import structlog

from src.monitoring.metrics import metrics
from src.services.betterauth import get_betterauth_service, BetterAuthError, TokenValidationError, PermissionDeniedError

logger = structlog.get_logger(__name__)

class SecurityPolicy:
    """Security policy configuration"""
    
    def __init__(self):
        # MFA requirements
        self.mfa_required_amount = Decimal("5000.00")  # Require MFA for amounts above this
        self.mfa_required_operations = ["refund", "large_payment", "account_change"]
        
        # Rate limiting
        self.rate_limits = {
            "payment_requests": {"count": 10, "window_minutes": 5},
            "refund_requests": {"count": 3, "window_minutes": 60},
            "status_queries": {"count": 100, "window_minutes": 5}
        }
        
        # Input validation patterns
        self.validation_patterns = {
            "phone_number": r"^(\+233|0)[2-9]\d{8}$",  # Ghana phone numbers
            "amount": r"^\d+(\.\d{1,2})?$",
            "user_id": r"^[a-zA-Z0-9_-]{3,50}$",
            "transaction_id": r"^[a-f0-9-]{36}$"  # UUID format
        }
        
        # Suspicious activity thresholds
        self.suspicious_thresholds = {
            "rapid_transactions": {"count": 5, "window_minutes": 2},
            "large_amount_sequence": {"amount": Decimal("10000.00"), "count": 3},
            "failed_attempts": {"count": 5, "window_minutes": 10}
        }

class SecurityEnforcer:
    """Enforces security policies and validates requests"""
    
    def __init__(self):
        self.policy = SecurityPolicy()
        self.active_sessions = {}  # Track active user sessions
        self.rate_limit_tracking = {}  # Track rate limiting per user
        self.suspicious_activity = {}  # Track suspicious activity
        self.betterauth = get_betterauth_service()
    
    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token with BetterAuth and extract user information
        """
        try:
            # Use BetterAuth service for token validation
            result = await self.betterauth.validate_jwt_token(token)
            
            if not result["valid"]:
                logger.warning("JWT token validation failed", error=result.get("error"))
                return result
            
            user_info = result["user_info"]
            user_id = user_info["user_id"]
            
            # Update active sessions tracking
            self.active_sessions[user_id] = {
                "session_id": user_info.get("session_id"),
                "last_activity": datetime.now(),
                "permissions": user_info.get("permissions", []),
                "is_verified": user_info.get("is_verified", False)
            }
            
            logger.debug("JWT token validated successfully", 
                        user_id=user_id,
                        is_verified=user_info.get("is_verified"),
                        permissions_count=len(user_info.get("permissions", [])))
            
            return result
            
        except TokenValidationError as e:
            logger.warning("Token validation error", error=str(e))
            metrics.record_error("jwt_validation_error", "security_enforcer")
            return {
                "valid": False,
                "error": str(e)
            }
        except BetterAuthError as e:
            logger.error("BetterAuth service error", error=str(e))
            metrics.record_error("betterauth_service_error", "security_enforcer")
            return {
                "valid": False,
                "error": "Authentication service error"
            }
        except Exception as e:
            logger.error("Unexpected JWT validation error", exc_info=e)
            metrics.record_error("jwt_validation_unexpected_error", "security_enforcer")
            return {
                "valid": False,
                "error": "Token validation failed"
            }
    
    async def check_mfa_requirement(
        self,
        user_id: str,
        operation: str,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Check if MFA is required for the operation"""
        
        try:
            requires_mfa = False
            reason = None
            
            # Check operation type
            if operation in self.policy.mfa_required_operations:
                requires_mfa = True
                reason = f"MFA required for {operation} operations"
            
            # Check amount threshold
            if amount and amount >= self.policy.mfa_required_amount:
                requires_mfa = True
                reason = f"MFA required for amounts above {self.policy.mfa_required_amount}"
            
            # Check user risk profile (TODO: implement risk scoring)
            user_risk = await self._get_user_risk_score(user_id)
            if user_risk > 0.7:  # High risk user
                requires_mfa = True
                reason = "MFA required due to high risk profile"
            
            return {
                "requires_mfa": requires_mfa,
                "reason": reason,
                "user_risk_score": user_risk
            }
            
        except Exception as e:
            logger.error("MFA requirement check failed", exc_info=e)
            # Default to requiring MFA on error for security
            return {
                "requires_mfa": True,
                "reason": "MFA required due to security check failure"
            }
    
    async def check_user_permissions(self, user_id: str, required_permissions: List[str]) -> Dict[str, Any]:
        """
        Check if user has required permissions using BetterAuth
        """
        try:
            has_permissions = await self.betterauth.check_user_permissions(user_id, required_permissions)
            
            if not has_permissions:
                logger.warning("User lacks required permissions",
                             user_id=user_id,
                             required_permissions=required_permissions)
                
                await self.log_security_event(
                    "permission_denied",
                    user_id,
                    {"required_permissions": required_permissions},
                    "WARNING"
                )
                
                return {
                    "authorized": False,
                    "error": "Insufficient permissions",
                    "required_permissions": required_permissions
                }
            
            logger.debug("Permission check passed", 
                        user_id=user_id,
                        permissions=required_permissions)
            
            return {"authorized": True}
            
        except Exception as e:
            logger.error("Permission check failed", user_id=user_id, error=str(e))
            return {
                "authorized": False,
                "error": "Permission check failed"
            }

    async def validate_mfa_token(self, user_id: str, mfa_token: str) -> Dict[str, Any]:
        """
        Validate MFA token (TOTP, SMS, etc.)
        TODO: Integrate with actual MFA provider
        """
        try:
            # TODO: Implement actual MFA validation
            # For now, simulate MFA validation
            
            # In production, this would validate TOTP, SMS codes, etc.
            is_valid = len(mfa_token) == 6 and mfa_token.isdigit()
            
            if is_valid:
                logger.info("MFA token validated successfully", user_id=user_id)
                return {"valid": True}
            else:
                logger.warning("Invalid MFA token", user_id=user_id)
                return {"valid": False, "error": "Invalid MFA token"}
                
        except Exception as e:
            logger.error("MFA validation failed", user_id=user_id, exc_info=e)
            return {"valid": False, "error": "MFA validation failed"}
    
    def sanitize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data to prevent injection attacks"""
        
        sanitized = {}
        
        for key, value in input_data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = re.sub(r'[<>"\';\\]', '', value)
                sanitized_value = sanitized_value.strip()
                sanitized[key] = sanitized_value
            elif isinstance(value, (int, float, Decimal)):
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_input(value)
            else:
                sanitized[key] = str(value)
        
        return sanitized
    
    def validate_input_format(self, field_name: str, value: str) -> bool:
        """Validate input format against defined patterns"""
        
        pattern = self.policy.validation_patterns.get(field_name)
        if not pattern:
            return True  # No validation pattern defined
        
        return bool(re.match(pattern, str(value)))
    
    async def check_rate_limit(self, user_id: str, operation: str) -> Dict[str, Any]:
        """Check if user has exceeded rate limits"""
        
        try:
            limit_config = self.policy.rate_limits.get(operation)
            if not limit_config:
                return {"allowed": True}
            
            current_time = datetime.now()
            window_start = current_time - timedelta(minutes=limit_config["window_minutes"])
            
            # Initialize tracking if not exists
            if user_id not in self.rate_limit_tracking:
                self.rate_limit_tracking[user_id] = {}
            
            if operation not in self.rate_limit_tracking[user_id]:
                self.rate_limit_tracking[user_id][operation] = []
            
            # Clean old entries
            user_operations = self.rate_limit_tracking[user_id][operation]
            user_operations[:] = [
                timestamp for timestamp in user_operations 
                if timestamp > window_start
            ]
            
            # Check limit
            if len(user_operations) >= limit_config["count"]:
                logger.warning("Rate limit exceeded",
                              user_id=user_id,
                              operation=operation,
                              count=len(user_operations),
                              limit=limit_config["count"])
                
                metrics.record_error("rate_limit_exceeded", "security_enforcer")
                
                return {
                    "allowed": False,
                    "reason": f"Rate limit exceeded: {limit_config['count']} {operation} per {limit_config['window_minutes']} minutes",
                    "retry_after_minutes": limit_config["window_minutes"]
                }
            
            # Record this operation
            user_operations.append(current_time)
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error("Rate limit check failed", exc_info=e)
            return {"allowed": True}  # Allow on error to avoid blocking legitimate users
    
    async def detect_suspicious_activity(
        self,
        user_id: str,
        operation: str,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Detect suspicious activity patterns"""
        
        try:
            current_time = datetime.now()
            
            # Initialize tracking
            if user_id not in self.suspicious_activity:
                self.suspicious_activity[user_id] = {
                    "transactions": [],
                    "failed_attempts": [],
                    "large_amounts": []
                }
            
            user_activity = self.suspicious_activity[user_id]
            
            # Check rapid transactions
            recent_window = current_time - timedelta(
                minutes=self.policy.suspicious_thresholds["rapid_transactions"]["window_minutes"]
            )
            
            recent_transactions = [
                t for t in user_activity["transactions"] 
                if t["timestamp"] > recent_window
            ]
            
            if len(recent_transactions) >= self.policy.suspicious_thresholds["rapid_transactions"]["count"]:
                logger.warning("Suspicious rapid transactions detected",
                              user_id=user_id,
                              transaction_count=len(recent_transactions))
                
                return {
                    "suspicious": True,
                    "reason": "Rapid transaction pattern detected",
                    "risk_level": "HIGH"
                }
            
            # Check large amount sequences
            if amount and amount >= self.policy.suspicious_thresholds["large_amount_sequence"]["amount"]:
                user_activity["large_amounts"].append({
                    "amount": amount,
                    "timestamp": current_time
                })
                
                # Clean old entries
                user_activity["large_amounts"] = [
                    entry for entry in user_activity["large_amounts"]
                    if entry["timestamp"] > recent_window
                ]
                
                if len(user_activity["large_amounts"]) >= self.policy.suspicious_thresholds["large_amount_sequence"]["count"]:
                    return {
                        "suspicious": True,
                        "reason": "Multiple large amount transactions",
                        "risk_level": "MEDIUM"
                    }
            
            # Record current transaction
            user_activity["transactions"].append({
                "operation": operation,
                "amount": amount,
                "timestamp": current_time
            })
            
            # Clean old transactions
            user_activity["transactions"] = [
                t for t in user_activity["transactions"]
                if t["timestamp"] > recent_window
            ]
            
            return {"suspicious": False}
            
        except Exception as e:
            logger.error("Suspicious activity detection failed", exc_info=e)
            return {"suspicious": False}
    
    async def _get_user_risk_score(self, user_id: str) -> float:
        """
        Get user risk score (0.0 = low risk, 1.0 = high risk)
        TODO: Integrate with actual risk scoring service
        """
        try:
            # TODO: Implement actual risk scoring
            # This could consider:
            # - Transaction history
            # - Account age
            # - Verification status
            # - Previous fraud incidents
            # - Device fingerprinting
            
            # For now, return a default low risk score
            return 0.2
            
        except Exception as e:
            logger.error("Risk score calculation failed", exc_info=e)
            return 0.5  # Default to medium risk on error
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data using SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def invalidate_user_session(self, user_id: str) -> Dict[str, Any]:
        """
        Invalidate user session in BetterAuth and local tracking
        """
        try:
            session_info = self.active_sessions.get(user_id)
            if not session_info:
                return {
                    "success": False,
                    "error": "No active session found"
                }
            
            session_id = session_info.get("session_id")
            if session_id:
                # Invalidate session in BetterAuth
                success = await self.betterauth.invalidate_session(session_id)
                if not success:
                    logger.warning("Failed to invalidate session in BetterAuth", 
                                 user_id=user_id, session_id=session_id)
            
            # Remove from local tracking
            del self.active_sessions[user_id]
            
            logger.info("User session invalidated", user_id=user_id)
            
            await self.log_security_event(
                "session_invalidated",
                user_id,
                {"session_id": session_id},
                "INFO"
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error("Session invalidation failed", user_id=user_id, error=str(e))
            return {
                "success": False,
                "error": "Session invalidation failed"
            }
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed user information from BetterAuth
        """
        try:
            user_info = await self.betterauth.get_user_info(user_id)
            
            if user_info:
                logger.debug("User info retrieved", user_id=user_id)
            else:
                logger.warning("User not found", user_id=user_id)
            
            return user_info
            
        except Exception as e:
            logger.error("Failed to get user info", user_id=user_id, error=str(e))
            return None
    
    async def refresh_user_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh user JWT token using refresh token
        """
        try:
            token_data = await self.betterauth.refresh_token(refresh_token)
            
            if token_data:
                logger.info("Token refreshed successfully")
            else:
                logger.warning("Token refresh failed")
            
            return token_data
            
        except Exception as e:
            logger.error("Token refresh error", error=str(e))
            return None

    async def log_security_event(
        self,
        event_type: str,
        user_id: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ):
        """Log security events for audit trail"""
        
        security_event = {
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "details": details
        }
        
        logger.info("Security event logged",
                   event_type=event_type,
                   user_id=user_id,
                   severity=severity)
        
        # TODO: Send to security monitoring system
        # This could be SIEM, security dashboard, or alert system
        
        metrics.record_error(f"security_event_{event_type.lower()}", "security_enforcer")

# Global security enforcer instance
security_enforcer = SecurityEnforcer()
