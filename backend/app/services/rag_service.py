from fastapi import HTTPException
from ..models.rag_models import RagRequest
from .embedding_service import EmbeddingService
from .vector_service import VectorService
from .llm_service import LLMService
from ..config.ng_words import NG_WORDS

class RagService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
    
    async def process_query(self, rag_req: RagRequest) -> dict:
        if any(ng_word in rag_req.question for ng_word in NG_WORDS):
            return {
                "answer": "申し訳ありませんが、そのような内容にはお答えできません。"
            }

        query_embedding = await self.embedding_service.get_embedding(rag_req.question)
        context_items = await self.vector_service.search(
            query_embedding, rag_req.top_k
        )
        answer = await self.llm_service.generate_answer(rag_req.question, context_items)
        if rag_req.with_context:
            return {
                "answer": answer,
                "context": [c.model_dump() for c in context_items]
            }
        else:
            return {"answer": answer}