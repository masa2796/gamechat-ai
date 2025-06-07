import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.rag_service import RagService
from app.services.auth_service import AuthService

client = TestClient(app)

def test_talk_guidelines_with_ng_word(monkeypatch):
    """
    NGワードが含まれる場合、定型文が返されることを確認するテスト
    """
    async def mock_process_query(self, rag_req):
        if "バカ" in rag_req.question:
            return {"answer": "申し訳ありませんが、そのような内容にはお答えできません。"}
        return {"answer": "通常の回答"}

    async def mock_verify_request(self, *args, **kwargs):
        return True

    monkeypatch.setattr(RagService, "process_query", mock_process_query)
    monkeypatch.setattr(AuthService, "verify_request", mock_verify_request)

    response = client.post("/api/rag/query", json={"question": "お前バカか？"})
    assert response.status_code == 200
    assert response.json()["answer"] == "申し訳ありませんが、そのような内容にはお答えできません。"

def test_talk_guidelines_without_ng_word(monkeypatch):
    """
    NGワードが含まれない場合、通常の応答が返されることを確認するテスト
    """
    async def mock_process_query(self, rag_req):
        return {"answer": "通常の回答"}

    async def mock_verify_request(self, *args, **kwargs):
        return True

    monkeypatch.setattr(RagService, "process_query", mock_process_query)
    monkeypatch.setattr(AuthService, "verify_request", mock_verify_request)

    response = client.post("/api/rag/query", json={"question": "ポケモンの進化について教えて！"})
    assert response.status_code == 200
    assert response.json()["answer"] == "通常の回答"

def test_talk_guidelines_responses(monkeypatch):
    """
    ガイドラインに記載された具体的な応答例をテスト
    """
    from app.services.rag_service import RagService
    from app.services.auth_service import AuthService

    async def mock_process_query(self, rag_req):
        if "こんにちは" in rag_req.question:
            return {"answer": "こんにちは！今日はどんなゲームの話をしましょうか？"}
        elif "バカ" in rag_req.question:
            return {"answer": "申し訳ありませんが、そのような内容にはお答えできません。"}
        elif "天気" in rag_req.question:
            return {"answer": "ゲームに関係のある話題に限定しています。"}
        return {"answer": "通常の回答"}

    async def mock_verify_request(self, *args, **kwargs):
        return True

    monkeypatch.setattr(RagService, "process_query", mock_process_query)
    monkeypatch.setattr(AuthService, "verify_request", mock_verify_request)

    # ガイドラインに基づくテストケース
    test_cases = [
        {"question": "こんにちは", "expected": "こんにちは！今日はどんなゲームの話をしましょうか？"},
        {"question": "お前バカか？", "expected": "申し訳ありませんが、そのような内容にはお答えできません。"},
        {"question": "今日の天気は？", "expected": "ゲームに関係のある話題に限定しています。"},
    ]

    for case in test_cases:
        response = client.post("/api/rag/query", json={"question": case["question"]})
        assert response.status_code == 200
        assert response.json()["answer"] == case["expected"]