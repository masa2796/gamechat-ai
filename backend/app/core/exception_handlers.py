from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError

def setup_exception_handlers(app):
    
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