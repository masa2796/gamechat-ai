# main.py
import time
import os
import logging
import random
import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
from .routers import rag, streaming, security_admin
from .core.exception_handlers import setup_exception_handlers
from .core.config import settings
from .core.security import SecurityHeadersMiddleware
from .core.rate_limit import RateLimitMiddleware
from .core.database import initialize_database, close_database, database_health_check
from .core.logging import GameChatLogger
from .services.storage_service import StorageService
import threading
from google.cloud import storage  # 追加: GCSクライアント

# 通信レイヤの冗長ログ抑制
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.INFO)  # ここはINFOでも残す価値あり
logging.getLogger("google.cloud").setLevel(logging.WARNING)
logging.getLogger("passlib").setLevel(logging.WARNING)
logging.getLogger("google.cloud").setLevel(logging.WARNING)
logging.getLogger("passlib").setLevel(logging.WARNING)

# Sentry初期化
if settings.SENTRY_DSN:
    def traces_sampler(sampling_context: dict[str, Any]) -> float:
        """動的トレースサンプリング"""
        # リクエストパスに基づいたサンプリング
        if "wsgi_environ" in sampling_context or "asgi_scope" in sampling_context:
            try:
                # FastAPIの場合、asgi_scopeから情報を取得
                scope = sampling_context.get("asgi_scope", {})
                path = scope.get("path", "")
                
                # ヘルスチェックやメトリクスエンドポイントは低頻度
                if path in ["/health", "/healthcheck", "/metrics", "/ping"]:
                    return 0.01 if settings.ENVIRONMENT == "production" else 0.1
                
                # 静的リソースは監視しない
                if path.startswith(("/static/", "/_next/", "/favicon.ico")):
                    return 0
                
                # API エンドポイントは中頻度
                if path.startswith("/api/"):
                    return 0.1 if settings.ENVIRONMENT == "production" else 0.5
                
                # その他のエンドポイント
                return 0.05 if settings.ENVIRONMENT == "production" else 1.0
                
            except Exception:
                # エラーが発生した場合のデフォルト値
                return 0.1 if settings.ENVIRONMENT == "production" else 1.0
        
        # その他の場合のデフォルト値
        return 0.1 if settings.ENVIRONMENT == "production" else 1.0
    
    def before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
        """エラーフィルタリング"""
        if settings.ENVIRONMENT != "production":
            return event
        
        # 一般的なネットワークエラーをフィルタリング
        if event.get("exception"):
            exc_values = event["exception"].get("values", [])
            for exc_value in exc_values:
                exc_type = exc_value.get("type", "")
                exc_value_str = exc_value.get("value", "")
                
                # よくあるネットワークエラー
                if any(pattern in exc_value_str.lower() for pattern in [
                    "connection reset", "connection aborted", "broken pipe",
                    "timeout", "connection refused", "network is unreachable"
                ]):
                    # 10%の確率で送信
                    return event if random.random() < 0.1 else None
                
                # HTTP エラーの処理
                if "httpx" in exc_type.lower() or "requests" in exc_type.lower():
                    # HTTP 5xx エラーは送信、4xx エラーは低頻度
                    if "5" in exc_value_str[:3]:
                        return event
                    elif "4" in exc_value_str[:3]:
                        return event if random.random() < 0.2 else None
        
        return event
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[500, 502, 503, 504],
            ),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        environment=settings.ENVIRONMENT,
        traces_sampler=traces_sampler,
        sample_rate=0.8 if settings.ENVIRONMENT == "production" else 1.0,
        send_default_pii=False,
        attach_stacktrace=True,
        before_send=before_send,  # type: ignore[arg-type]
        release=os.getenv("GIT_COMMIT_SHA") or os.getenv("VERCEL_GIT_COMMIT_SHA"),
    )

# ログ設定を初期化
GameChatLogger.configure_logging()

# ヘルスチェック用のアプリ開始時間
app_start_time = time.time()

# カスタムPrometheusメトリクス
RAG_QUERY_COUNTER = Counter(
    'gamechat_ai_rag_queries_total', 
    'Total number of RAG queries processed',
    ['method', 'status']
)

RAG_QUERY_DURATION = Histogram(
    'gamechat_ai_rag_query_duration_seconds',
    'Time spent processing RAG queries',
    ['method']
)

DATABASE_OPERATIONS_COUNTER = Counter(
    'gamechat_ai_database_operations_total',
    'Total number of database operations',
    ['operation', 'status']
)

STORAGE_OPERATIONS_COUNTER = Counter(
    'gamechat_ai_storage_operations_total',
    'Total number of storage operations',
    ['operation', 'status']
)

# メトリクス更新用ヘルパー関数
def increment_rag_query_counter(method: str, status: str) -> None:
    """RAGクエリカウンターを増加"""
    RAG_QUERY_COUNTER.labels(method=method, status=status).inc()

def observe_rag_query_duration(method: str, duration: float) -> None:
    """RAGクエリ処理時間を記録"""
    RAG_QUERY_DURATION.labels(method=method).observe(duration)

def increment_database_operations_counter(operation: str, status: str) -> None:
    """データベース操作カウンターを増加"""
    DATABASE_OPERATIONS_COUNTER.labels(operation=operation, status=status).inc()

def increment_storage_operations_counter(operation: str, status: str) -> None:
    """ストレージ操作カウンターを増加"""
    STORAGE_OPERATIONS_COUNTER.labels(operation=operation, status=status).inc()

# プロセス単位の初期化フラグ
_lifespan_initialized = False
_lifespan_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _lifespan_initialized
    logger = logging.getLogger("startup")
    logger.info("🚀 Starting GameChat AI backend...")

    # プロセス単位で初期化処理を1回だけ実行
    with _lifespan_lock:
        if not _lifespan_initialized:
            # データディレクトリの存在確認と作成
            logger.info("Checking for data directory...")
            try:
                logger.info(f"DATA_DIR: {settings.DATA_DIR}")
                logger.info(f"Current UID: {os.getuid()}, EUID: {os.geteuid()}, GID: {os.getgid()}, EGID: {os.getegid()}")
                parent_dir = os.path.dirname(str(settings.DATA_DIR)) or "/"
                logger.info(f"Parent dir: {parent_dir}")
                if os.path.exists(parent_dir):
                    stat = os.stat(parent_dir)
                    logger.info(f"Parent dir stat: mode={oct(stat.st_mode)}, uid={stat.st_uid}, gid={stat.st_gid}")
                else:
                    logger.warning(f"Parent dir does not exist: {parent_dir}")
                if os.path.exists(str(settings.DATA_DIR)):
                    stat = os.stat(str(settings.DATA_DIR))
                    logger.info(f"DATA_DIR stat: mode={oct(stat.st_mode)}, uid={stat.st_uid}, gid={stat.st_gid}")
                else:
                    logger.info(f"DATA_DIR does not exist yet: {settings.DATA_DIR}")
                if not os.path.exists(str(settings.DATA_DIR)):
                    os.makedirs(str(settings.DATA_DIR), exist_ok=True)
                    logger.info(f"📁 Created data directory: {settings.DATA_DIR}")
                else:
                    logger.info(f"📁 Data directory already exists: {settings.DATA_DIR}")
            except Exception as e:
                logger.error(f"⚠️ Could not create data directory: {e}", exc_info=True)

            # Cloud Run環境でGCSからdata/data.jsonをダウンロード
            data_path = None
            if settings.ENVIRONMENT == "production":
                bucket_name = settings.GCS_BUCKET_NAME
                gcs_blob_path = "data/data.json"
                local_path = "/tmp/data.json"
                try:
                    async def download_gcs_file():
                        def _download():
                            client = storage.Client()
                            bucket = client.bucket(bucket_name)
                            blob = bucket.blob(gcs_blob_path)
                            if not blob.exists():
                                raise FileNotFoundError(f"GCSファイルが存在しません: gs://{bucket_name}/{gcs_blob_path}")
                            blob.download_to_filename(local_path)
                        return await asyncio.to_thread(_download)
                    await download_gcs_file()
                    logger.info(f"✅ GCSからdata/data.jsonを/tmp/data.jsonにダウンロード完了: {local_path}")
                    data_path = local_path
                except Exception as e:
                    logger.error(f"❌ GCSからのdata/data.jsonダウンロードに失敗: {e}", exc_info=True)
                    raise
            # StorageServiceを初期化してデータを準備
            logger.info("Initializing StorageService...")
            try:
                if data_path:
                    storage_service = StorageService(data_path=data_path)
                else:
                    storage_service = StorageService()
                logger.info("✅ StorageService initialized successfully")
                
                # 主要なデータファイルの可用性をチェック
                data_status = {}
                for file_key in ["data", "convert_data", "embedding_list", "query_data"]:
                    file_path = storage_service.get_file_path(file_key)
                    data_status[file_key] = bool(file_path)
                # extraの値をプリミティブ型・dict・listのみに限定
                safe_data_status = {k: bool(v) for k, v in data_status.items()}
                logger.info("📊 Data files availability status:", extra={"data_status": safe_data_status})
                
                # 最低限必要なファイルの確認
                if not (data_status.get("data") or data_status.get("convert_data")):
                    logger.warning("⚠️ No primary data files available. Application may have limited functionality.")
            
            except Exception as e:
                logger.error(f"❌ StorageService initialization failed: {e}", exc_info=True)
                logger.warning("🔄 Application will continue with limited functionality")

            # 環境情報とパス設定をログ出力
            safe_env = {
                "environment": str(settings.ENVIRONMENT),
                "current_directory": str(os.getcwd()),
                "project_root": str(settings.PROJECT_ROOT),
                "data_file_path": str(settings.DATA_FILE_PATH),
                "converted_data_path": str(settings.CONVERTED_DATA_FILE_PATH),
                "data_file_exists": bool(os.path.exists(settings.DATA_FILE_PATH)),
                "converted_data_exists": bool(os.path.exists(settings.CONVERTED_DATA_FILE_PATH)),
                "data_dir_exists": bool(os.path.exists(str(settings.DATA_DIR))),
                "data_dir_contents": os.listdir(str(settings.DATA_DIR)) if os.path.exists(str(settings.DATA_DIR)) else "N/A"
            }
            logger.info("📍 Environment and Path Configuration:", extra=safe_env)

            _lifespan_initialized = True

    # データベース接続プール初期化
    logger.info("Initializing database connections...")
    try:
        await initialize_database()
        logger.info("✅ Database connections initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database connections: {e}", exc_info=True)

    # キャッシュプリウォーミング（バックグラウンドで実行）
    logger.info("Starting cache prewarming task setup...")
    try:
        from .core.cache import prewarmed_query_cache
        from .services.rag_service import RagService
        
        # バックグラウンドでプリウォーミング実行
        async def background_prewarm() -> None:
            logger.info("🔥 Background prewarming task waiting to start...")
            await asyncio.sleep(5)
            logger.info("🔥 Starting background cache prewarming process...")
            try:
                logger.info("Instantiating RagService for prewarming...")
                rag_service = RagService()
                logger.info("✅ RagService instantiated. Starting cache prewarm...")
                await prewarmed_query_cache.prewarm_cache(rag_service)
                logger.info("✅ Cache prewarming completed successfully.")
            except Exception as e:
                logger.error(f"❌ Cache prewarming failed during execution: {e}", exc_info=True)
        
        asyncio.create_task(background_prewarm())
        logger.info("✅ Cache prewarming task created and started.")
    except Exception as e:
        logger.error(f"❌ Could not start cache prewarming task: {e}", exc_info=True)
    
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

# Prometheus メトリクス設定
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="gamechat_ai_requests_inprogress",
    inprogress_labels=True,
)

# メトリクスを初期化して公開
instrumentator.instrument(app).expose(app)

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

import sys

try:
    from .core.config import settings
except Exception as e:
    import traceback
    print("[FATAL] settings import/init failed:", file=sys.stderr)
    traceback.print_exc()
    from .core.config import Settings  # 型エラー回避のため
    class DummySettings(Settings):
        ENVIRONMENT = "unknown"
        DEBUG = False
        CORS_ORIGINS = ["*"]
    settings = DummySettings()

@app.get("/health")
async def health_check() -> dict[str, str | int | float]:
    """ヘルスチェック用エンドポイント"""
    try:
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
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "service": "gamechat-ai-backend",
            "timestamp": datetime.now().isoformat(),
        }

@app.get("/health/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """詳細なヘルスチェック用エンドポイント"""
    current_time = time.time()
    uptime = current_time - app_start_time
    is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    # データベース接続状況を確認
    try:
        if is_test_mode:
            db_health = {"status": "test_mode", "message": "Database checks skipped in test mode"}
        else:
            db_health = await database_health_check()
    except Exception as e:
        db_health = {"status": "error", "message": str(e)}
    
    # ストレージサービス状況を確認
    try:
        storage_service = StorageService()
        storage_health: dict[str, Any] = {
            "status": "healthy" if not is_test_mode else "test_mode",
            "gcs_configured": bool(storage_service.bucket_name) if not is_test_mode else False,
            "environment": settings.ENVIRONMENT,
            "test_mode": is_test_mode
        }
        
        if not is_test_mode:
            storage_health["cache_info"] = storage_service.get_cache_info()
            
            # データファイルの可用性確認
            data_files = {}
            for file_key in ["data", "convert_data", "embedding_list", "query_data"]:
                file_path = storage_service.get_file_path(file_key)
                data_files[file_key] = bool(file_path)
            
            storage_health["data_files"] = data_files
        
    except Exception as e:
        storage_health = {"status": "error", "message": str(e), "test_mode": is_test_mode}
    
    health_data = {
        "status": "healthy",
        "service": "gamechat-ai-backend",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "test_mode": is_test_mode,
        "settings": {
            "gcs_bucket_name": settings.GCS_BUCKET_NAME if not is_test_mode else "test-mode",
            "data_dir": str(settings.DATA_DIR)
        },
        "checks": {
            "database": db_health,
            "external_apis": "test_mode" if is_test_mode else "healthy",
            "storage": storage_health
        }
    }
    
    return health_data

@app.get("/health/metrics")
async def metrics_health_check() -> dict[str, Any]:
    """メトリクス収集状況のヘルスチェック"""
    return {
        "status": "healthy",
        "service": "gamechat-ai-backend-metrics",
        "timestamp": datetime.now().isoformat(),
        "metrics_endpoint": "/metrics",
        "custom_metrics": {
            "rag_queries": "gamechat_ai_rag_queries_total",
            "rag_duration": "gamechat_ai_rag_query_duration_seconds",
            "database_ops": "gamechat_ai_database_operations_total",
            "storage_ops": "gamechat_ai_storage_operations_total"
        },
        "instrumentator": {
            "enabled": True,
            "inprogress_tracking": True,
            "excluded_handlers": ["/health", "/metrics"]
        }
    }

app.include_router(rag.router, prefix="/api")
app.include_router(streaming.router, prefix="/api")
app.include_router(security_admin.router, prefix="/api/security")