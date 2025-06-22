"""
ストリーミングレスポンス用エンドポイント
30秒タイムアウト問題解決のため、リアルタイムでレスポンスを配信
"""
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..services.rag_service import RagService
from ..models.rag_models import RagRequest
from ..core.logging import GameChatLogger
from ..core.performance import bottleneck_detector
import time

router = APIRouter(prefix="/streaming", tags=["streaming"])
logger = GameChatLogger.get_logger(__name__)

class StreamingRagService:
    """ストリーミング対応RAGサービス"""
    
    def __init__(self) -> None:
        self.rag_service = RagService()
    
    async def stream_rag_response(self, rag_req: RagRequest) -> AsyncGenerator[str, None]:
        """
        RAGレスポンスをストリーミング配信
        """
        start_time = time.perf_counter()
        
        try:
            # 1. 初期レスポンス（即座に返す）
            yield self._format_chunk({
                "type": "status",
                "message": "検索を開始しています...",
                "timestamp": time.time()
            })
            
            # 2. 検索実行（非同期処理）
            yield self._format_chunk({
                "type": "status", 
                "message": "データベースを検索中...",
                "timestamp": time.time()
            })
            
            # ハイブリッド検索の実行
            search_start = time.perf_counter()
            search_result = await self.rag_service.hybrid_search_service.search(
                rag_req.question, rag_req.top_k or 50
            )
            search_duration = time.perf_counter() - search_start
            
            # 検索結果の配信
            yield self._format_chunk({
                "type": "search_complete",
                "message": f"検索完了 ({len(search_result.get('merged_results', []))}件の結果)",
                "search_duration": search_duration,
                "timestamp": time.time()
            })
            
            # 3. LLM応答生成開始
            yield self._format_chunk({
                "type": "status",
                "message": "AIが回答を生成中...",
                "timestamp": time.time()
            })
            
            # LLM応答の生成（ストリーミング対応）
            llm_start = time.perf_counter()
            context_items = search_result.get("merged_results", [])[:10]
            
            async for response_chunk in self._stream_llm_response(
                rag_req.question, context_items
            ):
                yield response_chunk
            
            llm_duration = time.perf_counter() - llm_start
            total_duration = time.perf_counter() - start_time
            
            # 4. 最終レスポンス
            yield self._format_chunk({
                "type": "complete",
                "message": "回答生成完了",
                "performance": {
                    "total_duration": total_duration,
                    "search_duration": search_duration,
                    "llm_duration": llm_duration
                },
                "timestamp": time.time()
            })
            
            # ボトルネック検出
            bottleneck_detector.check_operation(
                "streaming_rag_total", total_duration,
                {"question_length": len(rag_req.question)}
            )
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield self._format_chunk({
                "type": "error",
                "message": f"エラーが発生しました: {str(e)}",
                "timestamp": time.time()
            })
    
    async def _stream_llm_response(self, question: str, context_items: list) -> AsyncGenerator[str, None]:
        """LLM応答をストリーミング配信"""
        try:
            # コンテキスト作成
            context_text = "\n".join([
                f"【{item.title}】\n{item.text}"
                for item in context_items[:5]  # 上位5件のみ使用
            ])
            
            # OpenAI ChatCompletionのストリーミング
            response_stream = self.rag_service.llm_service.stream_response(
                question, context_text
            )
            
            # レスポンスをチャンク単位で配信
            accumulated_response = ""
            async for chunk in response_stream:
                if chunk:
                    accumulated_response += chunk
                    yield self._format_chunk({
                        "type": "llm_chunk",
                        "content": chunk,
                        "accumulated": accumulated_response,
                        "timestamp": time.time()
                    })
                    
                    # レスポンス配信の調整（過負荷防止）
                    await asyncio.sleep(0.01)
            
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            yield self._format_chunk({
                "type": "llm_error",
                "message": f"LLM応答エラー: {str(e)}",
                "timestamp": time.time()
            })
    
    def _format_chunk(self, data: Dict[str, Any]) -> str:
        """SSE形式でチャンクをフォーマット"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

streaming_service = StreamingRagService()

@router.post("/rag/query")
async def stream_rag_query(rag_req: RagRequest) -> StreamingResponse:
    """
    ストリーミング対応RAGクエリエンドポイント
    Server-Sent Events (SSE) でリアルタイム配信
    """
    if not rag_req.question:
        raise HTTPException(status_code=400, detail="質問が入力されていません")
    
    logger.info(f"🚀 Streaming RAG query: {rag_req.question[:50]}...")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        async for chunk in streaming_service.stream_rag_response(rag_req):
            yield chunk
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginxバッファリング無効化
        }
    )

@router.get("/health")
async def streaming_health() -> Dict[str, Any]:
    """ストリーミングサービスヘルスチェック"""
    return {
        "status": "healthy",
        "service": "streaming",
        "timestamp": time.time()
    }
