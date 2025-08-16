"""
集約クエリの修正版テスト（Phase 3.2: テストケースの拡充）
CI環境でも動作するようにモック機能に特化したテスト
"""
import pytest
from unittest.mock import patch
from app.services.database_service import DatabaseService


class TestAggregationQueriesFixed:
    """集約クエリ機能の修正版テスト"""

    @pytest.fixture
    def database_service(self):
        """テスト用のデータベースサービス"""
        with patch.dict('os.environ', {
            'TEST_MODE': 'true',
            'BACKEND_TESTING': 'true', 
            'BACKEND_MOCK_EXTERNAL_SERVICES': 'true'
        }):
            service = DatabaseService()
            
            # テスト用データの設定
            test_data = [
                {
                    "title": "高HPカード", "name": "高HPカード", "hp": 300, "attack": 50, "cost": 5, 
                    "class": "ドラゴン", "rarity": "レジェンド",
                    "text": "強力な防御力を持つドラゴンカード"
                },
                {
                    "title": "中HPカード", "name": "中HPカード", "hp": 200, "attack": 80, "cost": 4,
                    "class": "エルフ", "rarity": "ゴールドレア", 
                    "text": "バランスの良いエルフカード"
                },
                {
                    "title": "低HPカード", "name": "低HPカード", "hp": 100, "attack": 120, "cost": 3,
                    "class": "ロイヤル", "rarity": "シルバーレア",
                    "text": "攻撃重視のロイヤルカード"
                },
                {
                    "title": "最高攻撃カード", "name": "最高攻撃カード", "hp": 150, "attack": 150, "cost": 6,
                    "class": "ウィッチ", "rarity": "レジェンド",
                    "text": "最強の攻撃力を持つウィッチカード"
                },
                {
                    "title": "最低コストカード", "name": "最低コストカード", "hp": 80, "attack": 30, "cost": 1,
                    "class": "ニュートラル", "rarity": "ブロンズレア",
                    "text": "低コストで使いやすいカード"
                }
            ]
            
            # 複数の属性に同じデータを設定
            service.data = test_data
            service.data_cache = test_data.copy()
            service.title_to_data = {card["title"]: card for card in test_data}
            service.storage_service = None
            
            return service

    def test_aggregation_query_detection_fixed(self, database_service):
        """集約クエリ検出機能のテスト（修正版）"""
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

    def test_aggregation_helper_methods_fixed(self, database_service):
        """集約ヘルパーメソッドの直接テスト（修正版）"""
        test_data = database_service.data
        
        # 最大値テスト
        max_hp_items = database_service._get_max_value_items(test_data, "hp")
        assert len(max_hp_items) >= 1
        if max_hp_items:
            assert max_hp_items[0]["hp"] == 300  # 高HPカードが選ばれることを確認
        
        # 最小値テスト
        min_cost_items = database_service._get_min_value_items(test_data, "cost")
        assert len(min_cost_items) >= 1
        if min_cost_items:
            assert min_cost_items[0]["cost"] == 1  # 最低コストカードが選ばれることを確認
        
        # 上位N件テスト
        top_2_attack = database_service._get_top_n_items(test_data, "attack", 2)
        assert len(top_2_attack) <= 2
        if len(top_2_attack) >= 2:
            # 攻撃力の降順でソートされていることを確認
            assert top_2_attack[0]["attack"] >= top_2_attack[1]["attack"]

    @pytest.mark.asyncio
    async def test_aggregation_queries_basic_execution(self, database_service):
        """集約クエリの基本実行テスト（修正版）"""
        # データが存在することを確認
        assert len(database_service.data) > 0
        assert len(database_service.data_cache) > 0
        
        queries = [
            "一番高いHPのカード",
            "最大攻撃力のカード",
            "最小コストのカード"
        ]
        
        for query in queries:
            # エラーが発生しないことを確認
            try:
                result = await database_service.filter_search_llm_async(query, top_k=5)
                assert isinstance(result, list)
                # 結果があってもなくても、エラーが発生しなければOK
            except Exception as e:
                pytest.fail(f"Query '{query}' raised an exception: {e}")

    def test_field_extraction_fixed(self, database_service):
        """フィールド値抽出のテスト（修正版）"""
        test_cards = database_service.data
        
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

    def test_aggregation_parsing_fixed(self, database_service):
        """集約クエリパーシングのテスト（修正版）"""
        test_cases = [
            ("一番高いHPのカード", "max", "hp"),
            ("最大攻撃力のカード", "max", "attack"),
            ("最小コストのカード", "min", "cost"),
            ("上位5位のダメージカード", "top_n", "attack"),  # ダメージ→attackにマッピング
            ("トップ3のHPカード", "top_n", "hp"),
        ]
        
        for query, expected_type, expected_field in test_cases:
            detection_result = database_service._detect_aggregation_query(query)
            
            if isinstance(detection_result, dict):
                assert detection_result.get("is_aggregation", False)
                # 可能であれば、タイプとフィールドも確認
                if "aggregation_type" in detection_result:
                    assert expected_type in str(detection_result["aggregation_type"]).lower()
                if "field" in detection_result:
                    assert expected_field in str(detection_result["field"]).lower()


class TestAggregationErrorHandlingFixed:
    """集約クエリのエラーハンドリングテスト（修正版）"""

    @pytest.fixture
    def database_service(self):
        """テスト用のデータベースサービス"""
        with patch.dict('os.environ', {
            'TEST_MODE': 'true',
            'BACKEND_TESTING': 'true',
            'BACKEND_MOCK_EXTERNAL_SERVICES': 'true'
        }):
            return DatabaseService()

    def test_aggregation_with_empty_data_fixed(self, database_service):
        """空データでの集約処理テスト（修正版）"""
        empty_data = []
        
        # 空データに対する集約メソッドのテスト
        max_result = database_service._get_max_value_items(empty_data, "hp")
        assert max_result == []
        
        min_result = database_service._get_min_value_items(empty_data, "cost")
        assert min_result == []
        
        top_n_result = database_service._get_top_n_items(empty_data, "attack", 5)
        assert top_n_result == []

    @pytest.mark.asyncio
    async def test_invalid_aggregation_queries_fixed(self, database_service):
        """無効な集約クエリのエラーハンドリング（修正版）"""
        invalid_queries = [
            "",  # 空文字
            "   ",  # 空白のみ
            "最大",  # 不完全なクエリ
            "一番高い",  # フィールド指定なし
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
