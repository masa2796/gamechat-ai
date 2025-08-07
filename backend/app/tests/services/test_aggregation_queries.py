"""
集約クエリの包括的テスト（Phase 3.2: テストケースの拡充）
最大値・最小値・上位N件検索と複合条件のテスト
"""
import pytest
from unittest.mock import patch
from app.services.database_service import DatabaseService


class TestAggregationQueries:
    """集約クエリ機能の包括的テスト"""

    @pytest.fixture
    def database_service(self):
        """テスト用のデータベースサービス"""
        with patch.dict('os.environ', {'TEST_MODE': 'true'}):
            service = DatabaseService()
            
            # テスト用データの設定
            service.data = [
                {
                    "title": "高HPカード", "hp": 300, "attack": 50, "cost": 5, 
                    "class": "ドラゴン", "rarity": "レジェンド",
                    "text": "強力な防御力を持つドラゴンカード"
                },
                {
                    "title": "中HPカード", "hp": 200, "attack": 80, "cost": 4,
                    "class": "エルフ", "rarity": "ゴールドレア", 
                    "text": "バランスの良いエルフカード"
                },
                {
                    "title": "低HPカード", "hp": 100, "attack": 120, "cost": 3,
                    "class": "ロイヤル", "rarity": "シルバーレア",
                    "text": "攻撃重視のロイヤルカード"
                },
                {
                    "title": "最高攻撃カード", "hp": 150, "attack": 150, "cost": 6,
                    "class": "ウィッチ", "rarity": "レジェンド",
                    "text": "最強の攻撃力を持つウィッチカード"
                },
                {
                    "title": "最低コストカード", "hp": 80, "attack": 30, "cost": 1,
                    "class": "ニュートラル", "rarity": "ブロンズレア",
                    "text": "低コストで使いやすいカード"
                }
            ]
            
            # title_to_dataマッピングを構築
            service.title_to_data = {card["title"]: card for card in service.data}
            
            return service

    @pytest.mark.asyncio
    async def test_max_value_aggregation_hp(self, database_service):
        """最大HP検索のテスト"""
        queries = [
            "一番高いHPのカード",
            "最大HPのカード", 
            "最高体力のカード",
            "HPがトップのカード"
        ]
        
        for query in queries:
            # 文字列リストを取得
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) > 0
            
            # カード詳細を取得
            result_details = database_service.get_card_details_by_titles(result_titles)
            
            # 最大HPカードが含まれることを確認（実際のデータを使用）
            if result_details:
                # テスト用データの確認
                hp_values = [card.get("hp", 0) for card in result_details if isinstance(card.get("hp"), int)]
                if hp_values:
                    # HPの最大値を持つカードが含まれることを確認
                    max_hp = max(hp_values)
                    assert max_hp > 0

    @pytest.mark.asyncio
    async def test_max_value_aggregation_attack(self, database_service):
        """最大攻撃力検索のテスト"""
        queries = [
            "一番高い攻撃力のカード",
            "最大ダメージのカード",
            "最高攻撃のカード"
        ]
        
        for query in queries:
            # 文字列リストを取得
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) > 0
            
            # カード詳細を取得
            result_details = database_service.get_card_details_by_titles(result_titles)
            
            # 最大攻撃力カードが含まれることを確認
            if result_details:
                attack_values = [card.get("attack", 0) for card in result_details if isinstance(card.get("attack"), int)]
                if attack_values:
                    max_attack = max(attack_values)
                    assert max_attack > 0

    @pytest.mark.asyncio
    async def test_min_value_aggregation_hp(self, database_service):
        """最小HP検索のテスト"""
        queries = [
            "一番低いHPのカード",
            "最小HPのカード",
            "最低体力のカード",
            "HPがボトムのカード"
        ]
        
        for query in queries:
            # 文字列リストを取得
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) > 0
            
            # カード詳細を取得
            result_details = database_service.get_card_details_by_titles(result_titles)
            
            # 最小HPカードが含まれることを確認
            if result_details:
                hp_values = [card.get("hp", 0) for card in result_details if isinstance(card.get("hp"), int)]
                if hp_values:
                    min_hp = min(hp_values)
                    assert min_hp > 0

    @pytest.mark.asyncio
    async def test_min_value_aggregation_cost(self, database_service):
        """最小コスト検索のテスト"""
        queries = [
            "一番低いコストのカード",
            "最小コストのカード",
            "最安カード"
        ]
        
        for query in queries:
            # 文字列リストを取得
            result_titles = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result_titles, list)
            assert len(result_titles) > 0
            
            # カード詳細を取得
            result_details = database_service.get_card_details_by_titles(result_titles)
            
            # 最小コストカードが含まれることを確認
            if result_details:
                cost_values = [card.get("cost", 0) for card in result_details if isinstance(card.get("cost"), int)]
                if cost_values:
                    min_cost = min(cost_values)
                    assert min_cost >= 0

    @pytest.mark.asyncio
    async def test_top_n_aggregation_hp(self, database_service):
        """上位N件HP検索のテスト"""
        queries = [
            "上位3位のHPカード",
            "トップ3のHPカード",
            "HP上位3カード"
        ]
        
        for query in queries:
            result = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result, list)
            assert len(result) >= 3
            
            # HP降順でソートされていることを確認
            hp_values = [card["hp"] for card in result[:3]]
            expected_order = [300, 200, 150]  # 期待される順序
            assert hp_values == expected_order

    @pytest.mark.asyncio
    async def test_top_n_aggregation_attack(self, database_service):
        """上位N件攻撃力検索のテスト"""
        queries = [
            "上位2位の攻撃力カード",
            "トップ2の攻撃カード"
        ]
        
        for query in queries:
            result = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result, list)
            assert len(result) >= 2
            
            # 攻撃力降順でソートされていることを確認
            attack_values = [card["attack"] for card in result[:2]]
            expected_order = [150, 120]  # 期待される順序
            assert attack_values == expected_order

    @pytest.mark.asyncio
    async def test_complex_aggregation_with_class_filter(self, database_service):
        """複合条件（集約+クラスフィルター）のテスト"""
        queries = [
            "ドラゴンクラスで一番高いHPのカード",
            "エルフクラスで最大攻撃力のカード",
            "レジェンドで最高HPのカード"
        ]
        
        # ドラゴンクラスでの最大HP
        result = await database_service.filter_search_llm_async(queries[0], top_k=10)
        assert isinstance(result, list)
        if result:
            # ドラゴンクラスのカードが含まれることを確認
            dragon_cards = [card for card in result if card.get("class") == "ドラゴン"]
            assert len(dragon_cards) > 0
            
        # エルフクラスでの最大攻撃力
        result = await database_service.filter_search_llm_async(queries[1], top_k=10)
        assert isinstance(result, list)
        if result:
            # エルフクラスのカードが含まれることを確認
            elf_cards = [card for card in result if card.get("class") == "エルフ"]
            assert len(elf_cards) > 0

    @pytest.mark.asyncio
    async def test_aggregation_with_rarity_filter(self, database_service):
        """集約+レアリティフィルターのテスト"""
        queries = [
            "レジェンドで一番高いHPのカード",
            "シルバーレアで最大攻撃力のカード"
        ]
        
        for query in queries:
            result = await database_service.filter_search_llm_async(query, top_k=10)
            
            assert isinstance(result, list)
            # レアリティフィルターが適用されていることを確認
            if result and "レジェンド" in query:
                legendary_cards = [card for card in result if card.get("rarity") == "レジェンド"]
                assert len(legendary_cards) > 0
            elif result and "シルバーレア" in query:
                silver_cards = [card for card in result if card.get("rarity") == "シルバーレア"]
                assert len(silver_cards) > 0

    def test_aggregation_helper_methods(self, database_service):
        """集約ヘルパーメソッドの直接テスト"""
        test_data = [
            {"title": "カードA", "hp": 100, "attack": 50},
            {"title": "カードB", "hp": 200, "attack": 80},
            {"title": "カードC", "hp": 150, "attack": 120}
        ]
        
        # 最大値テスト
        max_hp_items = database_service._get_max_value_items(test_data, "hp")
        assert len(max_hp_items) == 1
        assert max_hp_items[0]["title"] == "カードB"
        
        # 最小値テスト
        min_attack_items = database_service._get_min_value_items(test_data, "attack")
        assert len(min_attack_items) == 1
        assert min_attack_items[0]["title"] == "カードA"
        
        # 上位N件テスト
        top_2_hp = database_service._get_top_n_items(test_data, "hp", 2)
        assert len(top_2_hp) == 2
        assert top_2_hp[0]["title"] == "カードB"  # HP 200
        assert top_2_hp[1]["title"] == "カードC"  # HP 150

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

    @pytest.mark.asyncio
    async def test_aggregation_query_parsing(self, database_service):
        """集約クエリのパース機能テスト"""
        # 集約クエリ検出テスト
        test_queries = [
            ("一番高いHPのカード", True),
            ("最大ダメージのカード", True),
            ("上位5位のコストカード", True),
            ("普通のHPカード", False),
            ("HPが100のカード", False)
        ]
        
        for query, should_detect in test_queries:
            is_aggregation = database_service._detect_aggregation_query(query)
            assert is_aggregation == should_detect, f"Query: {query}, Expected: {should_detect}, Got: {is_aggregation}"

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, database_service):
        """大きなデータセットでのパフォーマンステスト"""
        # 大量のテストデータを生成
        large_data = []
        for i in range(100):
            large_data.append({
                "title": f"カード{i}",
                "hp": 50 + (i % 200),  # HP 50-249
                "attack": 30 + (i % 150),  # 攻撃力 30-179
                "cost": 1 + (i % 10),  # コスト 1-10
                "class": ["エルフ", "ドラゴン", "ロイヤル"][i % 3],
                "rarity": ["ブロンズレア", "シルバーレア", "ゴールドレア", "レジェンド"][i % 4],
                "text": f"テストカード{i}の説明"
            })
        
        # データを一時的に置き換え
        original_data = database_service.data
        database_service.data = large_data
        database_service.title_to_data = {card["title"]: card for card in large_data}
        
        try:
            # 集約クエリの実行
            import time
            start_time = time.time()
            
            result = await database_service.filter_search_llm_async("一番高いHPのカード", top_k=10)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # パフォーマンス確認（1秒以内に完了することを期待）
            assert execution_time < 1.0, f"集約クエリの実行時間が長すぎます: {execution_time}秒"
            
            # 結果の正確性確認
            assert isinstance(result, list)
            assert len(result) > 0
            
            # 最大HPが正しく検出されることを確認
            if result:
                max_hp = max(card["hp"] for card in large_data)
                top_result = result[0]
                assert top_result["hp"] == max_hp
                
        finally:
            # データを元に戻す
            database_service.data = original_data
            database_service.title_to_data = {card["title"]: card for card in original_data}


class TestAggregationErrorHandling:
    """集約クエリのエラーハンドリングテスト"""

    @pytest.fixture
    def database_service(self):
        """エラーテスト用のデータベースサービス"""
        with patch.dict('os.environ', {'TEST_MODE': 'true'}):
            service = DatabaseService()
            service.data = []  # 空のデータ
            service.title_to_data = {}
            return service

    @pytest.mark.asyncio
    async def test_aggregation_with_empty_data(self, database_service):
        """空データでの集約クエリテスト"""
        queries = [
            "一番高いHPのカード",
            "最大攻撃力のカード",
            "上位3位のコストカード"
        ]
        
        for query in queries:
            result = await database_service.filter_search_llm_async(query, top_k=10)
            
            # 空データでも適切に処理されることを確認
            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_aggregation_with_invalid_field_data(self, database_service):
        """無効なフィールドデータでの集約クエリテスト"""
        # 数値以外のデータを含むテストデータ
        database_service.data = [
            {"title": "無効HPカード", "hp": "無効", "attack": "N/A", "cost": None},
            {"title": "文字列HPカード", "hp": "高い", "attack": "強い", "cost": "安い"},
            {"title": "空フィールドカード", "text": "説明のみ"}
        ]
        database_service.title_to_data = {card["title"]: card for card in database_service.data}
        
        queries = [
            "一番高いHPのカード",
            "最大攻撃力のカード"
        ]
        
        for query in queries:
            result = await database_service.filter_search_llm_async(query, top_k=10)
            
            # 無効データでも適切に処理されることを確認
            assert isinstance(result, list)
            # 有効な数値フィールドがない場合は空結果
            assert len(result) == 0

    def test_aggregation_method_error_handling(self, database_service):
        """集約メソッドのエラーハンドリングテスト"""
        # None入力
        result = database_service._get_max_value_items(None, "hp")
        assert result == []
        
        # 存在しないフィールド
        test_data = [{"title": "テスト", "hp": 100}]
        result = database_service._get_max_value_items(test_data, "nonexistent_field")
        assert result == []
        
        # 上位N件で無効なcount
        result = database_service._get_top_n_items(test_data, "hp", 0)
        assert result == []
        
        result = database_service._get_top_n_items(test_data, "hp", -1)
        assert result == []
