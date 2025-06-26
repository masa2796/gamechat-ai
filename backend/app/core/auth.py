"""
Enhanced API authentication and authorization module.
"""
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import logging
from .log_security import security_audit_logger

logger = logging.getLogger(__name__)

# JWT imports with fallback
try:
    from jose import JWTError, jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    JWTError = Exception  # Fallback exception type
    jwt = None
    logger.warning("python-jose not available, JWT authentication disabled")

# Password hashing imports with fallback
try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    CryptContext = None
    logger.warning("passlib not available, password hashing disabled")

class APIKeyAuth:
    """API Key based authentication."""
    
    def __init__(self) -> None:
        self.api_keys = self._load_api_keys()
        self.api_key_usage: Dict[str, List[float]] = {}  # Track API key usage
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from environment variables."""
        api_keys = {}
        
        is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        environment = os.getenv("ENVIRONMENT", "development")
        
        if is_test_mode:
            logger.info("Test mode detected, using test API keys")
        
        key_configs = {
            "API_KEY_PRODUCTION": {"name": "production", "rate_limit": 1000, "permissions": ["read", "write"]},
            "API_KEY_DEVELOPMENT": {"name": "development", "rate_limit": 100, "permissions": ["read", "write"]},
            "API_KEY_READONLY": {"name": "readonly", "rate_limit": 500, "permissions": ["read"]},
            "API_KEY_FRONTEND": {"name": "frontend", "rate_limit": 200, "permissions": ["read"]},
        }

        for env_var, config in key_configs.items():
            key_value = os.getenv(env_var)
            if key_value:
                # Secret Managerからの改行文字を除去
                key_value = key_value.strip()
                logger.info(f"{config['name'].capitalize()} API key loaded: ***MASKED*** (type: {config['name']})")
                api_keys[key_value] = {
                    **config,
                    "created_at": datetime.now().isoformat()
                }
            else:
                # 環境に応じたログ出力
                is_required = (
                    (env_var == "API_KEY_PRODUCTION" and environment == "production") or
                    (env_var == "API_KEY_DEVELOPMENT" and environment == "development")
                )
                if is_required and not is_test_mode:
                    logger.warning(f"{config['name'].capitalize()} API key not found in environment variables, but it might be required.")
                else:
                    logger.info(f"{config['name'].capitalize()} API key not configured (optional or not required in this env)")
        
        logger.info(f"Total API keys loaded: {len(api_keys)}")
        return api_keys
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return key info."""
        logger.info("Verifying API key: ***MASKED***")
        logger.info(f"Available API keys count: {len(self.api_keys)}")
        
        if api_key in self.api_keys:
            key_info = self.api_keys[api_key]
            logger.info(f"API key verified successfully: {key_info['name']}")
            
            # Track usage
            current_time = time.time()
            if api_key not in self.api_key_usage:
                self.api_key_usage[api_key] = []
            
            # Clean old usage records (older than 1 hour)
            self.api_key_usage[api_key] = [
                timestamp for timestamp in self.api_key_usage[api_key]
                if current_time - float(timestamp) < 3600
            ]
            
            # Check rate limit
            current_usage = len(self.api_key_usage[api_key])
            rate_limit = key_info["rate_limit"]
            logger.info(f"Rate limit check: {current_usage}/{rate_limit}")
            
            if current_usage >= rate_limit:
                logger.warning(f"Rate limit exceeded for API key: {key_info['name']}")
                return None
            
            # Record usage
            self.api_key_usage[api_key].append(current_time)
            logger.info(f"API key verification successful: {key_info['name']}")
            
            return key_info
        
        logger.warning("API key verification failed: not found in available keys")
        return None

class JWTAuth:
    """JWT based authentication."""
    
    def __init__(self) -> None:
        self.secret_key = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        if PASSLIB_AVAILABLE and CryptContext:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        else:
            self.pwd_context = None
    
    def _generate_secret_key(self) -> str:
        """Generate a secret key if not provided."""
        is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        if is_test_mode:
            logger.info("Using test JWT secret key")
            return "test-jwt-secret-key-for-testing-only"
        else:
            logger.warning("JWT_SECRET_KEY not set, generating random key")
            return secrets.token_urlsafe(32)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if not JWT_AVAILABLE or not jwt:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT authentication not available"
            )
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt: str = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        if not JWT_AVAILABLE or not jwt:
            return None
        
        try:
            payload: Dict[str, Any] = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

class EnhancedAuth:
    """Enhanced authentication system combining multiple methods."""
    
    def __init__(self) -> None:
        self.api_key_auth = APIKeyAuth()
        self.jwt_auth = JWTAuth()
        self.security = HTTPBearer(auto_error=False)
    
    async def authenticate(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Dict[str, Any]:
        """Authenticate request using multiple methods."""
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info("Starting authentication process")
        
        # テスト環境での認証バイパス
        environment = os.getenv("ENVIRONMENT", "production")
        is_testing = os.getenv("TESTING", "false").lower() == "true"
        
        if environment == "test" or is_testing:
            logger.info("Test environment detected - bypassing authentication")
            security_audit_logger.log_auth_attempt(
                client_ip=client_ip,
                auth_type="test_bypass",
                success=True,
                details={"environment": environment, "testing": is_testing}
            )
            return {
                "auth_type": "test",
                "user_info": {"name": "test_user"},
                "permissions": ["read", "write"]
            }
        
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            logger.info("Attempting API key authentication")
            key_info = self.api_key_auth.verify_api_key(api_key)
            if key_info:
                logger.info(f"API key authentication successful: {key_info['name']}")
                security_audit_logger.log_auth_attempt(
                    client_ip=client_ip,
                    auth_type="api_key",
                    success=True,
                    details={"api_key_type": key_info['name'], "endpoint": str(request.url)}
                )
                security_audit_logger.log_api_key_usage(
                    api_key_type=key_info['name'],
                    endpoint=str(request.url.path),
                    client_ip=client_ip
                )
                return {
                    "auth_type": "api_key",
                    "user_info": key_info,
                    "permissions": key_info["permissions"]
                }
            else:
                logger.warning("API key verification failed")
                security_audit_logger.log_auth_attempt(
                    client_ip=client_ip,
                    auth_type="api_key",
                    success=False,
                    details={"reason": "invalid_api_key", "endpoint": str(request.url)}
                )
        
        # Check for JWT token
        if credentials and credentials.scheme == "Bearer":
            logger.info("Attempting JWT authentication")
            token_payload = self.jwt_auth.verify_token(credentials.credentials)
            if token_payload:
                logger.info("JWT authentication successful")
                security_audit_logger.log_auth_attempt(
                    client_ip=client_ip,
                    auth_type="jwt",
                    success=True,
                    details={"user_id": token_payload.get("sub"), "endpoint": str(request.url)}
                )
                return {
                    "auth_type": "jwt",
                    "user_info": token_payload,
                    "permissions": token_payload.get("permissions", ["read"])
                }
            else:
                logger.warning("JWT verification failed")
                security_audit_logger.log_auth_attempt(
                    client_ip=client_ip,
                    auth_type="jwt",
                    success=False,
                    details={"reason": "invalid_token", "endpoint": str(request.url)}
                )
        
        # Check for basic authentication (for development)
        auth_header = request.headers.get("Authorization")
        if auth_header:
            if auth_header.startswith("Basic "):
                logger.info("Attempting basic authentication")
                # For development purposes only
                if os.getenv("ENVIRONMENT") == "development":
                    logger.info("Basic authentication successful (development mode)")
                    security_audit_logger.log_auth_attempt(
                        client_ip=client_ip,
                        auth_type="basic_dev",
                        success=True,
                        details={"environment": "development", "endpoint": str(request.url)}
                    )
                    return {
                        "auth_type": "basic",
                        "user_info": {"name": "developer"},
                        "permissions": ["read", "write"]
                    }
                else:
                    logger.warning("Basic authentication not allowed in production")
                    security_audit_logger.log_auth_attempt(
                        client_ip=client_ip,
                        auth_type="basic_rejected",
                        success=False,
                        details={"reason": "basic_auth_not_allowed_in_production", "endpoint": str(request.url)}
                    )
        
        # No valid authentication found
        logger.error("Authentication failed: No valid credentials found")
        security_audit_logger.log_auth_attempt(
            client_ip=client_ip,
            auth_type="none",
            success=False,
            details={"reason": "no_valid_credentials", "endpoint": str(request.url), "user_agent": request.headers.get("user-agent")}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    def require_permission(self, required_permission: str) -> Callable:
        """Decorator to require specific permission."""
        def permission_checker(auth_info: Dict[str, Any] = Depends(self.authenticate)) -> Dict[str, Any]:
            if required_permission not in auth_info.get("permissions", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{required_permission}' required"
                )
            return auth_info
        return permission_checker

# Global authentication instance
auth = EnhancedAuth()

# Convenience functions
async def get_current_user(auth_info: Dict[str, Any] = Depends(auth.authenticate)) -> Dict[str, Any]:
    """Get current authenticated user."""
    return auth_info

def require_read_permission(auth_info: Dict[str, Any] = Depends(auth.require_permission("read"))) -> Dict[str, Any]:
    """Require read permission."""
    return auth_info

def require_write_permission(auth_info: Dict[str, Any] = Depends(auth.require_permission("write"))) -> Dict[str, Any]:
    """Require write permission."""
    return auth_info
