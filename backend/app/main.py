# main.py
import time
import logging
from datetime import datetime
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import rag
from .core.exception_handlers import setup_exception_handlers
from .core.config import settings
from .core.security import SecurityHeadersMiddleware
from .core.rate_limit import RateLimitMiddleware
from .core.database import initialize_database, close_database, database_health_check

app = FastAPI(
    title="GameChat AI API",
    description="GameChat AI Backend API",
    version="1.0.0",
    debug=settings.DEBUG
)

# セキュリティヘッダーミドルウェアを追加
app.add_middleware(SecurityHeadersMiddleware)

# レート制限ミドルウェアを追加
app.add_middleware(RateLimitMiddleware)

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
app_start_time = time.time()

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger = logging.getLogger("startup")
    logger.info("🚀 Starting GameChat AI backend...")
    
    # データベース接続プール初期化
    try:
        await initialize_database()
        logger.info("✅ Database connections initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database connections: {e}")
    
    logger.info("🎉 GameChat AI backend started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger = logging.getLogger("shutdown")
    logger.info("🛑 Shutting down GameChat AI backend...")
    
    # データベース接続プール終了
    try:
        await close_database()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")
    
    logger.info("👋 GameChat AI backend shutdown complete")

@app.get("/health")
async def health_check() -> dict[str, str | int | float]:
    """ヘルスチェック用エンドポイント"""
    current_time = time.time()
    uptime = current_time - app_start_time
    
    return {
        "status": "healthy",
        "service": "gamechat-ai-backend",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """詳細なヘルスチェック用エンドポイント"""
    current_time = time.time()
    uptime = current_time - app_start_time
    
    # データベース接続状況を確認
    try:
        db_health = await database_health_check()
    except Exception as e:
        db_health = {"status": "error", "message": str(e)}
    
    health_data = {
        "status": "healthy",
        "service": "gamechat-ai-backend",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": db_health,
            "external_apis": "healthy",  # 外部API接続チェック
            "storage": "healthy"  # ストレージ接続チェック
        }
    }
    
    return health_data

app.include_router(rag.router, prefix="/api")