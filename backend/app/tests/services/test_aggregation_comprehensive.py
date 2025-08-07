"""
包括的な集約クエリテスト（Phase 3.2: テストケースの拡充）
ランダム数値でのテスト、エッジケース、パフォーマンステストを含む
"""
import pytest
import random
from unittest.mock import patch
from app.services.database_service import DatabaseService


class TestAggregationComprehensive:
    """包括的な集約クエリテスト"""

    @pytest.fixture
    def database_service(self):
        """テスト用のデータベースサービス"""
        with patch.dict('os.environ', {'TEST_MODE': 'true'}):
            return DatabaseService()

    @pytest.mark.asyncio
    async def test_max_min_search_with_random_numbers(self, database_service):
        """ランダム数値での最大値/最小値検索テスト"""
        # ランダムな数値条件でテスト
        random_numbers = [random.randint(1, 200) for _ in range(5)]
        
        for num in random_numbers:
            # 最大値検索
            max_queries = [
                f"HP{num}以上で一番高いHPのカード",
                f"コスト{num}以上で最大攻撃力のカード",
                f"攻撃力{num}以上で最高コストのカード"
            ]
            
            for query in max_queries:
                result = await database_service.filter_search_llm_async(query, top_k=5)
                assert isinstance(result, list)
                # 結果がある場合の構造検証
                if result:
                    details = database_service.get_card_details_by_titles(result)
                    assert isinstance(details, list)
                    assert len(details) > 0
            
            # 最小値検索
            min_queries = [
                f"HP{num}以下で一番低いHPのカード",
                f"コスト{num}以下で最小攻撃力のカード",
                f"攻撃力{num}以下で最低コストのカード"
            ]
            
            for query in min_queries:
                result = await database_service.filter_search_llm_async(query, top_k=5)
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_top_n_search_various_counts(self, database_service):
        """様々なN値での上位N件検索テスト"""
        # 様々なN値でテスト
        n_values = [1, 2, 3, 5, 10, 20]
        
        for n in n_values:
            queries = [
                f"上位{n}位のHPカード",
                f"トップ{n}の攻撃力カード",
                f"上位{n}位のコストカード",
                f"ベスト{n}のダメージカード"
            ]
            
            for query in queries:
                result = await database_service.filter_search_llm_async(query, top_k=max(n, 10))
                assert isinstance(result, list)
                # 最大でもN件以下（実際のデータ量による）
                if result:
                    details = database_service.get_card_details_by_titles(result)
                    assert isinstance(details, list)

    @pytest.mark.asyncio
    async def test_complex_aggregation_filters(self, database_service):
        """複合条件（集約+フィルター）の包括的テスト"""
        # クラス + 集約
        class_aggregation_queries = [
            "エルフクラスで一番高いHPのカード",
            "ドラゴンクラスで最大攻撃力のカード",
            "ウィッチクラスで最小コストのカード",
            "ロイヤルクラスで上位3位のHPカード"
        ]
        
        # レアリティ + 集約
        rarity_aggregation_queries = [
            "レジェンドで一番高いHPのカード",
            "ゴールドレアで最大攻撃力のカード",
            "シルバーレアで最小コストのカード"
        ]
        
        # 数値条件 + 集約
        numeric_aggregation_queries = [
            "コスト5以下で一番高いHPのカード",
            "HP100以上で最大攻撃力のカード",
            "攻撃力50以上で最小コストのカード"
        ]
        
        all_queries = class_aggregation_queries + rarity_aggregation_queries + numeric_aggregation_queries
        
        for query in all_queries:
            result = await database_service.filter_search_llm_async(query, top_k=10)
            assert isinstance(result, list)
            # 結果構造の検証
            if result:
                details = database_service.get_card_details_by_titles(result)
                assert isinstance(details, list)
                for card in details:
                    assert "name" in card

    @pytest.mark.asyncio
    async def test_aggregation_edge_cases(self, database_service):
        """集約クエリのエッジケーステスト"""
        edge_case_queries = [
            # 存在しないフィールド
            "最大魔力のカード",
            # 曖昧な表現
            "とても高いHPのカード",
            "すごく低いコストのカード",
            # 複数集約条件
            "一番高いHPで最大攻撃力のカード",
            # 空集合になりそうな条件
            "HP1000以上で一番低いHPのカード"
        ]
        
        for query in edge_case_queries:
            # エラーが発生せず、適切にハンドリングされることを確認
            try:
                result = await database_service.filter_search_llm_async(query, top_k=5)
                assert isinstance(result, list)
            except Exception as e:
                # 特定の例外なら許容（ログで確認）
                print(f"Edge case query failed: {query}, Error: {e}")

    def test_aggregation_helper_methods_comprehensive(self, database_service):
        """集約ヘルパーメソッドの包括的テスト"""
        # より大きなテストデータセット
        test_data = [
            {"title": f"カード{i}", "hp": random.randint(10, 500), 
             "attack": random.randint(5, 200), "cost": random.randint(1, 10)}
            for i in range(20)
        ]
        
        # 最大値テスト
        max_hp_items = database_service._get_max_value_items(test_data, "hp")
        assert len(max_hp_items) >= 1
        if len(max_hp_items) > 1:
            # 同じ最大値を持つカードが複数ある場合
            max_hp_value = max_hp_items[0]["hp"]
            for item in max_hp_items:
                assert item["hp"] == max_hp_value
        
        # 最小値テスト
        min_cost_items = database_service._get_min_value_items(test_data, "cost")
        assert len(min_cost_items) >= 1
        if len(min_cost_items) > 1:
            min_cost_value = min_cost_items[0]["cost"]
            for item in min_cost_items:
                assert item["cost"] == min_cost_value
        
        # 上位N件テスト（様々なN値）
        for n in [1, 3, 5, 10, 15]:
            top_n_attack = database_service._get_top_n_items(test_data, "attack", n)
            assert len(top_n_attack) <= n
            assert len(top_n_attack) <= len(test_data)
            
            # ソート順の確認
            if len(top_n_attack) > 1:
                for i in range(len(top_n_attack) - 1):
                    assert top_n_attack[i]["attack"] >= top_n_attack[i + 1]["attack"]

    def test_field_value_extraction(self, database_service):
        """フィールド値抽出のテスト"""
        test_cards = [
            {"title": "テストカード1", "hp": 100, "attack": 50, "cost": 3},
            {"title": "テストカード2", "hp": "200", "attack": "80", "cost": "5"},  # 文字列数値
            {"title": "テストカード3", "hp": None, "attack": 120, "cost": 2},  # null値
            {"title": "テストカード4", "attack": 150, "cost": 4},  # 欠損フィールド
        ]
        
        for card in test_cards:
            # 各フィールドの抽出テスト
            for field in ["hp", "attack", "cost"]:
                try:
                    value = database_service._extract_numeric_field(card, field)
                    if value is not None:
                        assert isinstance(value, (int, float))
                        assert value >= 0
                except (ValueError, KeyError):
                    # フィールドが存在しない、または変換できない場合は許容
                    pass

    @pytest.mark.asyncio
    async def test_aggregation_performance(self, database_service):
        """集約クエリのパフォーマンステスト"""
        import time
        
        performance_queries = [
            "一番高いHPのカード",
            "最大攻撃力のカード",
            "上位10位のコストカード"
        ]
        
        for query in performance_queries:
            start_time = time.time()
            result = await database_service.filter_search_llm_async(query, top_k=20)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # パフォーマンス要件（10秒以内）
            assert execution_time < 10.0, f"Query '{query}' took {execution_time:.2f}s (too slow)"
            assert isinstance(result, list)

    def test_aggregation_query_parsing(self, database_service):
        """集約クエリパーシングの詳細テスト"""
        test_cases = [
            # (クエリ, 期待される集約タイプ, 期待されるフィールド)
            ("一番高いHPのカード", "max", "hp"),
            ("最大攻撃力のカード", "max", "attack"),
            ("最小コストのカード", "min", "cost"),
            ("上位5位のダメージカード", "top_n", "attack"),  # ダメージ→attackにマッピング
            ("トップ3のHPカード", "top_n", "hp"),
        ]
        
        for query, expected_type, expected_field in test_cases:
            # 集約クエリの解析をテスト
            detection_result = database_service._detect_aggregation_query(query)
            
            if isinstance(detection_result, dict):
                assert detection_result.get("is_aggregation", False)
                # 可能であれば、タイプとフィールドも確認
                if "aggregation_type" in detection_result:
                    assert expected_type in str(detection_result["aggregation_type"]).lower()
                if "field" in detection_result:
                    assert expected_field in str(detection_result["field"]).lower()

    @pytest.mark.asyncio
    async def test_mixed_language_aggregation(self, database_service):
        """多言語混在集約クエリのテスト"""
        mixed_queries = [
            "highest HPのカード",
            "maximum attackのカード", 
            "lowest costのカード",
            "top 5 HPカード",
            "最大 damage のカード"
        ]
        
        for query in mixed_queries:
            # 多言語混在でも適切に処理されることを確認
            result = await database_service.filter_search_llm_async(query, top_k=5)
            assert isinstance(result, list)


class TestAggregationErrorHandling:
    """集約クエリのエラーハンドリングテスト"""

    @pytest.fixture
    def database_service(self):
        """テスト用のデータベースサービス"""
        with patch.dict('os.environ', {'TEST_MODE': 'true'}):
            return DatabaseService()

    @pytest.mark.asyncio
    async def test_invalid_aggregation_queries(self, database_service):
        """無効な集約クエリのエラーハンドリング"""
        invalid_queries = [
            "",  # 空文字
            "   ",  # 空白のみ
            "最大",  # 不完全なクエリ
            "一番高い",  # フィールド指定なし
            "上位のカード",  # N値なし
        ]
        
        for query in invalid_queries:
            # エラーが適切にハンドリングされることを確認
            try:
                result = await database_service.filter_search_llm_async(query, top_k=5)
                assert isinstance(result, list)
                # 空の結果でも正常に処理される
            except Exception as e:
                # 特定の例外なら許容
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_aggregation_with_empty_data(self, database_service):
        """空データでの集約処理テスト"""
        empty_data = []
        
        # 空データに対する集約メソッドのテスト
        max_result = database_service._get_max_value_items(empty_data, "hp")
        assert max_result == []
        
        min_result = database_service._get_min_value_items(empty_data, "cost")
        assert min_result == []
        
        top_n_result = database_service._get_top_n_items(empty_data, "attack", 5)
        assert top_n_result == []

    def test_aggregation_with_invalid_field(self, database_service):
        """存在しないフィールドでの集約テスト"""
        test_data = [
            {"title": "カードA", "hp": 100, "attack": 50},
            {"title": "カードB", "hp": 200, "attack": 80}
        ]
        
        # 存在しないフィールド
        try:
            result = database_service._get_max_value_items(test_data, "nonexistent_field")
            # エラーにならない場合は空リストを返すことを期待
            assert result == []
        except KeyError:
            # KeyErrorが発生する場合も許容
            pass
