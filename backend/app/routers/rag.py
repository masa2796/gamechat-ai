from fastapi import APIRouter, Request, Response, Body, Cookie, HTTPException, Depends
from typing import Optional, Dict, Any
import logging
from ..models.rag_models import RagRequest
from ..services.rag_service import RagService
from ..services.auth_service import AuthService
from ..services.hybrid_search_service import HybridSearchService
from ..core.auth import require_read_permission

logger = logging.getLogger(__name__)

router = APIRouter()
rag_service = RagService()
auth_service = AuthService()
hybrid_search_service = HybridSearchService()

# OPTIONSプリフライトリクエストのハンドラー
@router.options("/rag/query")
@router.options("/chat")  
async def options_preflight(request: Request, response: Response) -> Dict[str, str]:
    """OPTIONSプリフライトリクエストを処理"""
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"OPTIONS request received from {client_host}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # CORS ヘッダーを設定
    response.headers["Access-Control-Allow-Origin"] = "https://gamechat-ai.web.app"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-API-Key, X-Requested-With, Accept, Origin, Cache-Control"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return {"status": "ok"}

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