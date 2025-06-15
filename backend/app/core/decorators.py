"""
エラーハンドリングデコレータ
"""
import functools
from typing import Any, Callable, Optional, Type

from .exceptions import GameChatException, to_http_exception
from .logging import GameChatLogger


def handle_exceptions(
    exception_type: Type[GameChatException] = GameChatException,
    fallback_return: Any = None,
    logger_name: Optional[str] = None,
    http_status_code: int = 500
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    例外処理デコレータ
    
    Args:
        exception_type: キャッチする例外タイプ
        fallback_return: 例外発生時のフォールバック戻り値
        logger_name: ログ出力に使用するロガー名
        http_status_code: HTTPExceptionに変換する際のステータスコード
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except GameChatException as e:
                # 共通例外の場合
                log_name = logger_name or func.__module__
                GameChatLogger.log_error(
                    log_name, 
                    f"Function {func.__name__} failed", 
                    e,
                    {"args": str(args), "kwargs": str(kwargs)}
                )
                
                # HTTPExceptionに変換するか、フォールバック値を返す
                if fallback_return is not None:
                    return fallback_return
                else:
                    raise to_http_exception(e, http_status_code)
                    
            except Exception as e:
                # 予期しない例外の場合
                log_name = logger_name or func.__module__
                GameChatLogger.log_error(
                    log_name,
                    f"Unexpected error in {func.__name__}",
                    e,
                    {"args": str(args), "kwargs": str(kwargs)}
                )
                
                # 共通例外に変換
                generic_exception = exception_type(
                    message=f"{func.__name__}でエラーが発生しました",
                    details={"original_error": str(e)}
                )
                
                if fallback_return is not None:
                    return fallback_return
                else:
                    raise to_http_exception(generic_exception, http_status_code)
        
        return wrapper
    return decorator


def handle_service_exceptions(
    service_name: str,
    fallback_return: Any = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    サービス層専用の例外処理デコレータ
    """
    return handle_exceptions(
        exception_type=GameChatException,
        fallback_return=fallback_return,
        logger_name=f"services.{service_name}",
        http_status_code=500
    )


def handle_api_exceptions(
    fallback_status: int = 500
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    API層専用の例外処理デコレータ（必ずHTTPExceptionを発生）
    """
    return handle_exceptions(
        exception_type=GameChatException,
        fallback_return=None,  # API層では必ず例外を発生
        logger_name="api",
        http_status_code=fallback_status
    )
