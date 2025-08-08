import pytest
from unittest.mock import patch
from app.services.database_service import DatabaseService


class TestComplexNumericPatterns:
    """複雑な数値パターンのテスト（Phase 2）"""

    @pytest.fixture
    def database_service(self):
        """テスト用データベースサービス"""
        with patch('app.services.storage_service.StorageService'):
            service = DatabaseService()
            # テスト用データを設定
            service.data_cache = [
                {
                    "id": "card-001",
                    "name": "低コストカード",
                    "cost": 2,
                    "hp": 30,
                    "attack": 20,
                    "class": "エルフ",
                    "rarity": "ブロンズレア"
                },
                {
                    "id": "card-002", 
                    "name": "中コストカード",
                    "cost": 5,
                    "hp": 50,
                    "attack": 45,
                    "class": "ドラゴン",
                    "rarity": "シルバーレア"
                },
                {
                    "id": "card-003",
                    "name": "高コストカード", 
                    "cost": 8,
                    "hp": 80,
                    "attack": 60,
                    "class": "ロイヤル",
                    "rarity": "ゴールドレア"
                },
                {
                    "id": "card-004",
                    "name": "超高コストカード",
                    "cost": 10,
                    "hp": 100,
                    "attack": 80,
                    "class": "ウィッチ",
                    "rarity": "レジェンド"
                }
            ]
            return service

    def test_parse_complex_numeric_conditions_range(self, database_service):
        """範囲指定パターンのパースをテスト"""
        # HPの範囲指定
        query = "HP50から80の間のカード"
        result = database_service._parse_complex_numeric_conditions(query)
        
        assert len(result["range_conditions"]) == 1
        range_condition = result["range_conditions"][0]
        assert range_condition["field"] == "hp"
        assert range_condition["min_value"] == 50
        assert range_condition["max_value"] == 80

    def test_parse_complex_numeric_conditions_multiple(self, database_service):
        """複数値パターンのパースをテスト"""
        query = "コスト5または8のカード"
        result = database_service._parse_complex_numeric_conditions(query)
        
        assert len(result["multiple_conditions"]) == 1
        multiple_condition = result["multiple_conditions"][0]
        assert multiple_condition["field"] == "cost"
        assert 5 in multiple_condition["values"]
        assert 8 in multiple_condition["values"]

    def test_parse_complex_numeric_conditions_approximate(self, database_service):
        """近似値パターンのパースをテスト"""
        query = "攻撃力約50のカード"
        result = database_service._parse_complex_numeric_conditions(query)
        
        assert len(result["approximate_conditions"]) == 1
        approximate_condition = result["approximate_conditions"][0]
        assert approximate_condition["field"] == "attack"
        assert approximate_condition["value"] == 50
        assert approximate_condition["tolerance"] > 0

    def test_identify_field_in_context(self, database_service):
        """フィールド名特定機能をテスト"""
        # HP関連
        query = "体力が50から80の間"
        field = database_service._identify_field_in_context(query, 3, 10)
        assert field == "hp"
        
        # 攻撃力関連
        query = "ダメージ40または60"
        field = database_service._identify_field_in_context(query, 3, 10)
        assert field == "attack"
        
        # コスト関連
        query = "マナコスト3から5"
        field = database_service._identify_field_in_context(query, 4, 11)
        assert field == "cost"

    def test_normalize_field_name(self, database_service):
        """フィールド名正規化機能をテスト"""
        assert database_service._normalize_field_name("体力") == "hp"
        assert database_service._normalize_field_name("ダメージ") == "attack"
        assert database_service._normalize_field_name("マナコスト") == "cost"
        assert database_service._normalize_field_name("未知フィールド") == "未知フィールド"

    def test_match_complex_numeric_condition_range(self, database_service):
        """範囲条件のマッチングをテスト"""
        item = {"hp": 60, "attack": 45, "cost": 5}
        
        # HP範囲条件（マッチする）
        range_condition = {
            "field": "hp",
            "min_value": 50,
            "max_value": 70
        }
        assert database_service._match_complex_numeric_condition(item, range_condition, "range")
        
        # HP範囲条件（マッチしない）
        range_condition_fail = {
            "field": "hp", 
            "min_value": 70,
            "max_value": 90
        }
        assert not database_service._match_complex_numeric_condition(item, range_condition_fail, "range")

    def test_match_complex_numeric_condition_multiple(self, database_service):
        """複数値条件のマッチングをテスト"""
        item = {"hp": 60, "attack": 45, "cost": 5}
        
        # コスト複数値条件（マッチする）
        multiple_condition = {
            "field": "cost",
            "values": [3, 5, 7]
        }
        assert database_service._match_complex_numeric_condition(item, multiple_condition, "multiple")
        
        # コスト複数値条件（マッチしない）
        multiple_condition_fail = {
            "field": "cost",
            "values": [1, 2, 3]
        }
        assert not database_service._match_complex_numeric_condition(item, multiple_condition_fail, "multiple")

    def test_match_complex_numeric_condition_approximate(self, database_service):
        """近似値条件のマッチングをテスト"""
        item = {"hp": 60, "attack": 45, "cost": 5}
        
        # 攻撃力近似条件（マッチする）
        approximate_condition = {
            "field": "attack",
            "value": 50,
            "tolerance": 10
        }
        assert database_service._match_complex_numeric_condition(item, approximate_condition, "approximate")
        
        # 攻撃力近似条件（マッチしない）
        approximate_condition_fail = {
            "field": "attack",
            "value": 20,
            "tolerance": 5
        }
        assert not database_service._match_complex_numeric_condition(item, approximate_condition_fail, "approximate")

    @pytest.mark.asyncio
    async def test_filter_search_with_range_pattern(self, database_service):
        """範囲パターンを使ったフィルタ検索をテスト"""
        # HP50から80の間のカードを検索
        results = await database_service.filter_search_llm_async("HP50から80の間", 10)
        
        # 該当するカードの名前を確認
        result_names = [name for name in results if name]
        assert "中コストカード" in result_names or "高コストカード" in result_names

    @pytest.mark.asyncio
    async def test_filter_search_with_multiple_pattern(self, database_service):
        """複数値パターンを使ったフィルタ検索をテスト"""
        # コスト5または8のカードを検索
        results = await database_service.filter_search_llm_async("コスト5または8", 10)
        
        # 該当するカードの名前を確認
        result_names = [name for name in results if name]
        assert "中コストカード" in result_names or "高コストカード" in result_names

    @pytest.mark.asyncio
    async def test_filter_search_with_approximate_pattern(self, database_service):
        """近似値パターンを使ったフィルタ検索をテスト"""
        # 攻撃力約45のカードを検索
        results = await database_service.filter_search_llm_async("攻撃力約45", 10)
        
        # 該当するカードの名前を確認
        result_names = [name for name in results if name]
        assert len(result_names) > 0  # 近似値なので何らかの結果があることを確認

    def test_fallback_with_complex_patterns(self, database_service):
        """フォールバック処理での複雑パターン処理をテスト"""
        item = {"hp": 60, "attack": 45, "cost": 5, "name": "テストカード"}
        
        # 範囲パターンでのマッチング
        result = database_service._match_filterable_fallback(item, "HP50から80の間")
        assert result
        
        # マッチしない範囲パターン
        result = database_service._match_filterable_fallback(item, "HP90から100の間")
        assert not result

    def test_get_mock_query_analysis_with_complex_patterns(self, database_service):
        """モック環境での複雑パターン解析をテスト"""
        # 範囲パターン
        result = database_service._get_mock_query_analysis("HP50から80の間")
        hp_condition = result["conditions"]["hp"]
        assert hp_condition["operator"] == "範囲"
        assert hp_condition["value"] == 50
        assert hp_condition["max_value"] == 80
        
        # 複数値パターン
        result = database_service._get_mock_query_analysis("攻撃力40または60")
        attack_condition = result["conditions"]["attack"]
        assert attack_condition["operator"] == "複数値"
        assert attack_condition["value"] == 40
        assert 60 in attack_condition["additional_values"]
        
        # 近似値パターン
        result = database_service._get_mock_query_analysis("約コスト5")
        cost_condition = result["conditions"]["cost"]
        assert cost_condition["operator"] == "近似"
        assert cost_condition["value"] == 5
