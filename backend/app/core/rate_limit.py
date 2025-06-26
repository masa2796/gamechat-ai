"""
Rate limiting middleware for FastAPI application.
"""
import time
import os
import logging
from typing import Dict, Tuple, Optional, Callable, Awaitable, Any, TYPE_CHECKING
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Redis import with fallback
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore
    logger.warning("Redis not available, using in-memory rate limiting only")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis for distributed rate limiting.
    Falls back to in-memory storage if Redis is not available.
    """
    
    def __init__(self, app: Any, redis_url: Optional[str] = None):
        super().__init__(app)
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.redis_client: Optional["Redis"] = None
        self.memory_store: Dict[str, Tuple[int, float]] = {}
        
        # Rate limiting rules
        self.rate_limits = {
            "/api/rag/query": (60, 60),  # 60 requests per minute
            "/api/rag/health": (100, 60), # 100 requests per minute
            "default": (100, 60)          # Default: 100 requests per minute
        }
        
        # Initialize Redis connection
        self._init_redis()
    
    def _init_redis(self) -> None:
        """Initialize Redis connection if available."""
        if not REDIS_AVAILABLE or not redis:
            logger.info("Redis not available, using in-memory rate limiting")
            return
            
        if self.redis_url:
            try:
                if redis:
                    self.redis_client = redis.from_url(
                        self.redis_url,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5
                    )
                    # Test connection
                    if self.redis_client:
                        self.redis_client.ping()
                    logger.info("Redis connection established for rate limiting")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory storage: {e}")
                self.redis_client = None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for specific path."""
        for rule_path, (limit, window) in self.rate_limits.items():
            if path.startswith(rule_path):
                return limit, window
        return self.rate_limits["default"]
    
    def _check_rate_limit_redis(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check rate limit using Redis."""
        if not self.redis_client:
            return self._check_rate_limit_memory(key, limit, window)
        
        try:
            current_time = int(time.time())
            pipeline = self.redis_client.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, current_time - window)
            
            # Count current requests
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipeline.expire(key, window)
            
            results = pipeline.execute()
            current_requests = results[1]
            
            return current_requests < limit, current_requests
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to allowing the request
            return True, 0
    
    def _check_rate_limit_memory(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check rate limit using in-memory storage."""
        current_time = time.time()
        
        if key in self.memory_store:
            count, first_request_time = self.memory_store[key]
            
            # Reset if window has passed
            if current_time - first_request_time > window:
                self.memory_store[key] = (1, current_time)
                return True, 1
            
            # Check if limit exceeded
            if count >= limit:
                return False, count
            
            # Increment counter
            self.memory_store[key] = (count + 1, first_request_time)
            return True, count + 1
        else:
            # First request
            self.memory_store[key] = (1, current_time)
            return True, 1
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/health/detailed"] or request.url.path.startswith("/static"):
            response = await call_next(request)
            return response
        
        client_ip = self._get_client_ip(request)
        path = request.url.path
        limit, window = self._get_rate_limit(path)
        
        # Create rate limit key
        rate_limit_key = f"rate_limit:{client_ip}:{path}"
        
        # Check rate limit
        if self.redis_client:
            allowed, current_requests = self._check_rate_limit_redis(rate_limit_key, limit, window)
        else:
            allowed, current_requests = self._check_rate_limit_memory(rate_limit_key, limit, window)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} requests per {window} seconds",
                    "retry_after": window
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(max(0, limit - current_requests)),
                    "X-RateLimit-Reset": str(int(time.time()) + window),
                    "Retry-After": str(window)
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current_requests))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
        
        return response
