from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError

from .exceptions import GameChatException
from .logging import GameChatLogger

def setup_exception_handlers(app):
    
    @app.exception_handler(GameChatException)
    async def gamechat_exception_handler(request: Request, exc: GameChatException):
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
    async def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
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
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
        return JSONResponse(status_code=exc.status_code, content={"error": {"message": str(exc.detail), "code": "HTTP_ERROR"}})