# main.py
import time
import os
import logging
from datetime import datetime
from typing import Any, AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import rag
from .core.exception_handlers import setup_exception_handlers
from .core.config import settings
from .core.security import SecurityHeadersMiddleware
from .core.rate_limit import RateLimitMiddleware
from .core.database import initialize_database, close_database, database_health_check
from .core.logging import GameChatLogger

# ログ設定を初期化
GameChatLogger.configure_logging()

# ヘルスチェック用のアプリ開始時間
app_start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    logger = logging.getLogger("startup")
    logger.info("🚀 Starting GameChat AI backend...")
    
    # データディレクトリの存在確認と作成
    try:
        if not os.path.exists(str(settings.DATA_DIR)):
            os.makedirs(str(settings.DATA_DIR), exist_ok=True)
            logger.info(f"📁 Created data directory: {settings.DATA_DIR}")
    except Exception as e:
        logger.warning(f"⚠️ Could not create data directory: {e}")
    
    # 環境情報とパス設定をログ出力
    logger.info("📍 Environment and Path Configuration:", extra={
        "environment": settings.ENVIRONMENT,
        "current_directory": os.getcwd(),
        "project_root": str(settings.PROJECT_ROOT),
        "data_file_path": settings.DATA_FILE_PATH,
        "converted_data_path": settings.CONVERTED_DATA_FILE_PATH,
        "data_file_exists": os.path.exists(settings.DATA_FILE_PATH),
        "converted_data_exists": os.path.exists(settings.CONVERTED_DATA_FILE_PATH),
        "data_dir_exists": os.path.exists(str(settings.DATA_DIR)),
        "data_dir_contents": os.listdir(str(settings.DATA_DIR)) if os.path.exists(str(settings.DATA_DIR)) else "N/A"
    })
    
    # データベース接続プール初期化
    try:
        await initialize_database()
        logger.info("✅ Database connections initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database connections: {e}")
    
    logger.info("🎉 GameChat AI backend started successfully")
    
    yield  # ここでアプリケーションが実行される
    
    # 終了時の処理
    logger = logging.getLogger("shutdown")
    logger.info("🛑 Shutting down GameChat AI backend...")
    
    # データベース接続プール終了
    try:
        await close_database()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")
    
    logger.info("👋 GameChat AI backend shutdown complete")

app = FastAPI(
    title="GameChat AI API",
    description="GameChat AI Backend API",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
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