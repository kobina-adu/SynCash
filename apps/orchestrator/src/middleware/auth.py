"""
Authentication Middleware for SyncCash Orchestrator
Integrates BetterAuth JWT validation with FastAPI
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
import structlog

from src.services.security_enforcer import security_enforcer
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

class AuthenticationError(HTTPException):
    """Authentication failed exception"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(HTTPException):
    """Authorization failed exception"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        token = credentials.credentials
        
        # Validate token with BetterAuth
        result = await security_enforcer.validate_jwt_token(token)
        
        if not result["valid"]:
            logger.warning("Token validation failed", error=result.get("error"))
            metrics.increment_counter("auth_token_validation_failed")
            raise AuthenticationError(result.get("error", "Invalid token"))
        
        user_info = result["user_info"]
        
        # Check if user account is active and verified for sensitive operations
        if not user_info.get("is_active", True):
            logger.warning("Inactive user attempted access", user_id=user_info["user_id"])
            raise AuthenticationError("Account is inactive")
        
        logger.debug("User authenticated successfully", user_id=user_info["user_id"])
        metrics.increment_counter("auth_token_validation_success")
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication error", exc_info=e)
        metrics.record_error("auth_unexpected_error", "auth_middleware")
        raise AuthenticationError("Authentication failed")

async def get_verified_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to get current user that must be email verified
    """
    if not current_user.get("is_verified", False):
        logger.warning("Unverified user attempted verified operation", 
                      user_id=current_user["user_id"])
        raise AuthenticationError("Email verification required")
    
    return current_user

def require_permissions(required_permissions: List[str]):
    """
    Dependency factory to check if user has required permissions
    """
    async def check_permissions(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_id = current_user["user_id"]
        
        try:
            # Check permissions with BetterAuth
            permission_result = await security_enforcer.check_user_permissions(
                user_id, required_permissions
            )
            
            if not permission_result["authorized"]:
                logger.warning("Permission denied", 
                             user_id=user_id,
                             required_permissions=required_permissions)
                metrics.increment_counter("auth_permission_denied")
                raise AuthorizationError(
                    f"Required permissions: {', '.join(required_permissions)}"
                )
            
            logger.debug("Permission check passed", 
                        user_id=user_id,
                        permissions=required_permissions)
            metrics.increment_counter("auth_permission_granted")
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Permission check error", user_id=user_id, exc_info=e)
            metrics.record_error("auth_permission_check_error", "auth_middleware")
            raise AuthorizationError("Permission check failed")
    
    return check_permissions

def require_mfa_for_amount(amount_threshold: float = 5000.0):
    """
    Dependency factory to require MFA for operations above amount threshold
    """
    async def check_mfa_requirement(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_verified_user)
    ) -> Dict[str, Any]:
        user_id = current_user["user_id"]
        
        try:
            # Get amount from request body if present
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.json() if hasattr(request, '_body') else {}
                amount = body.get("amount", 0)
                
                if amount >= amount_threshold:
                    # Check if MFA token is provided
                    mfa_token = request.headers.get("X-MFA-Token")
                    
                    if not mfa_token:
                        logger.warning("MFA required but not provided", 
                                     user_id=user_id, amount=amount)
                        raise AuthenticationError(
                            f"MFA required for amounts above {amount_threshold}"
                        )
                    
                    # Validate MFA token
                    mfa_result = await security_enforcer.validate_mfa_token(
                        user_id, mfa_token
                    )
                    
                    if not mfa_result["valid"]:
                        logger.warning("Invalid MFA token", user_id=user_id)
                        raise AuthenticationError("Invalid MFA token")
                    
                    logger.info("MFA validation passed", user_id=user_id, amount=amount)
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("MFA check error", user_id=user_id, exc_info=e)
            raise AuthenticationError("MFA validation failed")
    
    return check_mfa_requirement

async def get_optional_user(
    request: Request
) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current user if token is provided (optional authentication)
    """
    try:
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        result = await security_enforcer.validate_jwt_token(token)
        
        if result["valid"]:
            return result["user_info"]
        else:
            logger.debug("Optional auth failed", error=result.get("error"))
            return None
            
    except Exception as e:
        logger.debug("Optional auth error", exc_info=e)
        return None

# Common permission sets
class Permissions:
    """Common permission constants"""
    PAYMENT_INITIATE = ["payment:initiate"]
    PAYMENT_REFUND = ["payment:refund"]
    PAYMENT_STATUS = ["payment:status"]
    PAYMENT_ADMIN = ["payment:admin"]
    SYSTEM_ADMIN = ["system:admin"]
    USER_MANAGE = ["user:manage"]

# Common dependency combinations
RequirePaymentAccess = require_permissions(Permissions.PAYMENT_INITIATE)
RequireRefundAccess = require_permissions(Permissions.PAYMENT_REFUND)
RequireAdminAccess = require_permissions(Permissions.SYSTEM_ADMIN)
RequireMFAForLargePayments = require_mfa_for_amount(5000.0)
