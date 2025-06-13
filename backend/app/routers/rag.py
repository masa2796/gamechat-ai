from fastapi import APIRouter, Request, Response, Body, Cookie, HTTPException
from typing import Optional
from ..models.rag_models import RagRequest
from ..services.rag_service import RagService
from ..services.auth_service import AuthService
from ..services.hybrid_search_service import HybridSearchService

router = APIRouter()
rag_service = RagService()
auth_service = AuthService()
hybrid_search_service = HybridSearchService()

@router.post("/rag/query")
async def rag_query(
    request: Request,
    response: Response,
    rag_req: RagRequest = Body(...),
    recaptcha_passed: Optional[str] = Cookie(None)
):
    recaptcha_status = await auth_service.verify_request(
        request, response, rag_req.recaptchaToken, recaptcha_passed
    )
    if not recaptcha_status:
        raise HTTPException(status_code=401, detail="認証に失敗しました")
      
    result = await rag_service.process_query(rag_req)
    
    return result

@router.post("/rag/search-test")
async def search_test(
    request: Request,
    response: Response,
    query_data: dict = Body(...),
    recaptcha_passed: Optional[str] = Cookie(None)
):
    """ハイブリッド検索のテスト用エンドポイント"""
    recaptcha_status = await auth_service.verify_request(
        request, response, query_data.get("recaptchaToken"), recaptcha_passed
    )
    if not recaptcha_status:
        raise HTTPException(status_code=401, detail="認証に失敗しました")
    
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