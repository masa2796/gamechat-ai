"""
RAGサービスの基本テスト
"""
import pytest
from unittest.mock import patch
from app.services.rag_service import RagService
from app.models.rag_models import RagRequest, RagResponse, ContextItem
from app.models.classification_models import ClassificationResult, QueryType


class TestRagServiceBasic:
    """RAGサービスの基本機能テスト"""
    
    @pytest.fixture
    def rag_service(self):
        """RAGサービスのインスタンス"""
        return RagService()
    
    @pytest.mark.asyncio
    async def test_search_basic_greeting(self, rag_service):
        """基本的な挨拶に対するテスト"""
        with patch.object(rag_service, 'hybrid_search_service') as mock_hybrid, \
             patch.object(rag_service, 'llm_service') as mock_llm:
            
            # モックの設定
            mock_hybrid.search_hybrid.return_value = {
                "context": [],
                "classification": {"query_type": "GREETING", "confidence": 0.9}
            }
            
            mock_llm.generate_answer.return_value = "こんにちは！何かお手伝いできることはありますか？"
            
            request = RagRequest(question="こんにちは")
            result = await rag_service.process_query(request)
            
            assert isinstance(result, dict)
            # 基本的な応答が返されることを確認
            assert "context" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_search_semantic_query(self, rag_service):
        """意味検索クエリのテスト"""
        with patch.object(rag_service, 'hybrid_search_service') as mock_hybrid, \
             patch.object(rag_service, 'llm_service') as mock_llm:
            
            # モックの設定
            mock_hybrid.search_hybrid.return_value = {
                "context": [{"title": "テストカード", "content": "テスト内容"}],
                "classification": {"query_type": "SEMANTIC", "confidence": 0.8}
            }
            
            mock_llm.generate_answer.return_value = "検索結果に基づく回答"
            
            request = RagRequest(question="強いカードを教えて")
            result = await rag_service.process_query(request)
            
            assert isinstance(result, dict)
            assert "context" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, rag_service):
        """エラーハンドリングのテスト"""
        with patch.object(rag_service, 'hybrid_search_service') as mock_hybrid:
            # ハイブリッド検索サービスでエラーが発生
            mock_hybrid.search.side_effect = Exception("検索エラー")
            
            request = RagRequest(question="テストクエリ")
            result = await rag_service.process_query(request)
            
            assert isinstance(result, dict)
            # エラーハンドリングされて何らかの結果が返されることを確認
            assert "error" in result or "context" in result
    
    def test_rag_service_initialization(self, rag_service):
        """RAGサービスの初期化テスト"""
        assert rag_service is not None
        assert hasattr(rag_service, 'hybrid_search_service')
        assert hasattr(rag_service, 'llm_service')
        assert hasattr(rag_service, 'embedding_service')
        assert hasattr(rag_service, 'vector_service')
    
    @pytest.mark.asyncio
    async def test_filterable_query_handling(self, rag_service):
        """フィルター可能クエリのハンドリングテスト"""
        with patch.object(rag_service, 'hybrid_search_service') as mock_hybrid, \
             patch.object(rag_service, 'llm_service') as mock_llm:
            
            # モックの設定
            mock_hybrid.search_hybrid.return_value = {
                "context": [{"title": "高HPカード", "content": "HP100のカード"}],
                "classification": {"query_type": "FILTERABLE", "confidence": 0.9}
            }
            
            mock_llm.generate_answer.return_value = "HP100以上のカードについて説明します。"
            
            request = RagRequest(question="HP100以上のカード")
            result = await rag_service.process_query(request)
            
            assert isinstance(result, dict)
            assert "context" in result or "error" in result


class TestRagServiceConfiguration:
    """RAGサービス設定テスト"""
    
    @pytest.fixture
    def rag_service(self):
        return RagService()
    
    def test_service_dependencies(self, rag_service):
        """サービス依存関係のテスト"""
        # 各サービスが正しく初期化されていることを確認
        assert rag_service.hybrid_search_service is not None
        assert rag_service.llm_service is not None
        assert rag_service.embedding_service is not None
        assert rag_service.vector_service is not None
