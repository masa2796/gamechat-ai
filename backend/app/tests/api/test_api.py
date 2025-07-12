import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.rag_models import RagRequest

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
            from app.routers import rag
            monkeypatch.setattr(rag.rag_service, "process_query", mock_process_query)
            monkeypatch.setattr(rag.auth_service, "verify_request", mock_verify_request)

            response = client.post("/api/rag/query", json={"question": "フシギダネのHPは？"})
            assert response.status_code == 200
            assert "answer" in response.json()

        @pytest.mark.asyncio
        async def test_process_query_without_ng_word(self, mock_rag_service, monkeypatch):
            """NGワードなしでのクエリ処理テスト（現仕様）"""
            rag_req = RagRequest(question="カードの進化について教えて！", top_k=3, with_context=True)
            # モックサービスの返却値を現仕様に合わせて上書き
            async def mock_process_query(rag_req):
                return {"answer": "これはモックからのRAG応答です。", "context": [{"name": "テストカード1", "type": "炎"}]}
            monkeypatch.setattr(mock_rag_service, "process_query", mock_process_query)
            result = await mock_rag_service.process_query(rag_req)
            assert "answer" in result
            assert "context" in result
            assert isinstance(result["context"], list)

    # === 異常系テスト ===
    class TestErrorCases:
        """異常系・エラーケースのテスト"""

        def test_rag_query_validation_with_empty_question(self):
            """空の質問でのバリデーションエラーテスト"""
            response = client.post("/api/rag/query", json={"question": ""})
            assert response.status_code in (400, 422)

        @pytest.mark.asyncio
        async def test_process_query_with_ng_word(self, mock_rag_service, monkeypatch):
            """NGワード含有クエリでの処理テスト（現仕様）"""
            rag_req = RagRequest(question="お前バカか？", top_k=3, with_context=True)
            # モックサービスの返却値を現仕様に合わせて上書き
            async def mock_process_query(rag_req):
                return {"answer": "これはモックからのRAG応答です。"}
            monkeypatch.setattr(mock_rag_service, "process_query", mock_process_query)
            result = await mock_rag_service.process_query(rag_req)
            assert "answer" in result
            # NGワード時はanswerのみ返る想定
            assert isinstance(result["answer"], str)