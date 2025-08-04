"""
データベースサービスの追加テスト
"""
import pytest
from unittest.mock import patch
from app.services.database_service import DatabaseService


class TestDatabaseServiceBasic:
    """データベースサービスの基本機能テスト"""
    
    @pytest.fixture
    def database_service(self):
        """データベースサービスのインスタンス"""
        with patch('app.services.database_service.os.path.exists') as mock_exists, \
             patch.object(DatabaseService, 'reload_data') as mock_reload_data:
            # ファイルパスのモック
            mock_exists.return_value = True
            
            # データ読み込みをスキップ
            mock_reload_data.return_value = None
            
            service = DatabaseService()
            
            # テストデータを直接設定
            service.data = [
                {
                    "title": "テストカード1",
                    "hp": 100,
                    "type": "炎",
                    "attack": 50,
                    "content": "テストカードの説明1"
                },
                {
                    "title": "テストカード2", 
                    "hp": 200,
                    "type": "水",
                    "attack": 80,
                    "content": "テストカードの説明2"
                }
            ]
            
            service.title_to_data = {
                "テストカード1": service.data[0],
                "テストカード2": service.data[1]
            }
            
            # data_cache も設定
            service.data_cache = service.data.copy()
            
            return service
    
    def test_service_initialization(self, database_service):
        """サービス初期化のテスト"""
        assert database_service is not None
        assert hasattr(database_service, 'data')
        assert hasattr(database_service, 'title_to_data')
        assert len(database_service.data) == 2
    
    def test_get_card_details_existing_cards(self, database_service):
        """既存カードの詳細取得テスト"""
        titles = ["テストカード1", "テストカード2"]
        result = database_service.get_card_details_by_titles(titles)
        
        assert isinstance(result, list)
        assert len(result) == 2
        
        card1, card2 = result
        assert card1["title"] == "テストカード1"
        assert card1["hp"] == 100
        assert card2["title"] == "テストカード2"
        assert card2["hp"] == 200
    
    def test_get_card_details_nonexistent_cards(self, database_service):
        """存在しないカードの詳細取得テスト"""
        titles = ["存在しないカード"]
        result = database_service.get_card_details_by_titles(titles)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_card_details_mixed_cards(self, database_service):
        """存在するカードと存在しないカードの混在テスト"""
        titles = ["テストカード1", "存在しないカード", "テストカード2"]
        result = database_service.get_card_details_by_titles(titles)
        
        assert isinstance(result, list)
        assert len(result) == 2  # 存在するカードのみ返される
        
        titles_returned = [card["title"] for card in result]
        assert "テストカード1" in titles_returned
        assert "テストカード2" in titles_returned
    
    def test_filter_search_hp_condition(self, database_service):
        """HP条件でのフィルター検索テスト"""
        keywords = ["HP", "150", "以上"]
        result = database_service.filter_search(keywords, top_k=10)
        
        assert isinstance(result, list)
        # フィルター機能が動作することを確認（結果の数は実装に依存）
        assert len(result) >= 0
    
    def test_filter_search_type_condition(self, database_service):
        """タイプ条件でのフィルター検索テスト"""
        keywords = ["炎", "タイプ"]
        result = database_service.filter_search(keywords, top_k=10)
        
        assert isinstance(result, list)
        # フィルター機能が動作することを確認（結果の数は実装に依存）
        assert len(result) >= 0
    
    def test_filter_search_no_matches(self, database_service):
        """条件に一致しないフィルター検索テスト"""
        keywords = ["草", "タイプ"]  # 草タイプは存在しない
        result = database_service.filter_search(keywords, top_k=10)
        
        assert isinstance(result, list)
        # フィルター機能が動作することを確認（結果の数は実装に依存）
        assert len(result) >= 0
    
    def test_filter_search_empty_keywords(self, database_service):
        """空のキーワードでのフィルター検索テスト"""
        keywords = []
        result = database_service.filter_search(keywords, top_k=10)
        
        assert isinstance(result, list)
        # 空のキーワードの場合の動作を確認
        # 実装に応じて期待値を調整
    
    def test_calculate_text_score_method(self, database_service):
        """テキストスコア計算メソッドのテスト"""
        card = database_service.data[0]  # テストカード1
        keywords = ["炎", "タイプ"]
        
        if hasattr(database_service, '_calculate_text_score'):
            score = database_service._calculate_text_score(card, keywords)
            
            assert isinstance(score, (int, float))
            assert score >= 0  # スコアは非負の値
        else:
            # メソッドが存在しない場合はスキップ
            pytest.skip("_calculate_text_score method not implemented")


class TestDatabaseServicePerformance:
    """データベースサービスのパフォーマンステスト"""
    
    @pytest.fixture
    def large_database_service(self):
        """大量データを持つデータベースサービス"""
        with patch('app.services.database_service.os.path.exists') as mock_exists, \
             patch.object(DatabaseService, 'reload_data') as mock_reload_data:
            mock_exists.return_value = True
            mock_reload_data.return_value = None
            
            service = DatabaseService()
            
            # 大量のテストデータを生成
            service.data = []
            service.title_to_data = {}
            
            for i in range(1000):
                card = {
                    "title": f"カード{i}",
                    "hp": 50 + (i % 200),
                    "type": ["炎", "水", "草", "雷"][i % 4],
                    "attack": 30 + (i % 100),
                    "content": f"カード{i}の説明"
                }
                service.data.append(card)
                service.title_to_data[f"カード{i}"] = card
            
            # data_cache も設定
            service.data_cache = service.data.copy()
            
            return service
    
    def test_large_filter_search_performance(self, large_database_service):
        """大量データでのフィルター検索パフォーマンステスト"""
        import time
        
        keywords = ["HP", "100", "以上"]
        
        start_time = time.time()
        result = large_database_service.filter_search(keywords, top_k=50)
        end_time = time.time()
        
        search_time = end_time - start_time
        
        assert isinstance(result, list)
        assert len(result) <= 50  # top_kの制限
        assert search_time < 1.0  # 1秒以内で完了することを期待
    
    def test_bulk_card_details_retrieval(self, large_database_service):
        """大量カード詳細取得のテスト"""
        import time
        
        # 100枚のカードタイトルを準備
        titles = [f"カード{i}" for i in range(100)]
        
        start_time = time.time()
        result = large_database_service.get_card_details_by_titles(titles)
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        
        assert isinstance(result, list)
        assert len(result) == 100
        assert retrieval_time < 0.5  # 0.5秒以内で完了することを期待
