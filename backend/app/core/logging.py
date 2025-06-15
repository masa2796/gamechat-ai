"""
本番環境対応統一ログ設定
"""
import logging
import logging.handlers
import sys
import os
import json
from typing import Optional, Any, Dict
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """構造化JSON形式のログフォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # エラー情報を追加
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 追加のコンテキスト情報を追加
        if hasattr(record, 'extra_data') and record.extra_data:
            log_entry["extra"] = record.extra_data
        
        # 本番環境でのトレーサビリティ
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        return json.dumps(log_entry, ensure_ascii=False)

class GameChatLogger:
    """ゲームチャットAI本番対応統一ログ設定"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False
    
    @classmethod
    def configure_logging(cls):
        """本番環境対応のログ設定を初期化"""
        if cls._configured:
            return
        
        # 環境変数から設定を取得
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        environment = os.getenv("ENVIRONMENT", "development")
        
        # ログディレクトリの設定（CI環境対応）
        default_log_dir = "/app/logs" if environment == "production" else "./logs"
        log_dir = Path(os.getenv("LOG_DIR", default_log_dir))
        
        # ログディレクトリを作成（権限エラーの場合はスキップ）
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # CI環境や権限がない場合は標準出力のみ使用
            log_dir = None
            logging.warning(f"Cannot create log directory {log_dir}: {e}. Using stdout only.")
        
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # フォーマッターの選択
        if environment == "production":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 本番環境のファイルハンドラー（ログディレクトリが利用可能な場合のみ）
        if environment == "production" and log_dir is not None:
            try:
                # アプリケーションログ
                app_handler = logging.handlers.RotatingFileHandler(
                    log_dir / "app.log",
                    maxBytes=100 * 1024 * 1024,  # 100MB
                    backupCount=10
                )
                app_handler.setLevel(logging.INFO)
                app_handler.setFormatter(formatter)
                root_logger.addHandler(app_handler)
                
                # エラーログ
                error_handler = logging.handlers.RotatingFileHandler(
                    log_dir / "error.log",
                    maxBytes=50 * 1024 * 1024,  # 50MB
                    backupCount=10
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(formatter)
                root_logger.addHandler(error_handler)
                
                # アクセスログ（Gunicornが使用）
                access_handler = logging.handlers.RotatingFileHandler(
                    log_dir / "access.log",
                    maxBytes=100 * 1024 * 1024,  # 100MB
                    backupCount=10
                )
                access_handler.setLevel(logging.INFO)
                access_handler.setFormatter(formatter)
                
                # Gunicornのアクセスログを設定
                gunicorn_logger = logging.getLogger("gunicorn.access")
                gunicorn_logger.addHandler(access_handler)
            except (PermissionError, OSError) as e:
                logging.warning(f"Cannot create file handlers: {e}. Using console output only.")
        
        # 外部ライブラリのログレベル調整
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """統一フォーマットのロガーを取得"""
        cls.configure_logging()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def log_error(cls, logger_name: str, message: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
        """エラーログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra_data = {"error_type": type(error).__name__}
        if details:
            extra_data.update(details)
        
        logger.error(
            f"🔴 {message}: {str(error)}",
            exc_info=True,
            extra={"extra_data": extra_data}
        )
    
    @classmethod
    def log_warning(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """警告ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra = {"extra_data": details} if details else {}
        logger.warning(f"🟡 {message}", extra=extra)
    
    @classmethod
    def log_info(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """情報ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra = {"extra_data": details} if details else {}
        logger.info(f"🔵 {message}", extra=extra)
    
    @classmethod
    def log_success(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """成功ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra = {"extra_data": details} if details else {}
        logger.info(f"✅ {message}", extra=extra)
    
    @classmethod
    def log_security(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """セキュリティ関連ログ"""
        logger = cls.get_logger(logger_name)
        extra_data = {"category": "security"}
        if details:
            extra_data.update(details)
        
        logger.warning(f"🔐 SECURITY: {message}", extra={"extra_data": extra_data})
    
    @classmethod
    def log_performance(cls, logger_name: str, message: str, duration: float, details: Optional[Dict[str, Any]] = None) -> None:
        """パフォーマンス関連ログ"""
        logger = cls.get_logger(logger_name)
        extra_data = {"category": "performance", "duration_ms": duration * 1000}
        if details:
            extra_data.update(details)
        
        logger.info(f"⚡ PERFORMANCE: {message} (took {duration*1000:.2f}ms)", extra={"extra_data": extra_data})
    
    @classmethod
    def log_audit(cls, logger_name: str, action: str, user_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        """監査ログ"""
        logger = cls.get_logger(logger_name)
        extra_data = {"category": "audit", "action": action, "user_id": user_id}
        if details:
            extra_data.update(details)
        
        logger.info(f"📋 AUDIT: {action} by {user_id}", extra={"extra_data": extra_data})

# テスト環境など、必要に応じて手動で初期化する場合のみ呼び出し
# 本番環境では main.py で明示的に初期化される
if os.getenv("ENVIRONMENT") not in ["test", "testing"] and os.getenv("PYTEST_CURRENT_TEST") is None:
    GameChatLogger.configure_logging()
