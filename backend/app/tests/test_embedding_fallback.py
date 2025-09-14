import os

# Ensure no real OpenAI key so that EmbeddingService enters mock/fallback mode
os.environ.pop("BACKEND_OPENAI_API_KEY", None)
os.environ.setdefault("BACKEND_TESTING", "true")
os.environ.setdefault("BACKEND_MOCK_EXTERNAL_SERVICES", "true")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_returns_titles_in_fallback_mode():
    resp = client.post("/chat", json={"message": "フォールバックテスト", "top_k": 3, "with_context": True})
    assert resp.status_code == 200
    data = resp.json()
    # 基本構造
    assert "answer" in data
    assert isinstance(data.get("retrieved_titles"), list)
    # top_k 指定の範囲内で何らかのタイトルが返る（0件でもAPI成功だが、疑似ベクトル + ダミータイトル生成で>0想定）
    assert len(data["retrieved_titles"]) <= 3
    # context も with_context=True なので存在（0件可）
    assert "context" in data


def test_chat_without_context_flag():
    resp = client.post("/chat", json={"message": "context除外", "with_context": False})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    # with_context=False のため context は None または未含有（現実装は None 返却）
    assert data.get("context") in (None, [])
