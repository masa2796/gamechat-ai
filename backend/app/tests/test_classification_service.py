import pytest
from unittest.mock import MagicMock
from backend.app.models.classification_models import (
    ClassificationRequest, 
    ClassificationResult, 
    QueryType
)
from backend.app.services.classification_service import ClassificationService


class TestClassificationService:
    """分類サービスのテスト"""

    @pytest.fixture
    def classification_service(self):
        return ClassificationService()

    @pytest.fixture
    def mock_openai_response(self):
        """OpenAI APIレスポンスのモック"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "filterable",
            "summary": "HPが100以上のポケモン検索",
            "confidence": 0.9,
            "filter_keywords": ["HP", "100以上"],
            "search_keywords": [],
            "reasoning": "数値条件を検出"
        }"""
        return mock_response

    @pytest.mark.asyncio
    async def test_classify_filterable_query(self, classification_service, mock_openai_response, monkeypatch):
        """フィルター可能クエリの分類テスト"""
        # OpenAI クライアントをモック
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="HPが100以上のポケモン")
        result = await classification_service.classify_query(request)
        
        assert isinstance(result, ClassificationResult)
        assert result.query_type == QueryType.FILTERABLE
        assert result.confidence == 0.9
        assert "HP" in result.filter_keywords
        assert "100以上" in result.filter_keywords

    @pytest.mark.asyncio
    async def test_classify_semantic_query(self, classification_service, monkeypatch):
        """意味検索クエリの分類テスト"""
        # セマンティック検索用のモック
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "semantic",
            "summary": "強いポケモンの検索",
            "confidence": 0.8,
            "filter_keywords": [],
            "search_keywords": ["強い", "ポケモン"],
            "reasoning": "抽象的評価を検出"
        }"""
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="強いポケモンを教えて")
        result = await classification_service.classify_query(request)
        
        assert result.query_type == QueryType.SEMANTIC
        assert result.confidence == 0.8
        assert len(result.filter_keywords) == 0
        assert len(result.search_keywords) > 0

    @pytest.mark.asyncio
    async def test_classify_with_json_parse_error(self, classification_service, monkeypatch):
        """JSON解析エラー時のフォールバックテスト"""
        # 無効なJSONを返すモック
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "無効なJSON"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="テストクエリ")
        result = await classification_service.classify_query(request)
        
        # 修正されたフォールバック値を確認
        assert result.query_type == QueryType.FILTERABLE  # 複合クエリ対応でFILTERABLEに変更
        assert result.confidence == 0.5  # JSONパースエラー時のフォールバック値
        assert "JSON解析エラー" in result.reasoning
        # 手動キーワード抽出の確認
        assert "ダメージ" in result.filter_keywords
        assert "40以上" in result.filter_keywords
        assert "技" in result.filter_keywords
        assert "水" in result.filter_keywords
        assert "タイプ" in result.filter_keywords

    @pytest.mark.asyncio
    async def test_classify_with_api_error(self, classification_service, monkeypatch):
        """API呼び出しエラー時のフォールバックテスト"""
        # API例外を発生させるモック
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="テストクエリ")
        result = await classification_service.classify_query(request)
        
        # エラー時のフォールバック値を確認
        assert result.query_type == QueryType.SEMANTIC
        assert result.confidence == 0.3  # APIエラー時のフォールバック値
        assert "分類エラー" in result.reasoning

    def test_determine_search_strategy_filterable(self, classification_service):
        """フィルター検索戦略の決定テスト"""
        classification = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary="テスト",
            confidence=0.9,
            filter_keywords=["HP", "100以上"],
            search_keywords=[]
        )
        
        strategy = classification_service.determine_search_strategy(classification)
        
        assert strategy.use_db_filter is True
        assert strategy.use_vector_search is False
        assert strategy.db_filter_params is not None

    def test_determine_search_strategy_semantic(self, classification_service):
        """意味検索戦略の決定テスト"""
        classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="テスト",
            confidence=0.8,
            filter_keywords=[],
            search_keywords=["強い"]
        )
        
        strategy = classification_service.determine_search_strategy(classification)
        
        assert strategy.use_db_filter is False
        assert strategy.use_vector_search is True
        assert strategy.vector_search_params is not None

    def test_determine_search_strategy_hybrid(self, classification_service):
        """ハイブリッド検索戦略の決定テスト"""
        classification = ClassificationResult(
            query_type=QueryType.HYBRID,
            summary="テスト",
            confidence=0.7,
            filter_keywords=["炎"],
            search_keywords=["強い"]
        )
        
        strategy = classification_service.determine_search_strategy(classification)
        
        assert strategy.use_db_filter is True
        assert strategy.use_vector_search is True
        assert strategy.db_filter_params is not None
        assert strategy.vector_search_params is not None

    @pytest.mark.asyncio
    async def test_classify_complex_filterable_query(self, classification_service, monkeypatch):
        """複合フィルター条件クエリの分類テスト"""
        # 複合条件用のモック
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "filterable",
            "summary": "ダメージ40以上の技を持つ水タイプポケモン検索",
            "confidence": 0.95,
            "filter_keywords": ["ダメージ", "40以上", "技", "水", "タイプ"],
            "search_keywords": [],
            "reasoning": "技のダメージ条件とタイプ条件を検出"
        }"""
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="ダメージが40以上の技を持つ、水タイプポケモンを教えて")
        result = await classification_service.classify_query(request)
        
        assert result.query_type == QueryType.FILTERABLE
        assert result.confidence == 0.95
        assert "ダメージ" in result.filter_keywords
        assert "40以上" in result.filter_keywords
        assert "技" in result.filter_keywords
        assert "水" in result.filter_keywords
        assert "タイプ" in result.filter_keywords
