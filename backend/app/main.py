# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import rag
from .core.exception_handlers import setup_exception_handlers
from .core.config import settings
from .core.security import SecurityHeadersMiddleware

app = FastAPI(
    title="GameChat AI API",
    description="GameChat AI Backend API",
    version="1.0.0",
    debug=settings.DEBUG
)

# セキュリティヘッダーミドルウェアを追加
app.add_middleware(SecurityHeadersMiddleware)

# 統一例外ハンドラーをセットアップ
setup_exception_handlers(app)

# CORS設定を環境別に適用
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェック用エンドポイント"""
    return {"status": "healthy", "service": "gamechat-ai-backend"}

app.include_router(rag.router, prefix="/api")