import pytest
from unittest.mock import patch
from backend.app.services.database_service import DatabaseService
from backend.app.models.rag_models import ContextItem


class TestDatabaseService:
    """データベース検索サービスのテスト"""

    # === セットアップ・フィクスチャ ===
    @pytest.fixture
    def database_service(self):
        return DatabaseService()

    @pytest.fixture
    def mock_settings(self, monkeypatch):
        """設定をモックするフィクスチャ"""
        from backend.app.core.config import settings
        
        # テスト用のパスを設定
        monkeypatch.setattr(settings, "DATA_FILE_PATH", "/test/path/data.json")
        monkeypatch.setattr(settings, "CONVERTED_DATA_FILE_PATH", "/test/path/convert_data.json")
        return settings

    @pytest.fixture
    def sample_data(self):
        """テスト用のサンプルデータ"""
        return [
            {
                "id": "test-001",
                "name": "テストポケモン1",
                "type": "炎",
                "hp": 120,
                "species": "テストポケモン",
                "stage": "たね",
                "attacks": [{"name": "テスト技", "damage": 50}],
                "weakness": "水"
            },
            {
                "id": "test-002", 
                "name": "テストポケモン2",
                "type": "水",
                "hp": 80,
                "species": "テストポケモン",
                "stage": "1進化",
                "attacks": [{"name": "みずでっぽう", "damage": 30}],
                "weakness": "草"
            },
            {
                "id": "test-003",
                "name": "テストポケモン3",
                "type": "草",
                "hp": 150,
                "species": "テストポケモン",
                "stage": "2進化",
                "attacks": [{"name": "はっぱカッター", "damage": 60}],
                "weakness": "炎"
            }
        ]

    @pytest.fixture
    def mock_data(self):
        """複合条件テスト用のモックデータ"""
        return [
            {
                "id": "test-001",
                "name": "カメックス",
                "type": "水",
                "hp": 150,
                "attacks": [
                    {"name": "みずでっぽう", "damage": 40},
                    {"name": "ハイドロポンプ", "damage": 80}
                ]
            },
            {
                "id": "test-002",
                "name": "フシギダネ",
                "type": "草",
                "hp": 70,
                "attacks": [
                    {"name": "はっぱカッター", "damage": 30},
                    {"name": "つるのムチ", "damage": 10}
                ]
            },
            {
                "id": "test-003",
                "name": "ゼニガメ",
                "type": "水",
                "hp": 60,
                "attacks": [
                    {"name": "たいあたり", "damage": 20},
                    {"name": "みずでっぽう", "damage": 50}
                ]
            }
        ]

    # === 正常系テスト ===
    class TestNormalCases:
        """正常系のテストケース"""
        
        def test_load_data_success(self, database_service, sample_data, monkeypatch):
            """データ読み込み成功テスト"""
            mock_open = patch("builtins.open", create=True)
            mock_json_load = patch("json.load", return_value=sample_data)
            
            with mock_open, mock_json_load:
                data = database_service._load_data()
                assert len(data) == 3
                assert data[0]["name"] == "テストポケモン1"

        @pytest.mark.asyncio
        async def test_filter_search_with_valid_keywords_hp_condition(self, database_service, sample_data, monkeypatch):
            """HP条件でのフィルター検索テスト"""
            # データ読み込みをモック
            monkeypatch.setattr(database_service, "_load_data", lambda: sample_data)
            
            results = await database_service.filter_search(["HP", "100以上"], top_k=5)
            
            # HP100以上のポケモンを確認
            assert len(results) == 2  # HP120とHP150のポケモン
            assert all(isinstance(item, ContextItem) for item in results)
            
            # 結果の内容を確認
            names = [item.title for item in results]
            assert "テストポケモン1" in names  # HP120
            assert "テストポケモン3" in names  # HP150

        @pytest.mark.asyncio
        async def test_filter_search_with_valid_keywords_type_condition(self, database_service, sample_data, monkeypatch):
            """タイプ条件でのフィルター検索テスト"""
            monkeypatch.setattr(database_service, "_load_data", lambda: sample_data)
            
            results = await database_service.filter_search(["炎"], top_k=5)
            
            assert len(results) == 1
            assert results[0].title == "テストポケモン1"
            assert results[0].score == 2.5  # タイプマッチ(+2.0) + テキストマッチ(+0.5)

        @pytest.mark.asyncio
        async def test_filter_search_damage_and_type_condition(self, database_service, mock_data, monkeypatch):
            """ダメージ条件とタイプ条件の複合検索テスト"""
            # データ読み込みをモック
            monkeypatch.setattr(database_service, "_load_data", lambda: mock_data)
            
            # 水タイプで40以上のダメージを持つポケモンの検索
            keywords = ["ダメージ", "40以上", "技", "水", "タイプ"]
            results = await database_service.filter_search(keywords, 5)
            
            # 結果を確認
            assert len(results) >= 1  # カメックスとゼニガメが該当するはず
            assert isinstance(results, list)
            # 水タイプで40以上のダメージ技を持つポケモンが上位に来ることを確認
            if len(results) > 0:
                assert results[0].score >= 5.0  # 複合条件マッチで高スコア

        def test_calculate_filter_score_basic_hp_match(self, database_service):
            """HP条件の基本スコア計算テスト"""
            item = {"name": "テスト", "hp": 120, "type": "炎"}
            keywords = ["HP", "100以上"]
            
            score = database_service._calculate_filter_score(item, keywords)
            
            assert score > 0  # HP120は100以上の条件にマッチ
            assert score >= 1.0  # 2つのキーワードのうち2つマッチで正規化後1.0

        def test_calculate_filter_score_basic_type_match(self, database_service):
            """タイプ条件の基本スコア計算テスト"""
            item = {"name": "テスト", "type": "炎", "hp": 80}
            keywords = ["炎"]
            
            score = database_service._calculate_filter_score(item, keywords)
            
            assert score == 2.5  # タイプマッチ(+2.0) + テキストマッチ(+0.5)

        def test_extract_title_with_name(self, database_service):
            """タイトル抽出テスト（name属性）"""
            item = {"name": "ピカチュウ", "type": "電気"}
            assert database_service._extract_title(item) == "ピカチュウ"

        def test_extract_title_with_title_attribute(self, database_service):
            """タイトル抽出テスト（title属性）"""
            item = {"title": "テストタイトル"}
            assert database_service._extract_title(item) == "テストタイトル"

        def test_extract_text_complete_data(self, database_service):
            """完全なデータでのテキスト抽出テスト"""
            item = {
                "name": "ピカチュウ",
                "type": "電気",
                "hp": 60,
                "species": "ねずみポケモン",
                "stage": "たね",
                "attacks": [{"name": "でんきショック"}],
                "weakness": "闘"
            }
            
            text = database_service._extract_text(item)
            
            assert "タイプ: 電気" in text
            assert "HP: 60" in text
            assert "種類: ねずみポケモン" in text
            assert "進化段階: たね" in text
            assert "弱点: 闘" in text

        def test_database_service_with_config(self, mock_settings):
            """設定を使用したデータベースサービスの初期化テスト"""
            service = DatabaseService()
            
            # 設定からパスが取得されることを確認
            assert service.data_path == "/test/path/data.json"
            assert service.converted_data_path == "/test/path/convert_data.json"

        @pytest.mark.asyncio
        async def test_filter_search_with_custom_paths(self, mock_settings, sample_data):
            """カスタムパスでの検索テスト"""
            service = DatabaseService()
            
            # _load_dataメソッドをモックして、設定されたパスが使用されることを確認
            with patch.object(service, '_load_data', return_value=sample_data):
                results = await service.filter_search(["炎"], top_k=5)
                
                assert len(results) == 1
                assert results[0].title == "テストポケモン1"

    # === 異常系テスト ===
    class TestErrorCases:
        """異常系・エラーケースのテスト"""
        
        def test_load_data_file_not_found(self, database_service, monkeypatch):
            """ファイルが見つからない場合のテスト"""
            mock_open = patch("builtins.open", side_effect=FileNotFoundError)
            
            with mock_open:
                data = database_service._load_data()
                assert data == []

        @pytest.mark.asyncio
        async def test_filter_search_with_empty_keywords(self, database_service, sample_data, monkeypatch):
            """キーワードなしでの検索テスト"""
            monkeypatch.setattr(database_service, "_load_data", lambda: sample_data)
            
            results = await database_service.filter_search([], top_k=5)
            
            assert len(results) == 0  # キーワードなしなので結果なし

        @pytest.mark.asyncio
        async def test_filter_search_with_empty_data(self, database_service, monkeypatch):
            """データなしでの検索テスト"""
            monkeypatch.setattr(database_service, "_load_data", lambda: [])
            
            results = await database_service.filter_search(["HP", "100以上"], top_k=5)
            
            # フォールバック結果を確認
            assert len(results) == 1
            assert "データベース検索" in results[0].title

        def test_calculate_filter_score_no_match(self, database_service):
            """マッチなしのスコア計算テスト"""
            item = {"name": "テスト", "type": "水", "hp": 50}
            keywords = ["炎", "HP", "100以上"]
            
            score = database_service._calculate_filter_score(item, keywords)
            
            assert score < 0.5  # マッチ度が低い

        def test_extract_title_no_name_or_title(self, database_service):
            """タイトル抽出テスト（nameもtitleもない）"""
            item = {"type": "炎"}  # nameもtitleもない
            assert database_service._extract_title(item) == "不明なアイテム"

    # === パフォーマンステスト ===
    class TestPerformance:
        """パフォーマンス関連のテスト"""
        
        @pytest.mark.asyncio
        async def test_filter_search_damage_condition_only(self, database_service, mock_data, monkeypatch):
            """ダメージ条件のみでの検索パフォーマンステスト"""
            # データ読み込みをモック
            monkeypatch.setattr(database_service, "_load_data", lambda: mock_data)
            
            keywords = ["ダメージ", "40以上", "技"]
            results = await database_service.filter_search(keywords, 5)
            
            # 結果を確認
            assert isinstance(results, list)
            assert len(results) >= 2  # カメックスとゼニガメが該当するはず

        def test_calculate_filter_score_damage_match(self, database_service):
            """ダメージ条件マッチのスコア計算パフォーマンステスト"""
            item = {
                "name": "テストポケモン",
                "type": "水",
                "attacks": [
                    {"name": "みずでっぽう", "damage": 50},
                    {"name": "ハイドロポンプ", "damage": 30}
                ]
            }
            keywords = ["ダメージ", "40以上", "技"]
            score = database_service._calculate_filter_score(item, keywords)
            
            # ダメージ50の技があるので、40以上の条件にマッチしてスコアが付くはず
            assert score > 0

        def test_calculate_filter_score_damage_and_type_match(self, database_service):
            """ダメージ条件とタイプ条件の複合マッチのスコア計算パフォーマンステスト"""
            item = {
                "name": "カメックス",
                "type": "水",
                "attacks": [
                    {"name": "ハイドロポンプ", "damage": 60}
                ]
            }
            keywords = ["ダメージ", "40以上", "技", "水", "タイプ"]
            score = database_service._calculate_filter_score(item, keywords)
            
            # 水タイプ（+2.0）とダメージ40以上（+2.0）の両方にマッチするので高スコア
            assert score >= 4.0  # 少なくとも4.0以上のスコアが期待される
