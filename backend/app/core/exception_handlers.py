from fastapi import Request, HTTPException, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any, Dict
import logging
import traceback
import time
from datetime import datetime

from .exceptions import GameChatException
from .logging import GameChatLogger

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI) -> None:
    
    @app.exception_handler(GameChatException)
    async def gamechat_exception_handler(request: Request, exc: GameChatException) -> JSONResponse:
        """GameChat独自例外ハンドラー"""
        # エラー発生時間とリクエスト情報をログに記録
        error_id = f"err_{int(time.time() * 1000)}"
        
        GameChatLogger.log_error(
            "exception_handler",
            f"GameChatException occurred: {exc.message}",
            exc,
            {
                "error_id": error_id,
                "path": str(request.url),
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code if hasattr(exc, 'status_code') else 500,
            content={
                "error": {
                    "message": exc.message,
                    "code": exc.code,
                    "details": exc.details,
                    "error_id": error_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """バリデーションエラーハンドラー"""
        error_id = f"val_{int(time.time() * 1000)}"
        
        # より詳細なバリデーションエラー情報を構築
        validation_errors = []
        for error in exc.errors():
            validation_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input", "N/A")
            })
        
        logger.warning(
            f"Validation error for {request.method} {request.url}: {validation_errors}",
            extra={
                "error_id": error_id,
                "client_ip": request.client.host if request.client else "unknown",
                "validation_errors": validation_errors
            }
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "message": "Validation failed",
                    "code": "VALIDATION_ERROR",
                    "details": validation_errors,
                    "error_id": error_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """HTTP例外ハンドラー"""
        error_id = f"http_{int(time.time() * 1000)}"
        
        # ログレベルを状態コードに応じて調整
        if exc.status_code >= 500:
            log_level = logging.ERROR
        elif exc.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        logger.log(
            log_level,
            f"HTTP {exc.status_code} error for {request.method} {request.url}: {exc.detail}",
            extra={
                "error_id": error_id,
                "status_code": exc.status_code,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # HTTPException.detail can be str, dict, or other types
        error_content: Dict[str, Any]
        detail = exc.detail
        
        # Handle detail as Any type to avoid mypy Union type issues
        try:
            # Try to treat as dict
            if hasattr(detail, 'items') and callable(getattr(detail, 'items', None)):
                detail_dict: Dict[str, Any] = detail  # type: ignore
                error_content = {
                    "error": {
                        **detail_dict,
                        "error_id": error_id,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            else:
                raise TypeError("Not a dict-like object")
        except (TypeError, AttributeError):
            # String or other type
            error_content = {
                "error": {
                    "message": str(detail),
                    "code": "HTTP_ERROR",
                    "error_id": error_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        return JSONResponse(status_code=exc.status_code, content=error_content)
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Starlette HTTP例外ハンドラー"""
        error_id = f"starlette_{int(time.time() * 1000)}"
        
        logger.error(
            f"Starlette HTTP {exc.status_code} error for {request.method} {request.url}: {exc.detail}",
            extra={
                "error_id": error_id,
                "status_code": exc.status_code,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": str(exc.detail),
                    "code": "STARLETTE_HTTP_ERROR",
                    "error_id": error_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """一般的な例外ハンドラー（最後の砦）"""
        error_id = f"gen_{int(time.time() * 1000)}"
        
        # 詳細なエラー情報をログに記録
        logger.error(
            f"Unhandled exception for {request.method} {request.url}: {str(exc)}",
            extra={
                "error_id": error_id,
                "exception_type": type(exc).__name__,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "traceback": traceback.format_exc()
            }
        )
        
        # 本番環境では詳細なエラー情報を隠す
        import os
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        
        if is_production:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Internal server error",
                        "code": "INTERNAL_ERROR",
                        "error_id": error_id,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": str(exc),
                        "code": "INTERNAL_ERROR",
                        "type": type(exc).__name__,
                        "error_id": error_id,
                        "timestamp": datetime.now().isoformat(),
                        "traceback": traceback.format_exc().split('\n') if not is_production else None
                    }
                }
            )