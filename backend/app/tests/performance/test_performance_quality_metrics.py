import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.hybrid_search_service import HybridSearchService
from app.services.rag_service import RagService
from app.models.rag_models import RagRequest, ContextItem
from app.models.classification_models import ClassificationResult, QueryType


class TestPerformanceQualityMetrics:
    """パフォーマンス・品質測定テスト"""

    @pytest.fixture
    def rag_service(self):
        return RagService()

    @pytest.fixture
    def hybrid_search_service(self):
        return HybridSearchService()

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, hybrid_search_service, monkeypatch):
        """メモリ使用量最適化のテスト"""
        
        # 大量の結果を返すモック（メモリ使用量テスト用）
        large_results = [
            ContextItem(
                title=f"結果{i}",
                text="長いテキスト" * 100,  # 意図的に長いテキスト
                score=0.8
            )
            for i in range(100)  # 100件の結果
        ]
        
        # 分類とサービスのモック
        mock_classification = ClassificationResult(
            query_type=QueryType.HYBRID,
            summary="大量結果テスト",
            confidence=0.8,
            search_keywords=["テスト"],
            filter_keywords=["大量"],
            reasoning="メモリテスト"
        )
        
        monkeypatch.setattr(
            hybrid_search_service.classification_service,
            "classify_query",
            AsyncMock(return_value=mock_classification)
        )
        monkeypatch.setattr(
            hybrid_search_service.database_service,
            "filter_search",
            AsyncMock(return_value=large_results)
        )
        monkeypatch.setattr(
            hybrid_search_service.vector_service,
            "search",
            AsyncMock(return_value=large_results)
        )
        monkeypatch.setattr(
            hybrid_search_service.embedding_service,
            "get_embedding_from_classification",
            AsyncMock(return_value=[0.1] * 1536)
        )
        
        # 大量データでの検索実行
        result = await hybrid_search_service.search("大量データテスト", top_k=5)
        
        # 結果が適切に制限されていることを確認（メモリ効率化）
        assert len(result["merged_results"]) <= 5  # top_kで制限
        assert len(result["db_results"]) <= 100    # モックが返す実際の件数
        assert len(result["vector_results"]) <= 100  # モックが返す実際の件数
        
        # 品質フィルタリングが機能していることを確認
        assert result["search_quality"]["result_count"] > 0
        assert "overall_score" in result["search_quality"]
