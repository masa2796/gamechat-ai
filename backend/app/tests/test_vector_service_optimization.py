import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.vector_service import VectorService
from backend.app.models.rag_models import ContextItem
from backend.app.models.classification_models import ClassificationResult, QueryType
from backend.app.core.config import settings

class TestVectorServiceOptimization:
    """最適化されたVectorServiceのテスト"""

    @pytest.fixture
    def vector_service(self):
        return VectorService()

    @pytest.fixture
    def mock_classification_semantic(self):
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="強いポケモンの検索",
            confidence=0.85,
            search_keywords=["強い", "ポケモン"],
            filter_keywords=[],
            reasoning="セマンティック検索として分類"
        )

    @pytest.fixture
    def mock_classification_filterable(self):
        return ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="HP100以上のポケモン",
            confidence=0.90,
            search_keywords=[],
            filter_keywords=["HP", "100"],
            reasoning="フィルタ可能として分類"
        )

    @pytest.fixture
    def mock_classification_low_confidence(self):
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="不明な検索",
            confidence=0.3,
            search_keywords=["不明"],
            filter_keywords=[],
            reasoning="低信頼度分類"
        )

    @pytest.fixture
    def mock_upstash_high_score_results(self):
        """高スコアの検索結果をモック"""
        class MockMatch:
            def __init__(self, score, title, text):
                self.score = score
                self.metadata = {"title": title, "text": text}
                self.id = f"id-{title}"
        
        class MockResult:
            matches = [
                MockMatch(0.95, "フシギダネ", "フシギダネは草タイプのたねポケモンです。"),
                MockMatch(0.87, "リザードン", "リザードンは炎・飛行タイプのポケモンです。"),
                MockMatch(0.82, "カメックス", "カメックスは水タイプのポケモンです。")
            ]
        
        return MockResult()

    @pytest.fixture
    def mock_upstash_low_score_results(self):
        """低スコアの検索結果をモック"""
        class MockMatch:
            def __init__(self, score, title, text):
                self.score = score
                self.metadata = {"title": title, "text": text}
                self.id = f"id-{title}"
        
        class MockResult:
            matches = [
                MockMatch(0.35, "低関連性1", "あまり関連のない情報です。"),
                MockMatch(0.28, "低関連性2", "別の関連のない情報です。")
            ]
        
        return MockResult()

    @pytest.mark.asyncio
    async def test_optimized_search_with_high_confidence_semantic(
        self, vector_service, mock_classification_semantic, mock_upstash_high_score_results
    ):
        """高信頼度セマンティック検索の最適化テスト"""
        
        with patch.object(vector_service.vector_index, 'query', return_value=mock_upstash_high_score_results):
            result = await vector_service.search(
                query_embedding=[0.1] * 1536,
                top_k=10,
                classification=mock_classification_semantic
            )
            
            # 結果が適切に取得されることを確認
            assert len(result) > 0
            assert all(isinstance(item, ContextItem) for item in result)
            
            # 最適化されたネームスペースが使用されることを確認（セマンティック優先）
            # セマンティック検索では要約や説明が優先される
            
            # 高スコア結果のみが含まれることを確認
            assert all(item.score >= settings.VECTOR_SEARCH_CONFIG["minimum_score"] for item in result)

    @pytest.mark.asyncio
    async def test_optimized_search_with_filterable_type(
        self, vector_service, mock_classification_filterable, mock_upstash_high_score_results
    ):
        """フィルタ可能タイプの最適化テスト"""
        
        with patch.object(vector_service.vector_index, 'query', return_value=mock_upstash_high_score_results):
            result = await vector_service.search(
                query_embedding=[0.1] * 1536,
                top_k=5,
                classification=mock_classification_filterable
            )
            
            # フィルタ可能検索では具体的属性が優先される
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_low_score_filtering(
        self, vector_service, mock_classification_semantic, mock_upstash_low_score_results
    ):
        """低スコア結果のフィルタリングテスト"""
        
        with patch.object(vector_service.vector_index, 'query', return_value=mock_upstash_low_score_results):
            result = await vector_service.search(
                query_embedding=[0.1] * 1536,
                top_k=10,
                classification=mock_classification_semantic
            )
            
            # 低スコア結果は除外されるべき
            if result:
                # フォールバック結果が返される場合
                assert len(result) == 1
                assert "検索結果について" in result[0].title or "エラー" in result[0].title
            else:
                # 空の結果が返される場合
                assert len(result) == 0

    @pytest.mark.asyncio
    async def test_confidence_based_parameter_optimization(
        self, vector_service, mock_classification_low_confidence
    ):
        """信頼度に基づくパラメータ最適化テスト"""
        
        # 低信頼度の場合、パラメータが調整されることを確認
        top_k = 20
        min_score = None
        namespaces = None
        
        optimized_top_k, optimized_min_score, optimized_namespaces = vector_service._optimize_search_params(
            mock_classification_low_confidence, top_k, min_score, namespaces
        )
        
        # 低信頼度では検索件数が制限される
        expected_limit = settings.VECTOR_SEARCH_CONFIG["search_limits"]["semantic"]["vector"]
        assert optimized_top_k <= expected_limit
        
        # 低信頼度では閾値が調整される
        assert optimized_min_score > settings.VECTOR_SEARCH_CONFIG["minimum_score"]

    @pytest.mark.asyncio
    async def test_namespace_optimization_by_type(self, vector_service):
        """タイプ別ネームスペース最適化テスト"""
        
        # セマンティック検索のネームスペース
        semantic_classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="テスト",
            confidence=0.8,
            search_keywords=[],
            filter_keywords=[],
            reasoning=""
        )
        semantic_namespaces = vector_service._get_optimized_namespaces(semantic_classification)
        
        # セマンティック検索では要約が最初に来る
        assert semantic_namespaces[0] == "summary"
        assert "flavor" in semantic_namespaces[:3]
        
        # フィルタ可能検索のネームスペース
        filterable_classification = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="テスト",
            confidence=0.8,
            search_keywords=[],
            filter_keywords=[],
            reasoning=""
        )
        filterable_namespaces = vector_service._get_optimized_namespaces(filterable_classification)
        
        # フィルタ可能検索では具体的属性が最初に来る
        assert "hp" in filterable_namespaces[:3]
        assert "type" in filterable_namespaces[:3]

    @pytest.mark.asyncio
    async def test_fallback_message_generation(self, vector_service):
        """フォールバックメッセージ生成テスト"""
        
        # セマンティック検索のフォールバック
        semantic_classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="強いポケモン",
            confidence=0.8,
            search_keywords=["強い"],
            filter_keywords=[],
            reasoning=""
        )
        
        message = vector_service._generate_fallback_message(semantic_classification)
        assert "強いポケモン" in message
        assert "具体的なポケモン名" in message
        
        # フィルタ可能検索のフォールバック
        filterable_classification = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="HP条件",
            confidence=0.8,
            search_keywords=[],
            filter_keywords=["HP", "100"],
            reasoning=""
        )
        
        message = vector_service._generate_fallback_message(filterable_classification)
        assert "HP, 100" in message
        assert "検索条件を変更" in message

    @pytest.mark.asyncio
    async def test_search_error_handling(self, vector_service, mock_classification_semantic):
        """検索エラーハンドリングテスト"""
        
        # vector_index.queryがエラーを発生させる
        with patch.object(vector_service.vector_index, 'query', side_effect=Exception("接続エラー")):
            result = await vector_service.search(
                query_embedding=[0.1] * 1536,
                classification=mock_classification_semantic
            )
            
            # エラー時もフォールバック結果が返される
            assert len(result) == 1
            # ネームスペース毎のエラーは個別処理され、全体エラーではなく「結果なし」として処理される
            assert "検索結果について" in result[0].title or "エラー" in result[0].title
            assert result[0].score <= 0.1  # フォールバックまたはエラーの低スコア

class TestVectorServiceConfiguration:
    """VectorService設定のテスト"""

    def test_configuration_values(self):
        """設定値が適切に定義されているかテスト"""
        
        config = settings.VECTOR_SEARCH_CONFIG
        
        # 必要な設定項目が存在することを確認
        assert "similarity_thresholds" in config
        assert "search_limits" in config
        assert "confidence_adjustments" in config
        assert "merge_weights" in config
        assert "minimum_score" in config
        assert "fallback_enabled" in config
        
        # 類似度閾値が適切な範囲にあることを確認
        for threshold in config["similarity_thresholds"].values():
            assert 0.0 <= threshold <= 1.0
        
        # 信頼度調整係数が適切な範囲にあることを確認
        for adjustment in config["confidence_adjustments"].values():
            assert 0.0 <= adjustment <= 1.0
        
        # 重み付け係数の合計が1.0であることを確認
        db_weight = config["merge_weights"]["db_weight"]
        vector_weight = config["merge_weights"]["vector_weight"]
        assert abs((db_weight + vector_weight) - 1.0) < 0.01
