import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.rag_service import RagService
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
        async def test_process_query_without_ng_word(self, monkeypatch):
            """NGワードなしでのクエリ処理テスト"""
            service = RagService()
            rag_req = RagRequest(question="カードの進化について教えて！", top_k=3, with_context=False)

            async def mock_get_embedding(query):
                return [0.1, 0.2, 0.3]

            async def mock_search(query_embedding, top_k):
                return []

            async def mock_generate_answer(query, context_items, classification=None, search_info=None):
                return "カードの進化についての回答です。"

            # ハイブリッド検索サービス全体をモック
            async def mock_hybrid_search(query, top_k):
                return {
                    "classification": {
                        "query_type": "semantic",
                        "summary": query,
                        "confidence": 0.8
                    },
                    "search_strategy": {
                        "use_database": False,
                        "use_vector": True
                    },
                    "db_results": [],
                    "vector_results": [],
                    "merged_results": []
                }

            monkeypatch.setattr(service.hybrid_search_service, "search", mock_hybrid_search)
            monkeypatch.setattr(service.llm_service, "generate_answer", mock_generate_answer)

            result = await service.process_query(rag_req)
            assert result["answer"] == "カードの進化についての回答です。"

    # === 異常系テスト ===
    class TestErrorCases:
        """異常系・エラーケースのテスト"""

        def test_rag_query_validation_with_empty_question(self):
            """空の質問でのバリデーションエラーテスト"""
            response = client.post("/api/rag/query", json={"question": ""})
            assert response.status_code in (400, 422)

        @pytest.mark.asyncio
        async def test_process_query_with_ng_word(self):
            """NGワード含有クエリでの処理テスト"""
            service = RagService()
            rag_req = RagRequest(question="お前バカか？", top_k=3, with_context=False)
            result = await service.process_query(rag_req)
            assert result["answer"] == "申し訳ありませんが、そのような内容にはお答えできません。"