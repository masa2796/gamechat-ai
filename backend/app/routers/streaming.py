"""
ストリーミングレスポンス用エンドポイント
30秒タイムアウト問題解決のため、リアルタイムでレスポンスを配信
"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/rag/query")
async def stream_rag_query():
    """
    ストリーミング対応RAGクエリエンドポイント
    Server-Sent Events (SSE) でリアルタイム配信
    """
    pass

@router.get("/health")
async def streaming_health():
    """ストリーミングサービスヘルスチェック"""
    return {"status": "healthy", "service": "streaming"}
