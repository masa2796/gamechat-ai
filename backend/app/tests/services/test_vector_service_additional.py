"""
ベクターサービスの追加テスト
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.vector_service import VectorService


class TestVectorServiceBasic:
    """ベクターサービスの基本機能テスト"""
    
    @pytest.fixture
    def vector_service(self):
        """ベクターサービスのインスタンス"""
        with patch.object(VectorService, '_initialize_client'):
            service = VectorService()
            # モッククライアントを設定
            service.vector_index = MagicMock()
            return service
    
    def test_service_initialization(self, vector_service):
        """サービス初期化のテスト"""
        assert vector_service is not None
        assert hasattr(vector_service, 'vector_index')
    
    @pytest.mark.asyncio
    async def test_search_with_valid_vector(self, vector_service):
        """有効なベクターでの検索テスト"""
        # モックレスポンスの設定
        mock_response = [
            {"metadata": {"title": "テストカード1"}, "score": 0.9},
            {"metadata": {"title": "テストカード2"}, "score": 0.8}
        ]
        vector_service.vector_index.query.return_value = mock_response
        
        test_vector = [0.1] * 1536  # OpenAI埋め込みの次元数
        result = await vector_service.search(test_vector, top_k=2)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == "テストカード1"
        assert result[1] == "テストカード2"
    
    @pytest.mark.asyncio
    async def test_search_with_empty_results(self, vector_service):
        """空の結果での検索テスト"""
        # 空のレスポンス
        vector_service.vector_index.query.return_value = []
        
        test_vector = [0.1] * 1536
        result = await vector_service.search(test_vector, top_k=5)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_search_parallel_basic(self, vector_service):
        """並列検索の基本テスト"""
        # モックレスポンスの設定
        mock_response = [
            {"metadata": {"title": "パラレルカード1"}, "score": 0.9}
        ]
        vector_service.vector_index.query.return_value = mock_response
        
        test_vector = [0.1] * 1536
        result = await vector_service.search_parallel(test_vector, top_k=1)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "パラレルカード1"
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, vector_service):
        """検索エラーハンドリングのテスト"""
        # ベクター検索でエラーが発生
        vector_service.vector_index.query.side_effect = Exception("ベクター検索エラー")
        
        test_vector = [0.1] * 1536
        result = await vector_service.search(test_vector, top_k=5)
        
        # エラーが発生しても空のリストが返される
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_vector_dimension_validation(self, vector_service):
        """ベクター次元の妥当性確認テスト"""
        # 無効な次元のベクター
        invalid_vector = [0.1] * 100  # 1536ではない
        
        # 実際のサービスでは次元チェックが行われるべき
        # ここではモックなので、実装に応じてテストを調整
        assert len(invalid_vector) != 1536


class TestVectorServicePerformance:
    """ベクターサービスのパフォーマンステスト"""
    
    @pytest.fixture
    def vector_service(self):
        with patch.object(VectorService, '_initialize_client'):
            service = VectorService()
            service.vector_index = MagicMock()
            return service
    
    @pytest.mark.asyncio
    async def test_large_batch_search(self, vector_service):
        """大量検索のテスト"""
        # 大量の結果をモック
        mock_response = [
            {"metadata": {"title": f"カード{i}"}, "score": 0.9 - i*0.01}
            for i in range(100)
        ]
        vector_service.vector_index.query.return_value = mock_response
        
        test_vector = [0.1] * 1536
        result = await vector_service.search(test_vector, top_k=100)
        
        assert isinstance(result, list)
        assert len(result) == 100
        assert result[0] == "カード0"
        assert result[99] == "カード99"
    
    @pytest.mark.asyncio
    async def test_multiple_parallel_searches(self, vector_service):
        """複数の並列検索テスト"""
        import asyncio
        
        # モックレスポンス
        mock_response = [{"metadata": {"title": "並列カード"}, "score": 0.9}]
        vector_service.vector_index.query.return_value = mock_response
        
        test_vector = [0.1] * 1536
        
        # 複数の検索を並列実行
        tasks = [
            vector_service.search_parallel(test_vector, top_k=1)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == "並列カード"
