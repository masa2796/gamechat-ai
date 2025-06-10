import pytest
from unittest.mock import patch, AsyncMock
from backend.app.services.hybrid_search_service import HybridSearchService
from backend.app.models.rag_models import ContextItem
from backend.app.models.classification_models import ClassificationResult, QueryType, ClassificationRequest

class TestHybridSearchServiceOptimization:
    """最適化されたHybridSearchServiceのテスト"""

    @pytest.fixture
    def hybrid_service(self):
        return HybridSearchService()

    @pytest.fixture
    def mock_high_quality_db_results(self):
        return [
            ContextItem(title="フシギダネ", text="草タイプのたねポケモン", score=0.90),
            ContextItem(title="フシギソウ", text="草タイプの進化ポケモン", score=0.85),
            ContextItem(title="フシギバナ", text="草/毒タイプの最終進化", score=0.88)
        ]

    @pytest.fixture
    def mock_high_quality_vector_results(self):
        return [
            ContextItem(title="リザードン", text="炎/飛行タイプの最終進化", score=0.92),
            ContextItem(title="カメックス", text="水タイプの最終進化", score=0.89),
            ContextItem(title="ピカチュウ", text="電気タイプのマスコットポケモン", score=0.87)
        ]

    @pytest.fixture
    def mock_low_quality_results(self):
        return [
            ContextItem(title="関連性低1", text="あまり関連のない情報", score=0.35),
            ContextItem(title="関連性低2", text="別の関連のない情報", score=0.28)
        ]

    @pytest.fixture
    def mock_semantic_classification(self):
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="強いポケモンを探している",
            confidence=0.85,
            search_keywords=["強い", "ポケモン"],
            filter_keywords=[],
            reasoning="ユーザーは強力なポケモンを求めている"
        )

    @pytest.fixture
    def mock_hybrid_classification(self):
        return ClassificationResult(
            query_type=QueryType.HYBRID,
            summary="炎タイプで強いポケモン",
            confidence=0.90,
            search_keywords=["強い"],
            filter_keywords=["炎タイプ"],
            reasoning="タイプ条件と強さ条件の組み合わせ"
        )

    @pytest.fixture
    def mock_low_confidence_classification(self):
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="不明な要求",
            confidence=0.3,
            search_keywords=["不明"],
            filter_keywords=[],
            reasoning="意図が不明瞭"
        )

    @pytest.mark.asyncio
    async def test_optimized_search_quality_evaluation(
        self, 
        hybrid_service, 
        mock_semantic_classification,
        mock_high_quality_db_results,
        mock_high_quality_vector_results
    ):
        """検索品質評価の最適化テスト"""
        
        # 品質評価メソッドを直接テスト
        quality = hybrid_service._evaluate_search_quality(
            mock_high_quality_db_results,
            mock_high_quality_vector_results,
            mock_semantic_classification
        )
        
        # 高品質結果の評価
        assert quality["overall_score"] > 0.8
        assert quality["has_high_confidence_results"] is True
        assert quality["result_count"] == 6
        assert quality["avg_score"] > 0.85

    @pytest.mark.asyncio
    async def test_optimized_search_limits(self, hybrid_service):
        """最適化された検索制限のテスト"""
        
        # 高信頼度セマンティック分類
        high_confidence_semantic = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="テスト",
            confidence=0.9,
            search_keywords=[],
            filter_keywords=[],
            reasoning=""
        )
        
        limits = hybrid_service._get_optimized_limits(high_confidence_semantic, 10)
        
        # 高信頼度では制限が緩和される
        base_vector_limit = 15  # settings.VECTOR_SEARCH_CONFIG["search_limits"]["semantic"]["vector"]
        assert limits["vector_limit"] >= base_vector_limit
        
        # 低信頼度フィルタ可能分類
        low_confidence_filterable = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="テスト",
            confidence=0.4,
            search_keywords=[],
            filter_keywords=[],
            reasoning=""
        )
        
        limits = hybrid_service._get_optimized_limits(low_confidence_filterable, 10)
        
        # 低信頼度では制限が厳しくなる
        assert limits["vector_limit"] >= 5  # 最小値
        assert limits["db_limit"] >= 5      # 最小値

    @pytest.mark.asyncio
    async def test_inclusive_merge_for_low_quality(
        self, 
        hybrid_service,
        mock_semantic_classification,
        mock_low_quality_results
    ):
        """低品質時の包括的マージテスト"""
        
        # 低品質の検索品質を模擬
        low_quality = {
            "overall_score": 0.3,
            "has_high_confidence_results": False,
            "avg_score": 0.3
        }
        
        # 包括的マージが実行されることを確認
        result = hybrid_service._merge_results_inclusive(
            mock_low_quality_results,
            mock_low_quality_results,
            mock_semantic_classification,
            3
        )
        
        # 重複除去が行われることを確認
        titles = [item.title for item in result]
        assert len(titles) == len(set(titles))

    @pytest.mark.asyncio
    async def test_optimized_weighted_merge(
        self, 
        hybrid_service,
        mock_high_quality_db_results,
        mock_high_quality_vector_results
    ):
        """最適化された重み付きマージテスト"""
        
        result = hybrid_service._weighted_merge_optimized(
            mock_high_quality_db_results,
            mock_high_quality_vector_results,
            5
        )
        
        # 結果が適切にマージされている
        assert len(result) <= 5
        
        # 重み付けが適用されている（ベクトル結果が優先）
        # スコア順に並んでいることを確認
        scores = [item.score for item in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_no_results_handling(self, hybrid_service, mock_semantic_classification):
        """結果なし時の最適化処理テスト"""
        
        result = hybrid_service._handle_no_results_optimized(mock_semantic_classification)
        
        # 有用な提案が返される
        assert len(result) == 1
        assert "検索のご提案" in result[0].title
        assert "より具体的な" in result[0].text

    @pytest.mark.asyncio
    async def test_search_suggestion_generation(self, hybrid_service):
        """検索提案生成のテスト"""
        
        # セマンティック検索の提案
        semantic_classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="テスト",
            confidence=0.8,
            search_keywords=[],
            filter_keywords=[],
            reasoning=""
        )
        
        suggestion = hybrid_service._generate_search_suggestion(semantic_classification)
        assert "具体的なポケモン名" in suggestion
        assert "技" in suggestion or "HP" in suggestion
        
        # フィルタ可能検索の提案
        filterable_classification = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="テスト",
            confidence=0.8,
            search_keywords=[],
            filter_keywords=[],
            reasoning=""
        )
        
        suggestion = hybrid_service._generate_search_suggestion(filterable_classification)
        assert "数値条件を調整" in suggestion
        assert "複数条件を単一条件" in suggestion

    @pytest.mark.asyncio
    async def test_quality_based_filtering(
        self, 
        hybrid_service,
        mock_high_quality_vector_results,
        mock_low_quality_results
    ):
        """品質に基づくフィルタリングテスト"""
        
        # 高品質結果のフィルタリング
        high_quality = {"avg_score": 0.9}
        filtered_high = hybrid_service._filter_by_quality(
            mock_high_quality_vector_results, high_quality, 3
        )
        
        # 高品質結果はそのまま通る
        assert len(filtered_high) == 3
        
        # 低品質結果のフィルタリング
        low_quality = {"avg_score": 0.3}
        filtered_low = hybrid_service._filter_by_quality(
            mock_low_quality_results, low_quality, 3
        )
        
        # 低品質結果は除外されるか、1件のみ保持される
        assert len(filtered_low) <= 1

    @pytest.mark.asyncio
    async def test_end_to_end_optimization_flow(self, hybrid_service):
        """エンドツーエンドの最適化フローテスト"""
        
        # モックサービスを設定
        with patch.object(hybrid_service.classification_service, 'classify_query') as mock_classify, \
             patch.object(hybrid_service.classification_service, 'determine_search_strategy') as mock_strategy, \
             patch.object(hybrid_service.database_service, 'filter_search') as mock_db_search, \
             patch.object(hybrid_service.embedding_service, 'get_embedding_from_classification') as mock_embedding, \
             patch.object(hybrid_service.vector_service, 'search') as mock_vector_search:
            
            # モックの戻り値を設定
            mock_classify.return_value = ClassificationResult(
                query_type=QueryType.HYBRID,
                summary="炎タイプで強いポケモン",
                confidence=0.85,
                search_keywords=["強い"],
                filter_keywords=["炎タイプ"],
                reasoning="テスト"
            )
            
            mock_strategy.return_value = type('Strategy', (), {
                'use_db_filter': True,
                'use_vector_search': True
            })()
            
            mock_db_search.return_value = [
                ContextItem(title="リザードン", text="炎タイプのポケモン", score=0.9)
            ]
            
            mock_embedding.return_value = [0.1] * 1536
            
            mock_vector_search.return_value = [
                ContextItem(title="ブースター", text="炎タイプの進化ポケモン", score=0.85)
            ]
            
            # 最適化されたサーチを実行
            result = await hybrid_service.search("炎タイプで強いポケモン", top_k=3)
            
            # 最適化が適用されていることを確認
            assert result["optimization_applied"] is True
            assert "search_quality" in result
            assert len(result["merged_results"]) > 0
            
            # 検索品質が評価されていることを確認
            quality = result["search_quality"]
            assert "overall_score" in quality
            assert "result_count" in quality

class TestHybridSearchBackwardCompatibility:
    """下位互換性のテスト"""

    @pytest.fixture
    def hybrid_service(self):
        return HybridSearchService()

    def test_legacy_merge_methods_exist(self, hybrid_service):
        """レガシーマージメソッドが存在することを確認"""
        
        # レガシーメソッドが存在することを確認
        assert hasattr(hybrid_service, '_merge_results')
        assert hasattr(hybrid_service, '_weighted_merge')
        assert callable(hybrid_service._merge_results)
        assert callable(hybrid_service._weighted_merge)
