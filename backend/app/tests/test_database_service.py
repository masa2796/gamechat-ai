import pytest
from unittest.mock import AsyncMock, patch
from backend.app.services.database_service import DatabaseService
from backend.app.models.rag_models import ContextItem


class TestDatabaseService:
    """データベース検索サービスのテスト"""

    @pytest.fixture
    def database_service(self):
        return DatabaseService()

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

    def test_load_data_success(self, database_service, sample_data, monkeypatch):
        """データ読み込み成功テスト"""
        mock_open = patch("builtins.open", create=True)
        mock_json_load = patch("json.load", return_value=sample_data)
        
        with mock_open, mock_json_load:
            data = database_service._load_data()
            assert len(data) == 3
            assert data[0]["name"] == "テストポケモン1"

    def test_load_data_file_not_found(self, database_service, monkeypatch):
        """ファイルが見つからない場合のテスト"""
        mock_open = patch("builtins.open", side_effect=FileNotFoundError)
        
        with mock_open:
            data = database_service._load_data()
            assert data == []

    @pytest.mark.asyncio
    async def test_filter_search_hp_condition(self, database_service, sample_data, monkeypatch):
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
    async def test_filter_search_type_condition(self, database_service, sample_data, monkeypatch):
        """タイプ条件でのフィルター検索テスト"""
        monkeypatch.setattr(database_service, "_load_data", lambda: sample_data)
        
        results = await database_service.filter_search(["炎"], top_k=5)
        
        assert len(results) == 1
        assert results[0].title == "テストポケモン1"
        assert results[0].score == 1.0  # 完全一致

    @pytest.mark.asyncio
    async def test_filter_search_no_keywords(self, database_service, sample_data, monkeypatch):
        """キーワードなしでの検索テスト"""
        monkeypatch.setattr(database_service, "_load_data", lambda: sample_data)
        
        results = await database_service.filter_search([], top_k=5)
        
        assert len(results) == 0  # キーワードなしなので結果なし

    @pytest.mark.asyncio
    async def test_filter_search_no_data(self, database_service, monkeypatch):
        """データなしでの検索テスト"""
        monkeypatch.setattr(database_service, "_load_data", lambda: [])
        
        results = await database_service.filter_search(["HP", "100以上"], top_k=5)
        
        # フォールバック結果を確認
        assert len(results) == 1
        assert "データベース検索" in results[0].title

    def test_calculate_filter_score_hp_match(self, database_service):
        """HP条件のスコア計算テスト"""
        item = {"name": "テスト", "hp": 120, "type": "炎"}
        keywords = ["HP", "100以上"]
        
        score = database_service._calculate_filter_score(item, keywords)
        
        assert score > 0  # HP120は100以上の条件にマッチ
        assert score >= 1.0  # 2つのキーワードのうち2つマッチで正規化後1.0

    def test_calculate_filter_score_type_match(self, database_service):
        """タイプ条件のスコア計算テスト"""
        item = {"name": "テスト", "type": "炎", "hp": 80}
        keywords = ["炎"]
        
        score = database_service._calculate_filter_score(item, keywords)
        
        assert score == 1.0  # 完全一致

    def test_calculate_filter_score_no_match(self, database_service):
        """マッチなしのスコア計算テスト"""
        item = {"name": "テスト", "type": "水", "hp": 50}
        keywords = ["炎", "HP", "100以上"]
        
        score = database_service._calculate_filter_score(item, keywords)
        
        assert score < 0.5  # マッチ度が低い

    def test_extract_title(self, database_service):
        """タイトル抽出テスト"""
        item1 = {"name": "ピカチュウ", "type": "電気"}
        item2 = {"title": "テストタイトル"}
        item3 = {"type": "炎"}  # nameもtitleもない
        
        assert database_service._extract_title(item1) == "ピカチュウ"
        assert database_service._extract_title(item2) == "テストタイトル"
        assert database_service._extract_title(item3) == "不明なアイテム"

    def test_extract_text(self, database_service):
        """テキスト抽出テスト"""
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
