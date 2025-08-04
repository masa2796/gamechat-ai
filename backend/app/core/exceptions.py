"""
共通例外クラス定義
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException


class GameChatException(Exception):
    """ゲームチャットAIアプリケーションの基底例外クラス"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseServiceException(GameChatException):
    """データベースサービス関連の例外"""
    
    def __init__(
        self,
        message: str,
        code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class DatabaseException(GameChatException):
    """データベース関連例外"""
    
    def __init__(
        self,
        message: str = "データベース操作エラー",
        code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class VectorSearchException(GameChatException):
    """ベクトル検索関連例外"""
    
    def __init__(
        self,
        message: str = "ベクトル検索エラー",
        code: str = "VECTOR_SEARCH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class EmbeddingException(GameChatException):
    """埋め込み生成関連例外"""
    
    def __init__(
        self,
        message: str = "埋め込み生成エラー",
        code: str = "EMBEDDING_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class ClassificationException(GameChatException):
    """分類処理関連例外"""
    
    def __init__(
        self,
        message: str = "分類処理エラー",
        code: str = "CLASSIFICATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class LLMException(GameChatException):
    """LLM関連例外"""
    
    def __init__(
        self,
        message: str = "LLM処理エラー",
        code: str = "LLM_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class AuthenticationException(GameChatException):
    """認証関連例外"""
    
    def __init__(
        self,
        message: str = "認証エラー",
        code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class ValidationException(GameChatException):
    """バリデーション関連例外"""
    
    def __init__(
        self,
        message: str = "バリデーションエラー",
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class StorageException(GameChatException):
    """ストレージ関連例外"""
    
    def __init__(
        self,
        message: str = "ストレージ操作エラー",
        code: str = "STORAGE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


def to_http_exception(exc: GameChatException, status_code: int = 500) -> HTTPException:
    """GameChatExceptionをHTTPExceptionに変換"""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": exc.message,
            "code": exc.code,
            "details": exc.details
        }
    )
