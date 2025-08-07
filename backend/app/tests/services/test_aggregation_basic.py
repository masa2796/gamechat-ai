"""
集約クエリの基本テスト（Phase 3.2: テストケースの拡充）
最大値・最小値・上位N件検索のテスト
"""
import pytest
from unittest.mock import patch
from app.services.database_service import DatabaseService


class TestAggregationQueries:
    """集約クエリ機能の基本テスト"""

    @pytest.fixture
    def database_service(self):
        """テスト用のデータベースサービス"""
        with patch.dict('os.environ', {'TEST_MODE': 'true'}):
            return DatabaseService()

    @pytest.mark.asyncio
    async def test_max_value_aggregation_queries(self, database_service):
        """最大値集約クエリのテスト"""
        queries = [
            "一番高いHPのカード",
            "最大攻撃力のカード", 
            "最高コストのカード"
        ]
        
        for query in queries:
            # 集約クエリが正常に実行されることを確認
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) >= 0  # 結果が0件でもエラーにならないことを確認
            
            # カード詳細を取得して構造を確認
            if result_titles:
                result_details = database_service.get_card_details_by_titles(result_titles)
                assert isinstance(result_details, list)
                for card in result_details:
                    assert isinstance(card, dict)
                    assert "name" in card  # 実際のフィールド名は"name"

    @pytest.mark.asyncio
    async def test_min_value_aggregation_queries(self, database_service):
        """最小値集約クエリのテスト"""
        queries = [
            "一番低いHPのカード",
            "最小コストのカード",
            "最低攻撃力のカード"
        ]
        
        for query in queries:
            # 集約クエリが正常に実行されることを確認
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) >= 0
            
            # カード詳細を取得して構造を確認
            if result_titles:
                result_details = database_service.get_card_details_by_titles(result_titles)
                assert isinstance(result_details, list)
                for card in result_details:
                    assert isinstance(card, dict)
                    assert "name" in card  # 実際のフィールド名は"name"

    @pytest.mark.asyncio
    async def test_top_n_aggregation_queries(self, database_service):
        """上位N件集約クエリのテスト"""
        queries = [
            "上位3位のHPカード",
            "トップ5の攻撃力カード",
            "上位2位のコストカード"
        ]
        
        for query in queries:
            # 集約クエリが正常に実行されることを確認
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) >= 0
            
            # カード詳細を取得して構造を確認
            if result_titles:
                result_details = database_service.get_card_details_by_titles(result_titles)
                assert isinstance(result_details, list)

    @pytest.mark.asyncio
    async def test_complex_aggregation_with_filters(self, database_service):
        """複合条件（集約+フィルター）のテスト"""
        queries = [
            "ドラゴンクラスで一番高いHPのカード",
            "レジェンドで最大攻撃力のカード",
            "エルフクラスで最小コストのカード"
        ]
        
        for query in queries:
            # 複合条件集約クエリが正常に実行されることを確認
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) >= 0
            
            # カード詳細を取得して構造を確認
            if result_titles:
                result_details = database_service.get_card_details_by_titles(result_titles)
                assert isinstance(result_details, list)

    def test_aggregation_helper_methods(self, database_service):
        """集約ヘルパーメソッドの直接テスト"""
        test_data = [
            {"title": "カードA", "hp": 100, "attack": 50, "cost": 3},
            {"title": "カードB", "hp": 200, "attack": 80, "cost": 5},
            {"title": "カードC", "hp": 150, "attack": 120, "cost": 2}
        ]
        
        # 最大値テスト
        max_hp_items = database_service._get_max_value_items(test_data, "hp")
        assert len(max_hp_items) == 1
        assert max_hp_items[0]["title"] == "カードB"
        assert max_hp_items[0]["hp"] == 200
        
        # 最小値テスト
        min_cost_items = database_service._get_min_value_items(test_data, "cost")
        assert len(min_cost_items) == 1
        assert min_cost_items[0]["title"] == "カードC"
        assert min_cost_items[0]["cost"] == 2
        
        # 上位N件テスト
        top_2_attack = database_service._get_top_n_items(test_data, "attack", 2)
        assert len(top_2_attack) == 2
        assert top_2_attack[0]["title"] == "カードC"  # 攻撃力 120
        assert top_2_attack[1]["title"] == "カードB"  # 攻撃力 80

    def test_aggregation_query_detection(self, database_service):
        """集約クエリ検出機能のテスト"""
        # 集約クエリ検出テスト
        test_queries = [
            ("一番高いHPのカード", True),
            ("最大ダメージのカード", True),
            ("上位5位のコストカード", True),
            ("普通のHPカード", False),
            ("HPが100のカード", False)
        ]
        
        for query, should_detect in test_queries:
            detection_result = database_service._detect_aggregation_query(query)
            
            # _detect_aggregation_queryが辞書を返す場合
            if isinstance(detection_result, dict):
                is_aggregation = detection_result.get("is_aggregation", False)
            else:
                is_aggregation = detection_result
                
            assert is_aggregation == should_detect, f"Query: {query}, Expected: {should_detect}, Got: {is_aggregation}"

    def test_aggregation_edge_cases(self, database_service):
        """集約処理のエッジケースのテスト"""
        # 空データ
        empty_result = database_service._get_max_value_items([], "hp")
        assert empty_result == []
        
        # 無効なフィールド
        test_data = [{"title": "テスト", "hp": "無効"}]
        invalid_result = database_service._get_max_value_items(test_data, "hp")
        assert invalid_result == []
        
        # 同じ値を持つ複数アイテム
        same_value_data = [
            {"title": "カード1", "hp": 100},
            {"title": "カード2", "hp": 100},
            {"title": "カード3", "hp": 100}
        ]
        max_same = database_service._get_max_value_items(same_value_data, "hp")
        assert len(max_same) == 3  # 全て同じ最大値
        
        # 上位N件で無効なcount
        test_data = [{"title": "テスト", "hp": 100}]
        result = database_service._get_top_n_items(test_data, "hp", 0)
        assert result == []
        
        result = database_service._get_top_n_items(test_data, "hp", -1)
        assert result == []

    @pytest.mark.asyncio
    async def test_aggregation_performance(self, database_service):
        """集約クエリのパフォーマンステスト"""
        # パフォーマンステストはシンプルに実行時間のみ測定
        import time
        
        start_time = time.time()
        result = await database_service.filter_search_llm_async("一番高いHPのカード", top_k=5)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 合理的な実行時間（5秒以内）であることを確認
        assert execution_time < 5.0, f"集約クエリの実行時間が長すぎます: {execution_time}秒"
        
        # 結果が正常に返されることを確認
        assert isinstance(result, list)


class TestAggregationErrorHandling:
    """集約クエリのエラーハンドリングテスト"""

    @pytest.fixture
    def database_service(self):
        """エラーテスト用のデータベースサービス"""
        with patch.dict('os.environ', {'TEST_MODE': 'true'}):
            return DatabaseService()

    @pytest.mark.asyncio
    async def test_aggregation_with_malformed_queries(self, database_service):
        """不正なクエリでのエラーハンドリングテスト"""
        malformed_queries = [
            "",  # 空文字
            "   ",  # 空白のみ
            "最大",  # 不完全なクエリ
            "上位のカード",  # N件数が不明
        ]
        
        for query in malformed_queries:
            # 不正なクエリでもエラーにならずに適切に処理されることを確認
            try:
                result = await database_service.filter_search_llm_async(query, top_k=5)
                assert isinstance(result, list)
                # 空の結果や通常の検索結果が返されることを確認
            except Exception as e:
                # 予期しないエラーが発生した場合は失敗
                pytest.fail(f"Unexpected error for query '{query}': {e}")

    def test_aggregation_method_error_handling(self, database_service):
        """集約メソッドの直接エラーハンドリングテスト"""
        # None入力
        result = database_service._get_max_value_items(None, "hp")
        assert result == []
        
        # 存在しないフィールド
        test_data = [{"title": "テスト", "hp": 100}]
        result = database_service._get_max_value_items(test_data, "nonexistent_field")
        assert result == []
        
        # 型エラーが発生する可能性のあるデータ
        mixed_data = [
            {"title": "数値", "hp": 100},
            {"title": "文字列", "hp": "高い"},
            {"title": "None", "hp": None},
            {"title": "欠損", "other_field": "値"}
        ]
        
        # エラーが発生せずに有効なデータのみが処理されることを確認
        result = database_service._get_max_value_items(mixed_data, "hp")
        assert len(result) == 1
        assert result[0]["title"] == "数値"
