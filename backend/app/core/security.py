from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from .config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """本番環境用セキュリティヘッダーミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 本番環境でセキュリティヘッダーを追加
        if settings.ENVIRONMENT == "production":
            # セキュリティヘッダーの設定
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # HSTS (HTTPS Strict Transport Security)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # CSP (Content Security Policy) - 必要に応じて調整
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'self';"
            )
            
        return response
