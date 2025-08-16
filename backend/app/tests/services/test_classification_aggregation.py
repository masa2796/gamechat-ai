import pytest
import os
from app.services.classification_service import ClassificationService
from app.models.classification_models import ClassificationRequest, QueryType


class TestClassificationAggregation:
    """集約クエリと複雑な数値条件の分類テスト（実際の分類ロジック使用）"""

    def setup_method(self):
        """テスト前のセットアップ - モック環境でテスト"""
        os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"
        self.service = ClassificationService()

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if "BACKEND_MOCK_EXTERNAL_SERVICES" in os.environ:
            del os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"]

    @pytest.mark.asyncio
    async def test_classify_aggregation_max_query(self):
        """最大値集約クエリの分類テスト"""
        queries = [
            "一番高いHPのカード",
            "最大ダメージのカード", 
            "最高コストのカード",
            "HPがトップのカード"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.FILTERABLE
            assert "一番高い" in str(result.filter_keywords) or "最大" in str(result.filter_keywords) or "最高" in str(result.filter_keywords) or "トップ" in str(result.filter_keywords)
            assert any(field in str(result.filter_keywords) for field in ["HP", "ダメージ", "コスト"])

    @pytest.mark.asyncio
    async def test_classify_aggregation_min_query(self):
        """最小値集約クエリの分類テスト"""
        queries = [
            "一番低いHPのカード",
            "最小コストのカード",
            "最低ダメージのカード", 
            "HPがボトムのカード"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.FILTERABLE
            assert any(keyword in str(result.filter_keywords) for keyword in ["一番低い", "最小", "最低", "ボトム"])
            assert any(field in str(result.filter_keywords) for field in ["HP", "コスト", "ダメージ"])

    @pytest.mark.asyncio
    async def test_classify_aggregation_top_n_query(self):
        """上位N件集約クエリの分類テスト"""
        queries = [
            "上位3位のHPカード",
            "トップ5のダメージカード",
            "ベスト3のコストカード"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.FILTERABLE
            assert any(keyword in str(result.filter_keywords) for keyword in ["上位", "トップ", "ベスト"])

    @pytest.mark.asyncio
    async def test_classify_complex_numeric_range_query(self):
        """数値範囲条件の分類テスト"""
        queries = [
            "HPが50から100の間のカード",
            "コスト3～5のカード",
            "ダメージが10から20の範囲のカード"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.FILTERABLE
            # 数値パターンが検出されることを確認
            filter_str = str(result.filter_keywords)
            assert any(field in filter_str for field in ["HP", "コスト", "ダメージ"])

    @pytest.mark.asyncio
    async def test_classify_complex_numeric_multiple_values(self):
        """複数値条件の分類テスト"""
        queries = [
            "コスト1または3のカード",
            "HPが50か100のカード",
            "ファイアタイプまたは水タイプのカード"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.FILTERABLE
            assert "または" in str(result.filter_keywords) or "か" in str(result.filter_keywords) or "まで" in str(result.filter_keywords)

    @pytest.mark.asyncio
    async def test_classify_complex_numeric_approximate(self):
        """近似値条件の分類テスト"""
        queries = [
            "約100のHP",
            "50程度のダメージ",
            "およそ3のコスト"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.FILTERABLE
            filter_str = str(result.filter_keywords)
            assert any(keyword in filter_str for keyword in ["約", "程度", "およそ"])

    @pytest.mark.asyncio
    async def test_classify_hybrid_aggregation_semantic(self):
        """集約条件とセマンティック条件の複合テスト"""
        queries = [
            "最大ダメージで人気のカード",
            "一番高いHPで強いカード",
            "トップクラスのおすすめカード"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            # ハイブリッドまたはフィルター可能として分類される可能性
            assert result.query_type in [QueryType.HYBRID, QueryType.FILTERABLE, QueryType.SEMANTIC]
            # 集約キーワードがある場合はfilter_keywordsに含まれる
            if result.query_type == QueryType.HYBRID:
                assert len(result.filter_keywords) > 0
                assert len(result.search_keywords) > 0

    @pytest.mark.asyncio
    async def test_classify_greeting_unchanged(self):
        """挨拶クエリが正しく分類されることの確認"""
        greetings = [
            "こんにちは",
            "おはよう",
            "ありがとう",
            "よろしく"
        ]
        
        for greeting in greetings:
            request = ClassificationRequest(query=greeting)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.GREETING
            assert result.filter_keywords == []
            assert result.search_keywords == []

    @pytest.mark.asyncio
    async def test_classify_complex_conditions_with_class(self):
        """クラス指定と複雑条件の組み合わせテスト"""
        queries = [
            "エルフの一番高いHPカード",
            "ドラゴンタイプで約100のダメージ",
            "ウィッチクラスの上位3位のコスト"
        ]
        
        for query in queries:
            request = ClassificationRequest(query=query)
            result = await self.service.classify_query(request)
            
            assert result.query_type == QueryType.FILTERABLE
            filter_str = str(result.filter_keywords)
            # クラス名が含まれることを確認
            assert any(cls in filter_str for cls in ["エルフ", "ドラゴン", "ウィッチ"])
