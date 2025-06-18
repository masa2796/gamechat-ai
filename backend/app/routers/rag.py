from fastapi import APIRouter, Request, Response, Body, Cookie, HTTPException, Depends
from typing import Optional, Dict, Any
import os
import logging
from ..models.rag_models import RagRequest
from ..services.rag_service import RagService
from ..services.auth_service import AuthService
from ..services.hybrid_search_service import HybridSearchService
from ..core.auth import require_read_permission, auth

logger = logging.getLogger(__name__)

router = APIRouter()
rag_service = RagService()
auth_service = AuthService()
hybrid_search_service = HybridSearchService()

@router.get("/debug/auth-status")
async def debug_auth_status() -> Dict[str, Any]:
    """認証システムのデバッグ情報を返すエンドポイント（本番では無効化すべき）"""
    environment = os.getenv("ENVIRONMENT", "unknown")
    
    # デバッグ用に一時的に本番環境でも有効化
    # if environment == "production":
    #     raise HTTPException(status_code=404, detail="Not found")
    
    # 環境変数の確認
    env_status = {
        "ENVIRONMENT": environment,
        "API_KEY_PRODUCTION": "Set" if os.getenv("API_KEY_PRODUCTION") else "Not set",
        "API_KEY_DEVELOPMENT": "Set" if os.getenv("API_KEY_DEVELOPMENT") else "Not set",
        "API_KEY_READONLY": "Set" if os.getenv("API_KEY_READONLY") else "Not set",
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }
    
    # APIキー認証システムの状態
    api_key_count = len(auth.api_key_auth.api_keys)
    
    return {
        "environment_variables": env_status,
        "api_key_count": api_key_count,
        "auth_system_initialized": True,
        "timestamp": "2025-06-17T00:00:00Z"
    }

@router.post("/debug/test-auth")
async def debug_test_auth(
    request: Request,
    test_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """認証フローをテストするデバッグエンドポイント"""
    environment = os.getenv("ENVIRONMENT", "unknown")
    
    # デバッグ用に一時的に本番環境でも有効化
    # if environment == "production":
    #     raise HTTPException(status_code=404, detail="Not found")
    
    logger.info("=== DEBUG AUTH TEST STARTED ===")
    
    # ヘッダー情報をログ出力
    headers_info = {}
    for key, value in request.headers.items():
        if key.lower() == "x-api-key":
            headers_info[key] = f"{value[:10]}***" if value else "None"
        else:
            headers_info[key] = value
    
    logger.info(f"Request headers: {headers_info}")
    
    # 手動で認証を試行
    try:
        auth_result = await auth.authenticate(request, None)
        logger.info(f"Authentication successful: {auth_result}")
        return {
            "status": "success",
            "auth_result": auth_result,
            "headers": headers_info
        }
    except HTTPException as e:
        logger.error(f"Authentication failed: {e.detail}")
        return {
            "status": "failed",
            "error": e.detail,
            "status_code": e.status_code,
            "headers": headers_info
        }
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "headers": headers_info
        }

@router.get("/debug/env-status")
async def debug_env_status() -> Dict[str, Any]:
    """環境変数とSecret設定の状態を確認するデバッグエンドポイント"""
    environment = os.getenv("ENVIRONMENT", "unknown")
    
    # デバッグ用に一時的に本番環境でも有効化
    # if environment == "production":
    #     raise HTTPException(status_code=404, detail="Not found")
    
    # 重要な環境変数の確認
    env_status = {
        "ENVIRONMENT": environment,
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "OPENAI_API_KEY": "Set" if os.getenv("OPENAI_API_KEY") else "Not set",
        "UPSTASH_VECTOR_REST_URL": "Set" if os.getenv("UPSTASH_VECTOR_REST_URL") else "Not set", 
        "UPSTASH_VECTOR_REST_TOKEN": "Set" if os.getenv("UPSTASH_VECTOR_REST_TOKEN") else "Not set",
        "RECAPTCHA_SECRET": "Set" if os.getenv("RECAPTCHA_SECRET") else "Not set",
        "API_KEY_DEVELOPMENT": "Set" if os.getenv("API_KEY_DEVELOPMENT") else "Not set",
        "API_KEY_PRODUCTION": "Set" if os.getenv("API_KEY_PRODUCTION") else "Not set",
        "API_KEY_FRONTEND": "Set" if os.getenv("API_KEY_FRONTEND") else "Not set",
        "API_KEY_READONLY": "Set" if os.getenv("API_KEY_READONLY") else "Not set",
    }
    
    # OpenAI APIキーの詳細確認
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_details = {
        "present": bool(openai_key),
        "starts_with_sk": openai_key.startswith("sk-") if openai_key else False,
        "length": len(openai_key) if openai_key else 0,
        "first_10_chars": openai_key[:10] if openai_key else None
    }
    
    # APIキーの詳細確認
    api_key_details = {}
    for key_name in ["API_KEY_DEVELOPMENT", "API_KEY_PRODUCTION", "API_KEY_FRONTEND", "API_KEY_READONLY"]:
        key_value = os.getenv(key_name)
        api_key_details[key_name] = {
            "present": bool(key_value),
            "length": len(key_value) if key_value else 0,
            "first_10_chars": key_value[:10] if key_value else None
        }
    
    return {
        "environment_variables": env_status,
        "openai_api_key_details": openai_details,
        "api_key_details": api_key_details,
        "timestamp": "2025-06-18T00:00:00Z"
    }

@router.post("/rag/query")
async def rag_query(
    request: Request,
    response: Response,
    rag_req: RagRequest = Body(...),
    recaptcha_passed: Optional[str] = Cookie(None),
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """RAGクエリエンドポイント - API認証とreCAPTCHA認証の両方が必要"""
    recaptcha_status = await auth_service.verify_request(
        request, response, rag_req.recaptchaToken, recaptcha_passed
    )
    if not recaptcha_status:
        raise HTTPException(status_code=401, detail="reCAPTCHA認証に失敗しました")
    
    # API認証情報がauth_infoに含まれる
    result = await rag_service.process_query(rag_req)
    
    return result

@router.post("/rag/search-test")
async def search_test(
    request: Request,
    response: Response,
    query_data: Dict[str, Any] = Body(...),
    recaptcha_passed: Optional[str] = Cookie(None),
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """ハイブリッド検索のテスト用エンドポイント - API認証とreCAPTCHA認証の両方が必要"""
    recaptcha_status = await auth_service.verify_request(
        request, response, query_data.get("recaptchaToken"), recaptcha_passed
    )
    if not recaptcha_status:
        raise HTTPException(status_code=401, detail="reCAPTCHA認証に失敗しました")
    
    query = query_data.get("query", "")
    top_k = query_data.get("top_k", 50)
    
    if not query:
        raise HTTPException(status_code=400, detail="クエリが必要です")
    
    # ハイブリッド検索を実行
    result = await hybrid_search_service.search(query, top_k)
    
    return {
        "query": query,
        "classification": result["classification"].model_dump(),
        "search_strategy": result["search_strategy"].model_dump(),
        "db_results": [item.model_dump() for item in result["db_results"]],
        "vector_results": [item.model_dump() for item in result["vector_results"]],
        "merged_results": [item.model_dump() for item in result["merged_results"]]
    }

@router.post("/chat")
async def chat(
    request: Request,
    response: Response,
    chat_data: Dict[str, Any] = Body(...),
    recaptcha_passed: Optional[str] = Cookie(None),
    auth_info: dict = Depends(require_read_permission)
) -> Dict[str, Any]:
    """一般的なチャットエンドポイント - API認証とreCAPTCHA認証の両方が必要"""
    # リクエストデータをRagRequestに変換
    question = chat_data.get("message") or chat_data.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="メッセージまたは質問が必要です")
    
    # reCAPTCHA認証確認
    recaptcha_status = await auth_service.verify_request(
        request, response, chat_data.get("recaptchaToken"), recaptcha_passed
    )
    if not recaptcha_status:
        raise HTTPException(status_code=401, detail="reCAPTCHA認証に失敗しました")
    
    # RagRequestオブジェクトを作成
    from ..models.rag_models import RagRequest
    rag_req = RagRequest(
        question=question,
        top_k=chat_data.get("top_k", 5),
        with_context=chat_data.get("with_context", False),
        recaptchaToken=chat_data.get("recaptchaToken")
    )
    
    # RAGサービスで処理
    result = await rag_service.process_query(rag_req)
    
    # チャット形式のレスポンスに変換
    return {
        "response": result.get("answer", "申し訳ありませんが、回答を生成できませんでした。"),
        "context": result.get("context", []) if chat_data.get("with_context") else None
    }