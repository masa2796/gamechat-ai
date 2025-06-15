"""
Enhanced API authentication and authorization module.
"""
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import logging

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
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.api_key_usage = {}  # Track API key usage
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from environment variables."""
        api_keys = {}
        
        # Production API key
        prod_key = os.getenv("API_KEY_PRODUCTION")
        if prod_key:
            api_keys[prod_key] = {
                "name": "production",
                "rate_limit": 1000,  # requests per hour
                "permissions": ["read", "write"],
                "created_at": datetime.now().isoformat()
            }
        
        # Development API key
        dev_key = os.getenv("API_KEY_DEVELOPMENT")
        if dev_key:
            api_keys[dev_key] = {
                "name": "development",
                "rate_limit": 100,  # requests per hour
                "permissions": ["read", "write"],
                "created_at": datetime.now().isoformat()
            }
        
        # Read-only API key
        readonly_key = os.getenv("API_KEY_READONLY")
        if readonly_key:
            api_keys[readonly_key] = {
                "name": "readonly",
                "rate_limit": 500,  # requests per hour
                "permissions": ["read"],
                "created_at": datetime.now().isoformat()
            }
        
        return api_keys
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return key info."""
        if api_key in self.api_keys:
            key_info = self.api_keys[api_key]
            
            # Track usage
            current_time = time.time()
            if api_key not in self.api_key_usage:
                self.api_key_usage[api_key] = []
            
            # Clean old usage records (older than 1 hour)
            self.api_key_usage[api_key] = [
                timestamp for timestamp in self.api_key_usage[api_key]
                if current_time - timestamp < 3600
            ]
            
            # Check rate limit
            if len(self.api_key_usage[api_key]) >= key_info["rate_limit"]:
                logger.warning(f"Rate limit exceeded for API key: {key_info['name']}")
                return None
            
            # Record usage
            self.api_key_usage[api_key].append(current_time)
            
            return key_info
        
        return None

class JWTAuth:
    """JWT based authentication."""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        if PASSLIB_AVAILABLE and CryptContext:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        else:
            self.pwd_context = None
    
    def _generate_secret_key(self) -> str:
        """Generate a secret key if not provided."""
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
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        if not JWT_AVAILABLE or not jwt:
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

class EnhancedAuth:
    """Enhanced authentication system combining multiple methods."""
    
    def __init__(self):
        self.api_key_auth = APIKeyAuth()
        self.jwt_auth = JWTAuth()
        self.security = HTTPBearer(auto_error=False)
    
    async def authenticate(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Dict[str, Any]:
        """Authenticate request using multiple methods."""
        
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key_info = self.api_key_auth.verify_api_key(api_key)
            if key_info:
                return {
                    "auth_type": "api_key",
                    "user_info": key_info,
                    "permissions": key_info["permissions"]
                }
        
        # Check for JWT token
        if credentials and credentials.scheme == "Bearer":
            token_payload = self.jwt_auth.verify_token(credentials.credentials)
            if token_payload:
                return {
                    "auth_type": "jwt",
                    "user_info": token_payload,
                    "permissions": token_payload.get("permissions", ["read"])
                }
        
        # Check for basic authentication (for development)
        if request.headers.get("Authorization"):
            auth_header = request.headers.get("Authorization")
            if auth_header.startswith("Basic "):
                # For development purposes only
                if os.getenv("ENVIRONMENT") == "development":
                    return {
                        "auth_type": "basic",
                        "user_info": {"name": "developer"},
                        "permissions": ["read", "write"]
                    }
        
        # No valid authentication found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    def require_permission(self, required_permission: str):
        """Decorator to require specific permission."""
        def permission_checker(auth_info: Dict[str, Any] = Depends(self.authenticate)):
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
