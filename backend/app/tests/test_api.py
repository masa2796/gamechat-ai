import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.rag_service import RagService
from backend.app.models.rag_models import RagRequest

client = TestClient(app)

def test_rag_query_validation():
    response = client.post("/api/rag/query", json={"question": ""})
    assert response.status_code in (400, 422)

def test_rag_query_success(monkeypatch):
    async def mock_process_query(rag_req):
        return {"answer": "テスト回答", "context": []}

    async def mock_verify_request(*args, **kwargs):
        return True
    
    # ルーターのインスタンスを直接モックする
    from backend.app.routers import rag
    monkeypatch.setattr(rag.rag_service, "process_query", mock_process_query)
    monkeypatch.setattr(rag.auth_service, "verify_request", mock_verify_request)

    response = client.post("/api/rag/query", json={"question": "フシギダネのHPは？"})
    assert response.status_code == 200
    assert "answer" in response.json()

@pytest.mark.asyncio
async def test_process_query_with_ng_word():
    service = RagService()
    rag_req = RagRequest(question="お前バカか？", top_k=3, with_context=False)
    result = await service.process_query(rag_req)
    assert result["answer"] == "申し訳ありませんが、そのような内容にはお答えできません。"

@pytest.mark.asyncio
async def test_process_query_without_ng_word(monkeypatch):
    service = RagService()
    rag_req = RagRequest(question="ポケモンの進化について教えて！", top_k=3, with_context=False)

    async def mock_get_embedding(query):
        return [0.1, 0.2, 0.3]

    async def mock_search(query_embedding, top_k):
        return []

    async def mock_generate_answer(question, context_items):
        return "ポケモンの進化についての回答です。"

    monkeypatch.setattr(service.embedding_service, "get_embedding", mock_get_embedding)
    monkeypatch.setattr(service.vector_service, "search", mock_search)
    monkeypatch.setattr(service.llm_service, "generate_answer", mock_generate_answer)

    result = await service.process_query(rag_req)
    assert result["answer"] == "ポケモンの進化についての回答です。"