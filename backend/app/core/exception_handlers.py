from fastapi import Request, HTTPException, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict

from .exceptions import GameChatException
from .logging import GameChatLogger

def setup_exception_handlers(app: FastAPI) -> None:
    
    @app.exception_handler(GameChatException)
    async def gamechat_exception_handler(request: Request, exc: GameChatException) -> JSONResponse:
        """共通例外ハンドラー"""
        # ログ出力
        GameChatLogger.log_error(
            "exception_handler",
            f"GameChatException occurred: {exc.message}",
            exc,
            {"path": str(request.url), "method": request.method}
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": exc.message,
                    "code": exc.code,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": exc.errors()[0]["msg"],
                    "code": "VALIDATION_ERROR"
                }
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        # HTTPException.detail can be str, dict, or other types
        error_content: Dict[str, Any]
        detail = exc.detail
        
        # Type guard for dict check
        if hasattr(detail, 'items') and callable(getattr(detail, 'items')):
            # Treat as dict-like object
            error_content = {"error": detail}
        else:
            # Treat as string or other type
            error_content = {"error": {"message": str(detail), "code": "HTTP_ERROR"}}
        
        return JSONResponse(status_code=exc.status_code, content=error_content)