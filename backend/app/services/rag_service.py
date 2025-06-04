from app.models.rag_models import RagRequest
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService

class RagService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
    
    async def process_query(self, rag_req: RagRequest) -> dict:
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