import pytest
from unittest.mock import AsyncMock
from backend.app.services.hybrid_search_service import HybridSearchService
from backend.app.models.classification_models import ClassificationResult, QueryType
from backend.app.models.rag_models import ContextItem
   
class TestHybridSearchService:
    """ハイブリッド検索サービスのテスト"""

    @pytest.fixture
    def hybrid_search_service(self):
        return HybridSearchService()

    @pytest.fixture
    def sample_context_items(self):
        """テスト用のContextItemサンプル"""
        return [
            ContextItem(title="DB結果1", text="データベースからの結果", score=0.9),
            ContextItem(title="DB結果2", text="データベースからの結果2", score=0.8),
            ContextItem(title="Vector結果1", text="ベクトル検索の結果", score=0.95),
            ContextItem(title="Vector結果2", text="ベクトル検索の結果2", score=0.85)
        ]

    @pytest.mark.asyncio
    async def test_search_filterable_query(self, hybrid_search_service, monkeypatch):
        """フィルター可能クエリの統合検索テスト"""
        # 分類サービスのモック
        mock_classification = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="HPが100以上のポケモン",
            confidence=0.9,
            filter_keywords=["HP", "100以上"],
            search_keywords=[]
        )
        
        # DB検索結果のモック
        mock_db_results = [
            ContextItem(title="高HPポケモン", text="HP120のポケモン", score=1.0)
        ]
        
        # サービスのモック化
        mock_classify = AsyncMock(return_value=mock_classification)
        mock_db_search = AsyncMock(return_value=mock_db_results)
        
        monkeypatch.setattr(hybrid_search_service.classification_service, "classify_query", mock_classify)
        monkeypatch.setattr(hybrid_search_service.database_service, "filter_search", mock_db_search)
        
        result = await hybrid_search_service.search("HPが100以上のポケモン", 3)
        
        assert result["classification"].query_type == QueryType.FILTERABLE
        assert len(result["db_results"]) == 1
        assert len(result["vector_results"]) == 0  # フィルターのみなのでベクトル検索なし
        assert len(result["merged_results"]) == 1

    @pytest.mark.asyncio
    async def test_search_semantic_query(self, hybrid_search_service, monkeypatch):
        """意味検索クエリの統合検索テスト"""
        # 分類サービスのモック
        mock_classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="強いポケモン",
            confidence=0.8,
            filter_keywords=[],
            search_keywords=["強い"]
        )
        
        # ベクトル検索結果のモック
        mock_vector_results = [
            ContextItem(title="強力なポケモン", text="攻撃力の高いポケモン", score=0.9)
        ]
        
        # サービスのモック化
        mock_classify = AsyncMock(return_value=mock_classification)
        mock_embedding = AsyncMock(return_value=[0.1] * 1536)
        mock_vector_search = AsyncMock(return_value=mock_vector_results)
        
        monkeypatch.setattr(hybrid_search_service.classification_service, "classify_query", mock_classify)
        monkeypatch.setattr(hybrid_search_service.embedding_service, "get_embedding_from_classification", mock_embedding)
        monkeypatch.setattr(hybrid_search_service.vector_service, "search", mock_vector_search)
        
        result = await hybrid_search_service.search("強いポケモンを教えて", 3)
        
        assert result["classification"].query_type == QueryType.SEMANTIC
        assert len(result["db_results"]) == 0  # 意味検索のみなのでDB検索なし
        assert len(result["vector_results"]) == 1
        assert len(result["merged_results"]) == 1

    @pytest.mark.asyncio
    async def test_search_hybrid_query(self, hybrid_search_service, monkeypatch):
        """ハイブリッドクエリの統合検索テスト"""
        # 分類サービスのモック
        mock_classification = ClassificationResult(
            query_type=QueryType.HYBRID,
            summary="炎タイプで強いポケモン",
            confidence=0.85,
            filter_keywords=["炎"],
            search_keywords=["強い"]
        )
        
        # 両方の検索結果のモック
        mock_db_results = [
            ContextItem(title="炎タイプポケモン", text="炎タイプのポケモン", score=0.8)
        ]
        mock_vector_results = [
            ContextItem(title="強力なポケモン", text="攻撃力の高いポケモン", score=0.9)
        ]
        
        # サービスのモック化
        mock_classify = AsyncMock(return_value=mock_classification)
        mock_db_search = AsyncMock(return_value=mock_db_results)
        mock_embedding = AsyncMock(return_value=[0.1] * 1536)
        mock_vector_search = AsyncMock(return_value=mock_vector_results)
        
        monkeypatch.setattr(hybrid_search_service.classification_service, "classify_query", mock_classify)
        monkeypatch.setattr(hybrid_search_service.database_service, "filter_search", mock_db_search)
        monkeypatch.setattr(hybrid_search_service.embedding_service, "get_embedding_from_classification", mock_embedding)
        monkeypatch.setattr(hybrid_search_service.vector_service, "search", mock_vector_search)
        
        result = await hybrid_search_service.search("炎タイプで強いポケモン", 3)
        
        assert result["classification"].query_type == QueryType.HYBRID
        assert len(result["db_results"]) == 1
        assert len(result["vector_results"]) == 1
        assert len(result["merged_results"]) == 2  # マージされた結果

    @pytest.mark.asyncio
    async def test_search_greeting_query(self, hybrid_search_service, monkeypatch):
        """挨拶クエリの検索スキップテスト"""
        # 分類サービスのモック（挨拶を返す）
        mock_classification = ClassificationResult(
            query_type=QueryType.GREETING,
            summary="挨拶",
            confidence=0.9,
            filter_keywords=[],
            search_keywords=[]
        )
        
        mock_classify = AsyncMock(return_value=mock_classification)
        monkeypatch.setattr(hybrid_search_service.classification_service, "classify_query", mock_classify)
        
        result = await hybrid_search_service.search("こんにちは", 3)
        
        # 挨拶の場合は検索をスキップ
        assert result["classification"].query_type == QueryType.GREETING
        assert result["search_strategy"]["skip_search"]
        assert result["search_strategy"]["reason"] == "greeting_detected"
        assert len(result["db_results"]) == 0
        assert len(result["vector_results"]) == 0
        assert len(result["merged_results"]) == 0
        assert result["search_quality"]["greeting_detected"]
        assert not result["search_quality"]["search_needed"]

    def test_merge_results_filterable_priority(self, hybrid_search_service, sample_context_items):
        """フィルター優先のマージテスト"""
        classification = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="テスト",
            confidence=0.9,
            filter_keywords=["テスト"],
            search_keywords=[]
        )
        
        db_results = sample_context_items[:2]  # DB結果2件
        vector_results = sample_context_items[2:]  # ベクトル結果2件
        
        merged = hybrid_search_service._merge_results(db_results, vector_results, classification, 3)
        
        # フィルター優先なのでDB結果が先に来る
        assert len(merged) == 3
        assert merged[0].title == "DB結果1"
        assert merged[1].title == "DB結果2"

    def test_merge_results_semantic_priority(self, hybrid_search_service, sample_context_items):
        """意味検索優先のマージテスト"""
        classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="テスト",
            confidence=0.8,
            filter_keywords=[],
            search_keywords=["テスト"]
        )
        
        db_results = sample_context_items[:2]
        vector_results = sample_context_items[2:]
        
        merged = hybrid_search_service._merge_results(db_results, vector_results, classification, 3)
        
        # 意味検索優先なのでベクトル結果が先に来る
        assert len(merged) == 3
        assert merged[0].title == "Vector結果1"
        assert merged[1].title == "Vector結果2"

    def test_merge_results_hybrid_weighted(self, hybrid_search_service, sample_context_items):
        """ハイブリッドの重み付きマージテスト"""
        classification = ClassificationResult(
            query_type=QueryType.HYBRID,
            summary="テスト",
            confidence=0.7,
            filter_keywords=["テスト"],
            search_keywords=["テスト"]
        )
        
        db_results = sample_context_items[:2]
        vector_results = sample_context_items[2:]
        
        merged = hybrid_search_service._merge_results(db_results, vector_results, classification, 4)
        
        # 重み付きマージで全4件
        assert len(merged) == 4
        # ベクトル結果の方が重みが大きいので上位に来る
        assert "[Vec]" in merged[0].title
        assert "[Vec]" in merged[1].title

    def test_merge_results_empty_inputs(self, hybrid_search_service):
        """空の入力でのマージテスト"""
        classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="テスト",
            confidence=0.5,
            filter_keywords=[],
            search_keywords=[]
        )
        
        # 両方空の場合
        merged = hybrid_search_service._merge_results([], [], classification, 3)
        assert len(merged) == 0
        
        # DB結果のみの場合
        db_results = [ContextItem(title="DB結果", text="テスト", score=0.8)]
        merged = hybrid_search_service._merge_results(db_results, [], classification, 3)
        assert len(merged) == 1
        assert merged[0].title == "DB結果"

    def test_weighted_merge(self, hybrid_search_service, sample_context_items):
        """重み付きマージのロジックテスト"""
        db_results = sample_context_items[:2]
        vector_results = sample_context_items[2:]
        
        merged = hybrid_search_service._weighted_merge(db_results, vector_results, 3)
        
        assert len(merged) == 3
        # スコア順でソートされている
        assert merged[0].score >= merged[1].score >= merged[2].score
        # DB結果は[DB]、ベクトル結果は[Vec]のプレフィックス
        db_count = sum(1 for item in merged if "[DB]" in item.title)
        vec_count = sum(1 for item in merged if "[Vec]" in item.title)
        assert db_count + vec_count == 3
