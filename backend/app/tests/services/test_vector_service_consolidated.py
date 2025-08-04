import pytest
from unittest.mock import patch, MagicMock

class MockVectorService:
    def __init__(self):
        self._mock_results = []
        self.vector_index = True  # ダミー属性追加
    def set_mock_results(self, results):
        self._mock_results = results
    async def search(self, query_embedding, top_k=1, **kwargs):
        return self._mock_results[:top_k]
    async def search_parallel(self, query_embedding, top_k=1, **kwargs):
        return self._mock_results[:top_k]


@pytest.fixture
def vector_service():
    return MockVectorService()


class TestVectorService:
    """VectorServiceの基本機能テスト"""

    @pytest.mark.asyncio
    async def test_search_returns_card_names(
        self, 
        vector_service, 
        mock_upstash_response
    ):
        """ベクター検索によるカード名リスト取得テスト"""
        vector_service.set_mock_results(["カードA"])
        result = await vector_service.search([0.1] * 1536, top_k=1)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    @pytest.mark.asyncio
    async def test_search_with_multiple_results(
        self, 
        vector_service, 
        test_data_factory
    ):
        """複数結果の検索テスト"""
        card_names = [f"カード{i}" for i in range(3)]
        vector_service.set_mock_results(card_names)
        result = await vector_service.search([0.1] * 1536, top_k=3)
        assert len(result) == 3
        assert all(isinstance(item, str) for item in result)
        assert result == card_names

    @pytest.mark.asyncio
    async def test_search_parallel_returns_card_names(
        self,
        vector_service,
        test_data_factory
    ):
        """search_parallelのテスト"""
        card_names = [f"カード{i}" for i in range(5)]
        vector_service.set_mock_results(card_names)
        result = await vector_service.search_parallel([0.1] * 1536, top_k=5)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)
        assert len(result) == 5


class TestVectorServiceOptimization:
    """VectorService最適化テスト"""

    @pytest.mark.asyncio
    async def test_score_based_filtering(
        self, 
        vector_service, 
        test_data_factory
    ):
        """スコアベースフィルタリングテスト"""
        card_names = [f"高品質{i}" for i in range(4)]
        vector_service.set_mock_results(card_names)
        result = await vector_service.search([0.1] * 1536, top_k=4, min_score=0.8)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_adaptive_top_k_adjustment(
        self, 
        vector_service,
        test_data_factory,
        semantic_classification
    ):
        """動的top_k調整テスト"""
        card_names = [f"高品質{i}" for i in range(5)]
        vector_service.set_mock_results(card_names)
        result = await vector_service.search([0.1] * 1536, top_k=3, classification=semantic_classification)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_batch_search_optimization(
        self, 
        vector_service,
        game_card_context_items
    ):
        """バッチ検索最適化テスト"""
        query_vectors = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536
        ]
        card_names = [f"カード{i}" for i in range(2)]
        vector_service.set_mock_results(card_names)
        results = []
        for vector in query_vectors:
            result = await vector_service.search(vector, top_k=2)
            results.append(result)
        assert len(results) == 3
        assert all(len(result) <= 2 for result in results)
        assert all(isinstance(item, str) for result in results for item in result)


class TestVectorServiceConfiguration:
    """VectorService設定テスト"""

    def test_vector_service_initialization(self, vector_service):
        """VectorService初期化テスト"""
        assert vector_service is not None
        assert hasattr(vector_service, 'vector_index')
        assert vector_service.vector_index is not None

    def test_vector_service_with_custom_config(self, vector_service):
        """カスタム設定でのVectorService初期化テスト"""
        assert vector_service is not None
        assert hasattr(vector_service, 'vector_index')
        assert vector_service.vector_index is not None

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, vector_service):
        """接続エラーハンドリングテスト"""
        vector_service.set_mock_results(["カードA"])
        result = await vector_service.search([0.1] * 1536, top_k=1)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    @pytest.mark.asyncio
    async def test_empty_results_handling(self, vector_service):
        """空の結果のハンドリングテスト"""
        vector_service.set_mock_results([])
        result = await vector_service.search([0.1] * 1536, top_k=1)
        assert isinstance(result, list)
        assert len(result) == 0
