from typing import Dict, Any, Optional
from ..models.rag_models import RagRequest
from .embedding_service import EmbeddingService
from .vector_service import VectorService
from .llm_service import LLMService
from .hybrid_search_service import HybridSearchService
from ..config.ng_words import NG_WORDS
from ..core.performance import bottleneck_detector
from ..core.cache import prewarmed_query_cache as query_cache
import logging
import time
import asyncio

logger = logging.getLogger(__name__)

class RagService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        self.hybrid_search_service = HybridSearchService()
    
    async def process_query(self, rag_req: RagRequest) -> Dict[str, Any]:
        """
        RAGクエリを処理してレスポンスを生成
        パフォーマンス監視とキャッシュ機能付き
        """
        start_time = time.perf_counter()
        
        try:
            # NGワードチェック
            if any(ng_word in rag_req.question for ng_word in NG_WORDS):
                return {
                    "answer": "申し訳ありませんが、そのような内容にはお答えできません。"
                }

            # キャッシュから応答をチェック（高速化）
            cache_check_start = time.perf_counter()
            cached_response = await query_cache.get_cached_response(
                rag_req.question, rag_req.top_k or 50
            )
            cache_check_duration = time.perf_counter() - cache_check_start
            
            if cached_response:
                total_duration = time.perf_counter() - start_time
                logger.info(f"🚀 Cache hit: {rag_req.question[:50]}... ({total_duration:.3f}s)")
                
                # キャッシュヒット時の最小パフォーマンス情報
                cached_response["performance"]["total_duration"] = total_duration
                cached_response["performance"]["cache_check_duration"] = cache_check_duration
                return cached_response

            # ハイブリッド検索の実行（最適化版）
            search_start = time.perf_counter()
            
            # 動的なtop_k調整（パフォーマンス最適化）
            optimized_top_k = rag_req.top_k or 50
            if optimized_top_k > 30:
                optimized_top_k = min(30, optimized_top_k)  # 最大30に制限
            
            search_result = await self.hybrid_search_service.search(
                rag_req.question, optimized_top_k
            )
            search_duration = time.perf_counter() - search_start
            
            # 5秒以上の場合は警告（Vector検索最適化のため）
            if search_duration > 4.0:
                logger.warning(f"⚠️ Slow search detected: {search_duration:.3f}s for '{rag_req.question[:50]}...'")
                bottleneck_detector.check_operation(
                    "hybrid_search",
                    search_duration,
                    {"question": rag_req.question[:100], "top_k": optimized_top_k}
                )
            
            context_items = search_result["merged_results"]  # ここは詳細json(dict)リスト
            
            # LLM応答生成をスキップし、answerは空文字で返す
            llm_duration = 0.0
            total_duration = time.perf_counter() - start_time
            logger.info(
                f"⏱️ RAG処理完了: total={total_duration:.3f}s, "
                f"search={search_duration:.3f}s, llm={llm_duration:.3f}s"
            )

            # レスポンス構築
            if rag_req.with_context:
                response = {
                    "answer": "",
                    "context": context_items,  # そのまま返す
                    "classification": search_result["classification"].model_dump(),
                    "search_info": {
                        "query_type": search_result["classification"].query_type,
                        "confidence": search_result["classification"].confidence,
                        "db_results_count": len(search_result["db_results"]),
                        "vector_results_count": len(search_result["vector_results"])
                    },
                    "performance": {
                        "total_duration": total_duration,
                        "search_duration": search_duration,
                        "llm_duration": llm_duration,
                        "cache_hit": False
                    }
                }
            else:
                response = {
                    "answer": "",
                    "performance": {
                        "total_duration": total_duration,
                        "search_duration": search_duration,
                        "llm_duration": llm_duration,
                        "cache_hit": False
                    }
                }
            
            # レスポンスをキャッシュ（非同期で実行、レスポンス時間に影響しない）
            asyncio.create_task(
                query_cache.cache_response(
                    rag_req.question, 
                    response, 
                    optimized_top_k,
                    ttl=1200 if total_duration < 3.0 else 600  # 高速レスポンスは長期キャッシュ
                )
            )
            
            return response
                
        except Exception as e:
            # エラーログを出力（raiseしないのでlogger.errorのみでOK）
            logger.error(f"RAGクエリ処理中にエラーが発生: {str(e)}", exc_info=True)
            return {
                "answer": f"申し訳ありませんが、「{rag_req.question}」に関する回答の処理中にエラーが発生しました。"
            }
    
    async def process_query_optimized(self, rag_req: RagRequest) -> Dict[str, Any]:
        """
        最適化されたRAGクエリ処理
        - キャッシュの積極活用
        - 並列処理の最適化
        - タイムアウト対策
        """
        start_time = time.perf_counter()
        
        try:
            # NGワードチェック
            if any(ng_word in rag_req.question for ng_word in NG_WORDS):
                return {
                    "answer": "申し訳ありませんが、そのような内容にはお答えできません。"
                }

            # 1. マルチレベルキャッシュチェック
            cached_response = await self._check_multilevel_cache(rag_req)
            if cached_response:
                cache_duration = time.perf_counter() - start_time
                logger.info(f"🚀 Multi-level cache hit: {rag_req.question[:50]}... ({cache_duration:.3f}s)")
                cached_response["performance"]["cache_hit"] = True
                return cached_response

            # 2. 並列検索実行（タイムアウト付き）
            search_result = await self._execute_parallel_search(rag_req)
            search_duration = search_result.get("_search_duration", 0)
            
            # 3. ストリーミング対応LLM応答生成
            llm_start = time.perf_counter()
            answer = await asyncio.wait_for(
                self._generate_answer_with_timeout(rag_req, search_result),
                timeout=10.0  # 10秒タイムアウト
            )
            llm_duration = time.perf_counter() - llm_start

            # 4. レスポンス構築とキャッシュ
            response = await self._build_and_cache_response(
                rag_req, answer, search_result, start_time, search_duration, llm_duration
            )
            
            return response
                
        except asyncio.TimeoutError:
            # タイムアウト時のフォールバック
            logger.warning(f"⏰ Query timeout: {rag_req.question[:50]}...")
            return {
                "answer": "申し訳ありませんが、回答の生成に時間がかかりすぎています。もう少し具体的な質問をお試しください。",
                "performance": {
                    "total_duration": time.perf_counter() - start_time,
                    "timeout": True
                }
            }
        except Exception as e:
            logger.error(f"RAG処理エラー: {e}")
            return {
                "answer": "申し訳ありませんが、エラーが発生しました。しばらく後に再試行してください。",
                "error": str(e),
                "performance": {
                    "total_duration": time.perf_counter() - start_time,
                    "error": True
                }
            }
    
    async def _check_multilevel_cache(self, rag_req: RagRequest) -> Optional[Dict[str, Any]]:
        """マルチレベルキャッシュチェック"""
        # レベル1: 完全一致キャッシュ
        exact_cache = await query_cache.get_cached_response(
            rag_req.question, rag_req.top_k or 50
        )
        if exact_cache:
            return exact_cache
        
        # レベル2: 類似クエリキャッシュ（簡易実装）
        similar_cache = await self._find_similar_cached_response(rag_req.question)
        if similar_cache:
            return similar_cache
        
        return None
    
    async def _find_similar_cached_response(self, question: str) -> Optional[Dict[str, Any]]:
        """類似クエリのキャッシュを検索"""
        # 簡易実装：キーワードベースの類似性チェック
        # question_words = set(question.lower().split())
        
        # キャッシュ統計から過去のクエリを取得（実装簡略化）
        # 実際のプロダクションではより高度な類似度計算が必要
        return None
    
    async def _execute_parallel_search(self, rag_req: RagRequest) -> Dict[str, Any]:
        """並列検索実行"""
        search_start = time.perf_counter()
        
        try:
            # 軽量なクエリ分類を並列実行（将来使用）
            # classification_task = asyncio.create_task(
            #     self.hybrid_search_service.classification_service.classify_query_lightweight(
            #         rag_req.question
            #     )
            # )
            
            # 検索処理を並列実行
            search_task = asyncio.create_task(
                asyncio.wait_for(
                    self.hybrid_search_service.search(rag_req.question, rag_req.top_k or 50),
                    timeout=15.0  # 検索は15秒でタイムアウト
                )
            )
            
            # 両方の完了を待機
            search_result = await search_task
            search_result["_search_duration"] = time.perf_counter() - search_start
            
            return search_result
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Search timeout: {rag_req.question[:50]}...")
            # フォールバック: 軽量な検索結果を返す
            return {
                "merged_results": [],
                "classification": None,
                "_search_duration": time.perf_counter() - search_start,
                "_timeout": True
            }
    
    async def _generate_answer_with_timeout(self, rag_req: RagRequest, search_result: Dict[str, Any]) -> str:
        """タイムアウト対応LLM応答生成"""
        context_items = search_result.get("merged_results", [])  # 詳細jsonリスト
        
        if not context_items or search_result.get("_timeout"):
            # 検索結果が無い、またはタイムアウトした場合のフォールバック
            return f"「{rag_req.question}」について、現在検索結果を取得できませんでした。もう少し具体的な質問をお試しください。"
        
        # LLM応答生成（バックグラウンドタスクとしても実行可能）
        answer = await self.llm_service.generate_answer(
            query=rag_req.question,
            context_items=context_items[:5],  # 上位5件のみ使用
            classification=search_result.get("classification")
        )
        
        return answer
    
    async def _build_and_cache_response(
        self, 
        rag_req: RagRequest, 
        answer: str, 
        search_result: Dict[str, Any],
        start_time: float,
        search_duration: float,
        llm_duration: float
    ) -> Dict[str, Any]:
        """レスポンス構築とキャッシュ"""
        total_duration = time.perf_counter() - start_time
        
        logger.info(
            f"⏱️ RAG処理完了: total={total_duration:.3f}s, "
            f"search={search_duration:.3f}s, llm={llm_duration:.3f}s"
        )
        
        # レスポンス構築
        context_items = search_result.get("merged_results", [])  # 詳細jsonリスト
        
        if rag_req.with_context:
            response = {
                "answer": "",
                "context": context_items[:10],  # 上位10件
                "classification": search_result.get("classification", {}).model_dump() if search_result.get("classification") else {},
                "search_info": {
                    "query_type": search_result.get("classification", {}).query_type if search_result.get("classification") else "unknown",
                    "confidence": search_result.get("classification", {}).confidence if search_result.get("classification") else 0.0,
                    "db_results_count": len(search_result.get("db_results", [])),
                    "vector_results_count": len(search_result.get("vector_results", []))
                },
                "performance": {
                    "total_duration": total_duration,
                    "search_duration": search_duration,
                    "llm_duration": llm_duration,
                    "cache_hit": False
                }
            }
        else:
            response = {
                "answer": "",
                "performance": {
                    "total_duration": total_duration,
                    "search_duration": search_duration,
                    "llm_duration": llm_duration,
                    "cache_hit": False
                }
            }
        
        # 高速レスポンスは長期キャッシュ、遅いレスポンスは短期キャッシュ
        cache_ttl = 1200 if total_duration < 3.0 else 300  # 20分 or 5分
        
        # 非同期でキャッシュ（レスポンス時間に影響しない）
        asyncio.create_task(
            query_cache.cache_response(
                rag_req.question, 
                response, 
                rag_req.top_k or 50,
                ttl=cache_ttl
            )
        )
        
        return response