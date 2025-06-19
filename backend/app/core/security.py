from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Any, Awaitable
from .config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """本番環境用セキュリティヘッダーミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
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
            
            # CSP (Content Security Policy) - Firebase Hosting + Cloud Run用
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' https://gamechat-ai.web.app https://gamechat-ai.firebaseapp.com; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.google.com https://www.gstatic.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self' https: https://gamechat-ai.web.app https://gamechat-ai.firebaseapp.com; "
                "frame-ancestors 'self' https://gamechat-ai.web.app https://gamechat-ai.firebaseapp.com;"
            )
            
        return response
