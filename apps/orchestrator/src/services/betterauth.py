"""
BetterAuth Integration Service for SyncCash Orchestrator
Handles JWT validation, user authentication, and session management with BetterAuth
"""
import httpx
import jwt
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog
from functools import lru_cache

from src.config.settings import get_settings
from src.monitoring.metrics import metrics

logger = structlog.get_logger(__name__)

class BetterAuthError(Exception):
    """Base exception for BetterAuth errors"""
    pass

class TokenValidationError(BetterAuthError):
    """Token validation failed"""
    pass

class UserNotFoundError(BetterAuthError):
    """User not found in BetterAuth"""
    pass

class PermissionDeniedError(BetterAuthError):
    """User lacks required permissions"""
    pass

class BetterAuthService:
    """BetterAuth integration service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.betterauth_base_url
        self.api_key = self.settings.betterauth_api_key
        self.jwt_secret = self.settings.betterauth_jwt_secret
        self.jwt_algorithm = self.settings.jwt_algorithm
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(10.0)
        )
        
        # Cache for user permissions and session data
        self._user_cache = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token with BetterAuth and extract user information
        """
        try:
            if not token:
                raise TokenValidationError("Token is required")
            
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
            
            # First, decode and validate JWT locally
            try:
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=[self.jwt_algorithm],
                    options={"verify_exp": True}
                )
            except jwt.ExpiredSignatureError:
                raise TokenValidationError("Token has expired")
            except jwt.InvalidTokenError as e:
                raise TokenValidationError(f"Invalid token: {str(e)}")
            
            user_id = payload.get("sub")
            if not user_id:
                raise TokenValidationError("Token missing user ID")
            
            # Verify token with BetterAuth service
            user_info = await self._verify_token_with_service(token, user_id)
            
            logger.debug("JWT token validated successfully", 
                        user_id=user_id,
                        expires_at=payload.get("exp"))
            
            metrics.increment_counter("betterauth_token_validation_success")
            
            return {
                "valid": True,
                "user_info": user_info,
                "token_payload": payload
            }
            
        except TokenValidationError as e:
            logger.warning("Token validation failed", error=str(e))
            metrics.increment_counter("betterauth_token_validation_failed")
            return {
                "valid": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error("Unexpected error during token validation", exc_info=e)
            metrics.record_error("betterauth_validation_error", "betterauth_service")
            return {
                "valid": False,
                "error": "Token validation failed"
            }
    
    async def _verify_token_with_service(self, token: str, user_id: str) -> Dict[str, Any]:
        """Verify token with BetterAuth service and get user info"""
        try:
            # Check cache first
            cache_key = f"user_{user_id}"
            cached_data = self._user_cache.get(cache_key)
            
            if cached_data and datetime.now() < cached_data["expires_at"]:
                return cached_data["user_info"]
            
            # Call BetterAuth API to verify token and get user info
            response = await self.client.post(
                "/api/auth/verify-token",
                json={"token": token}
            )
            
            if response.status_code == 401:
                raise TokenValidationError("Token is invalid or expired")
            elif response.status_code == 404:
                raise UserNotFoundError(f"User {user_id} not found")
            elif response.status_code != 200:
                raise BetterAuthError(f"BetterAuth API error: {response.status_code}")
            
            data = response.json()
            user_info = {
                "user_id": data["user"]["id"],
                "email": data["user"]["email"],
                "name": data["user"]["name"],
                "roles": data["user"].get("roles", []),
                "permissions": data["user"].get("permissions", []),
                "is_verified": data["user"].get("emailVerified", False),
                "is_active": data["user"].get("active", True),
                "session_id": data.get("sessionId"),
                "expires_at": datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))
            }
            
            # Cache user info
            self._user_cache[cache_key] = {
                "user_info": user_info,
                "expires_at": datetime.now() + self._cache_ttl
            }
            
            return user_info
            
        except httpx.RequestError as e:
            logger.error("Failed to connect to BetterAuth service", error=str(e))
            raise BetterAuthError("Authentication service unavailable")
    
    async def check_user_permissions(self, user_id: str, required_permissions: List[str]) -> bool:
        """Check if user has required permissions"""
        try:
            cache_key = f"user_{user_id}"
            cached_data = self._user_cache.get(cache_key)
            
            if not cached_data or datetime.now() >= cached_data["expires_at"]:
                # Need to refresh user data
                response = await self.client.get(f"/api/users/{user_id}")
                
                if response.status_code == 404:
                    raise UserNotFoundError(f"User {user_id} not found")
                elif response.status_code != 200:
                    raise BetterAuthError(f"Failed to get user permissions: {response.status_code}")
                
                data = response.json()
                user_permissions = data.get("permissions", [])
                
                # Update cache
                self._user_cache[cache_key] = {
                    "user_info": {"permissions": user_permissions},
                    "expires_at": datetime.now() + self._cache_ttl
                }
            else:
                user_permissions = cached_data["user_info"].get("permissions", [])
            
            # Check if user has all required permissions
            has_permissions = all(perm in user_permissions for perm in required_permissions)
            
            logger.debug("Permission check completed",
                        user_id=user_id,
                        required_permissions=required_permissions,
                        user_permissions=user_permissions,
                        has_permissions=has_permissions)
            
            return has_permissions
            
        except Exception as e:
            logger.error("Permission check failed", user_id=user_id, error=str(e))
            return False
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed user information from BetterAuth"""
        try:
            cache_key = f"user_{user_id}"
            cached_data = self._user_cache.get(cache_key)
            
            if cached_data and datetime.now() < cached_data["expires_at"]:
                return cached_data["user_info"]
            
            response = await self.client.get(f"/api/users/{user_id}")
            
            if response.status_code == 404:
                return None
            elif response.status_code != 200:
                raise BetterAuthError(f"Failed to get user info: {response.status_code}")
            
            data = response.json()
            user_info = {
                "user_id": data["id"],
                "email": data["email"],
                "name": data["name"],
                "roles": data.get("roles", []),
                "permissions": data.get("permissions", []),
                "is_verified": data.get("emailVerified", False),
                "is_active": data.get("active", True),
                "created_at": data.get("createdAt"),
                "last_login": data.get("lastLogin")
            }
            
            # Cache user info
            self._user_cache[cache_key] = {
                "user_info": user_info,
                "expires_at": datetime.now() + self._cache_ttl
            }
            
            return user_info
            
        except Exception as e:
            logger.error("Failed to get user info", user_id=user_id, error=str(e))
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session in BetterAuth"""
        try:
            response = await self.client.post(
                "/api/auth/logout",
                json={"sessionId": session_id}
            )
            
            success = response.status_code == 200
            
            if success:
                logger.info("Session invalidated successfully", session_id=session_id)
                # Clear relevant cache entries
                self._clear_user_cache_by_session(session_id)
            else:
                logger.warning("Failed to invalidate session", 
                             session_id=session_id,
                             status_code=response.status_code)
            
            return success
            
        except Exception as e:
            logger.error("Session invalidation failed", session_id=session_id, error=str(e))
            return False
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh JWT token using refresh token"""
        try:
            response = await self.client.post(
                "/api/auth/refresh",
                json={"refreshToken": refresh_token}
            )
            
            if response.status_code != 200:
                logger.warning("Token refresh failed", status_code=response.status_code)
                return None
            
            data = response.json()
            
            logger.info("Token refreshed successfully")
            metrics.increment_counter("betterauth_token_refresh_success")
            
            return {
                "access_token": data["accessToken"],
                "refresh_token": data.get("refreshToken"),
                "expires_in": data.get("expiresIn"),
                "token_type": data.get("tokenType", "Bearer")
            }
            
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            metrics.increment_counter("betterauth_token_refresh_failed")
            return None
    
    def _clear_user_cache_by_session(self, session_id: str):
        """Clear cache entries for a specific session"""
        keys_to_remove = []
        for key, data in self._user_cache.items():
            if data.get("user_info", {}).get("session_id") == session_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._user_cache[key]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check BetterAuth service health"""
        try:
            response = await self.client.get("/api/health")
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "service": "betterauth"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "service": "betterauth"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "betterauth"
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

# Global BetterAuth service instance
@lru_cache()
def get_betterauth_service() -> BetterAuthService:
    """Get cached BetterAuth service instance"""
    return BetterAuthService()
