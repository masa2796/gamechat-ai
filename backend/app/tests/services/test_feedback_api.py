import pytest
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

@pytest.mark.asyncio
async def test_feedback_flow(monkeypatch):
    # モックRAGで query_id を返す
    from app.routers import rag
    async def mock_process_query(rag_req):
        return {"context": [], "classification": {}, "search_info": {}, "query_id": "test-query-123"}
    async def mock_verify_request(*args, **kwargs):
        return True
    monkeypatch.setattr(rag.rag_service, "process_query", mock_process_query)
    monkeypatch.setattr(rag.auth_service, "verify_request", mock_verify_request)

    # まずクエリ実行
    res = client.post("/api/rag/query", json={"question": "テスト"})
    assert res.status_code == 200
    qid = res.json().get("query_id") or "test-query-123"

    # QueryContext が無い状態でも feedback submit が動作することを確認
    fb_res = client.post("/api/feedback", json={"query_id": qid, "rating": -1})
    assert fb_res.status_code == 200
    data = fb_res.json()["data"]
    assert data["query_id"] == qid
    assert data["rating"] == -1

    # recent 取得
    recent = client.get("/api/feedback/recent")
    assert recent.status_code == 200
    items = recent.json().get("items", [])
    assert len(items) >= 1
