import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rag_query_validation():
    response = client.post("/api/rag/query", json={"question": ""})
    assert response.status_code in (400, 422)

def test_rag_query_success(monkeypatch):
    from app.services.rag_service import RagService
    from app.services.auth_service import AuthService

    async def mock_process_query(self, rag_req):
        return {"answer": "テスト回答", "context": []}

    async def mock_verify_request(self, *args, **kwargs):
        return True
    monkeypatch.setattr(RagService, "process_query", mock_process_query)
    monkeypatch.setattr(AuthService, "verify_request", mock_verify_request)

    response = client.post("/api/rag/query", json={"question": "フシギダネのHPは？"})
    assert response.status_code == 200
    assert "answer" in response.json()