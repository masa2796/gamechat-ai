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
import traceback

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
    def configure_logging(cls) -> None:
        """Cloud Run/本番環境向け: ログ設定を初期化（stdoutのみ、重複防止）"""
        if cls._configured:
            return
        
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        environment = os.getenv("ENVIRONMENT", "development")
        
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))
        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # フォーマッターの選択
        formatter: logging.Formatter
        if environment == "production":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # stdoutのみ
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # ファイルハンドラーはCloud Runでは一切追加しない
        # gunicorn/uvicornのloggerもstdoutのみ
        for logger_name in ["gunicorn.error", "gunicorn.access", "uvicorn", "uvicorn.access", "fastapi"]:
            logger_obj = logging.getLogger(logger_name)
            logger_obj.handlers.clear()
            logger_obj.addHandler(console_handler)
            logger_obj.setLevel(logging.WARNING if logger_name != "gunicorn.error" else logging.INFO)
            logger_obj.propagate = False
        
        # OpenAI/Upstash等の冗長なログも抑制
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("upstash_vector").setLevel(logging.WARNING)
        logging.getLogger("app.core.database").setLevel(logging.INFO)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """統一フォーマットのロガーを取得（propagate=Falseで重複防止）"""
        cls.configure_logging()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.propagate = False  # 伝播禁止で重複防止
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def log_error(cls, logger_name: str, message: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
        """エラーログの統一フォーマット（extraはプリミティブ型のみ）"""
        logger = cls.get_logger(logger_name)
        extra_data = {
            "error_type": type(error).__name__,
            "error": str(error),
            "traceback": traceback.format_exc()
        }
        if details:
            # details内もプリミティブ型・dict・listのみ許容
            safe_details = cls._sanitize_extra(details)
            extra_data.update(safe_details)
        logger.error(
            f"🔴 {message}: {str(error)}",
            exc_info=True,
            extra={"extra_data": extra_data}
        )
    
    @staticmethod
    def _sanitize_extra(data):
        """extraで渡す値をプリミティブ型・dict・listのみに制限"""
        if isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, dict):
            return {k: GameChatLogger._sanitize_extra(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [GameChatLogger._sanitize_extra(v) for v in data]
        else:
            return str(data)

    @classmethod
    def log_warning(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """警告ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra = {"extra_data": cls._sanitize_extra(details)} if details else {}
        logger.warning(f"🟡 {message}", extra=extra)
    
    @classmethod
    def log_info(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """情報ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra = {"extra_data": cls._sanitize_extra(details)} if details else {}
        logger.info(f"🔵 {message}", extra=extra)
    
    @classmethod
    def log_success(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """成功ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra = {"extra_data": cls._sanitize_extra(details)} if details else {}
        logger.info(f"✅ {message}", extra=extra)
    
    @classmethod
    def log_security(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """セキュリティ関連ログ"""
        logger = cls.get_logger(logger_name)
        extra_data = {"category": "security"}
        if details:
            extra_data.update(cls._sanitize_extra(details))
        logger.warning(f"🔐 SECURITY: {message}", extra={"extra_data": extra_data})
    
    @classmethod
    def log_performance(cls, logger_name: str, message: str, duration: float, details: Optional[Dict[str, Any]] = None) -> None:
        """パフォーマンス関連ログ"""
        logger = cls.get_logger(logger_name)
        extra_data = {"category": "performance", "duration_ms": duration * 1000}
        if details:
            extra_data.update(cls._sanitize_extra(details))
        logger.info(f"⚡ PERFORMANCE: {message} (took {duration*1000:.2f}ms)", extra={"extra_data": extra_data})
    
    @classmethod
    def log_audit(cls, logger_name: str, action: str, user_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        """監査ログ"""
        logger = cls.get_logger(logger_name)
        extra_data = {"category": "audit", "action": action, "user_id": user_id}
        if details:
            extra_data.update(cls._sanitize_extra(details))
        logger.info(f"📋 AUDIT: {action} by {user_id}", extra={"extra_data": extra_data})
    
    @classmethod
    def log_debug(cls, logger_name: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """デバッグログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        extra = {"extra_data": cls._sanitize_extra(details)} if details else {}
        logger.debug(f"🟢 {message}", extra=extra)

# テスト環境など、必要に応じて手動で初期化する場合のみ呼び出し
# 本番環境では main.py で明示的に初期化される
if os.getenv("ENVIRONMENT") not in ["test", "testing"] and os.getenv("PYTEST_CURRENT_TEST") is None:
    GameChatLogger.configure_logging()
