import os
os.environ.setdefault("BACKEND_TESTING", "true")
os.environ.setdefault("BACKEND_MOCK_EXTERNAL_SERVICES", "true")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mvp_chat_basic():
    resp = client.post("/chat", json={"message": "テスト"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert data["answer"]
