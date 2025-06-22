from typing import Dict, Any
from ..models.rag_models import RagRequest
from .embedding_service import EmbeddingService
from .vector_service import VectorService
from .llm_service import LLMService
from .hybrid_search_service import HybridSearchService
from ..config.ng_words import NG_WORDS

class RagService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        self.hybrid_search_service = HybridSearchService()
    
    async def process_query(self, rag_req: RagRequest) -> Dict[str, Any]:
        if any(ng_word in rag_req.question for ng_word in NG_WORDS):
            return {
                "answer": "申し訳ありませんが、そのような内容にはお答えできません。"
            }

        # 新しいハイブリッド検索フローを使用
        search_result = await self.hybrid_search_service.search(
            rag_req.question, rag_req.top_k or 50
        )
        
        context_items = search_result["merged_results"]
        
        # 分類結果と検索情報を含めて回答生成
        answer = await self.llm_service.generate_answer(
            query=rag_req.question,
            context_items=context_items,
            classification=search_result["classification"],
            search_info=search_result.get("search_quality", {})
        )
        
        if rag_req.with_context:
            return {
                "answer": answer,
                "context": [c.model_dump() for c in context_items],
                "classification": search_result["classification"].model_dump(),
                "search_info": {
                    "query_type": search_result["classification"].query_type,
                    "confidence": search_result["classification"].confidence,
                    "db_results_count": len(search_result["db_results"]),
                    "vector_results_count": len(search_result["vector_results"])
                }
            }
        else:
            return {"answer": answer}