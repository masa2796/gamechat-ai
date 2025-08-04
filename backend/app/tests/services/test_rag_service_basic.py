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
        with patch.object(rag_service, 'classification_service') as mock_classification, \
             patch.object(rag_service, 'llm_service') as mock_llm:
            
            # モックの設定
            mock_classification.classify_query.return_value = ClassificationResult(
                query_type=QueryType.GREETING,
                confidence=0.9,
                summary="挨拶クエリ"
            )
            
            mock_llm.generate_greeting_response.return_value = "こんにちは！何かお手伝いできることはありますか？"
            
            request = RagRequest(query="こんにちは")
            result = await rag_service.search(request)
            
            assert isinstance(result, RagResponse)
            assert result.answer == "こんにちは！何かお手伝いできることはありますか？"
            assert result.query_type == QueryType.GREETING
    
    @pytest.mark.asyncio
    async def test_search_semantic_query(self, rag_service):
        """意味検索クエリのテスト"""
        with patch.object(rag_service, 'classification_service') as mock_classification, \
             patch.object(rag_service, 'hybrid_search_service') as mock_hybrid, \
             patch.object(rag_service, 'llm_service') as mock_llm:
            
            # モックの設定
            mock_classification.classify_query.return_value = ClassificationResult(
                query_type=QueryType.SEMANTIC,
                confidence=0.8,
                summary="カード検索クエリ"
            )
            
            mock_context_items = [
                ContextItem(title="テストカード", content="テスト内容", score=0.9)
            ]
            mock_hybrid.search.return_value = mock_context_items
            
            mock_llm.generate_answer.return_value = "テストカードについて説明します。"
            
            request = RagRequest(query="強いカードを教えて")
            result = await rag_service.search(request)
            
            assert isinstance(result, RagResponse)
            assert result.answer == "テストカードについて説明します。"
            assert result.query_type == QueryType.SEMANTIC
            assert len(result.context_items) == 1
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, rag_service):
        """エラーハンドリングのテスト"""
        with patch.object(rag_service, 'classification_service') as mock_classification:
            # 分類サービスでエラーが発生
            mock_classification.classify_query.side_effect = Exception("分類エラー")
            
            request = RagRequest(query="テストクエリ")
            result = await rag_service.search(request)
            
            # エラーが発生してもレスポンスが返される
            assert isinstance(result, RagResponse)
            assert "申し訳" in result.answer or "エラー" in result.answer
    
    def test_rag_service_initialization(self, rag_service):
        """RAGサービスの初期化テスト"""
        assert rag_service is not None
        assert hasattr(rag_service, 'classification_service')
        assert hasattr(rag_service, 'hybrid_search_service')
        assert hasattr(rag_service, 'llm_service')
    
    @pytest.mark.asyncio
    async def test_filterable_query_handling(self, rag_service):
        """フィルター可能クエリのハンドリングテスト"""
        with patch.object(rag_service, 'classification_service') as mock_classification, \
             patch.object(rag_service, 'database_service') as mock_database, \
             patch.object(rag_service, 'llm_service') as mock_llm:
            
            # モックの設定
            mock_classification.classify_query.return_value = ClassificationResult(
                query_type=QueryType.FILTERABLE,
                confidence=0.9,
                summary="フィルター検索",
                filter_keywords=["HP", "100"]
            )
            
            mock_context_items = [
                ContextItem(title="高HPカード", content="HP100のカード", score=1.0)
            ]
            mock_database.filter_search.return_value = mock_context_items
            
            mock_llm.generate_answer.return_value = "HP100以上のカードについて説明します。"
            
            request = RagRequest(query="HP100以上のカード")
            result = await rag_service.search(request)
            
            assert isinstance(result, RagResponse)
            assert result.query_type == QueryType.FILTERABLE
            assert len(result.context_items) == 1


class TestRagServiceConfiguration:
    """RAGサービス設定テスト"""
    
    @pytest.fixture
    def rag_service(self):
        return RagService()
    
    def test_service_dependencies(self, rag_service):
        """サービス依存関係のテスト"""
        # 各サービスが正しく初期化されていることを確認
        assert rag_service.classification_service is not None
        assert rag_service.hybrid_search_service is not None
        assert rag_service.database_service is not None
        assert rag_service.llm_service is not None
