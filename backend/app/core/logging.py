"""
統一ログ設定
"""
import logging
import sys
from typing import Optional, Dict


class GameChatLogger:
    """ゲームチャットAI統一ログ設定"""
    
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """統一フォーマットのロガーを取得"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            
            # 既存のハンドラーを削除
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # コンソールハンドラーを追加
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # フォーマッター設定
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
            logger.propagate = False
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def log_error(cls, logger_name: str, message: str, error: Exception, details: Optional[dict] = None) -> None:
        """エラーログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        error_msg = f"🔴 {message}: {str(error)}"
        if details:
            error_msg += f" | Details: {details}"
        logger.error(error_msg, exc_info=True)
    
    @classmethod
    def log_warning(cls, logger_name: str, message: str, details: Optional[dict] = None) -> None:
        """警告ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        warning_msg = f"🟡 {message}"
        if details:
            warning_msg += f" | Details: {details}"
        logger.warning(warning_msg)
    
    @classmethod
    def log_info(cls, logger_name: str, message: str, details: Optional[dict] = None) -> None:
        """情報ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        info_msg = f"🔵 {message}"
        if details:
            info_msg += f" | Details: {details}"
        logger.info(info_msg)
    
    @classmethod
    def log_success(cls, logger_name: str, message: str, details: Optional[dict] = None) -> None:
        """成功ログの統一フォーマット"""
        logger = cls.get_logger(logger_name)
        success_msg = f"✅ {message}"
        if details:
            success_msg += f" | Details: {details}"
        logger.info(success_msg)
