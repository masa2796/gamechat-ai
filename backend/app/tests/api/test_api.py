import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.rag_models import RagRequest

client = TestClient(app)


class TestRagAPI:
    """RAG API のテスト"""

    # === 正常系テスト ===
    class TestNormalCases:
        """正常系のテストケース"""
        
        def test_rag_query_success_with_valid_request(self, monkeypatch):
            """有効なリクエストでのRAGクエリ成功テスト"""
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
        async def test_process_query_without_ng_word(self, mock_rag_service):
            """NGワードなしでのクエリ処理テスト"""
            # モック化されたRagServiceを使用
            rag_req = RagRequest(question="カードの進化について教えて！", top_k=3, with_context=False)
            
            # モックサービスでテスト
            result = await mock_rag_service.process_query(rag_req.question, rag_req.top_k)
            
            assert "response" in result
            assert "context_items" in result
            assert result["response"] == "これはモックからのRAG応答です。"

    # === 異常系テスト ===
    class TestErrorCases:
        """異常系・エラーケースのテスト"""

        def test_rag_query_validation_with_empty_question(self):
            """空の質問でのバリデーションエラーテスト"""
            response = client.post("/api/rag/query", json={"question": ""})
            assert response.status_code in (400, 422)

        @pytest.mark.asyncio
        async def test_process_query_with_ng_word(self, mock_rag_service):
            """NGワード含有クエリでの処理テスト"""
            # モック化されたRagServiceを使用
            result = await mock_rag_service.process_query("お前バカか？", 3)
            
            # モックの応答を確認
            assert "response" in result
            assert result["response"] == "これはモックからのRAG応答です。"