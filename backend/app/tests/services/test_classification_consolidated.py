import pytest
from unittest.mock import MagicMock
from backend.app.models.classification_models import (
    ClassificationRequest, 
    ClassificationResult, 
    QueryType
)
from backend.app.tests.mocks import MockOpenAIResponse


class TestClassificationService:
    """分類サービスの基本機能テスト"""

    @pytest.mark.asyncio
    async def test_classify_filterable_query(
        self, 
        classification_service, 
        mock_openai_client
    ):
        """フィルター可能クエリの分類テスト"""
        # OpenAIクライアントをモックに置き換え
        classification_service.client = mock_openai_client
        
        request = ClassificationRequest(query="HPが100以上のポケモン")
        result = await classification_service.classify_query(request)
        
        assert isinstance(result, ClassificationResult)
        assert result.query_type == QueryType.SEMANTIC
        assert result.confidence == 0.8
        
        # API呼び出しが行われたことを確認
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_semantic_query(
        self, 
        classification_service, 
        semantic_classification
    ):
        """意味検索クエリの分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="semantic",
            summary="強いポケモンの検索",
            confidence=0.8,
            search_keywords=["強い", "ポケモン"],
            filter_keywords=[]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        classification_service.client = mock_client
        
        request = ClassificationRequest(query="強いポケモンを教えて")
        result = await classification_service.classify_query(request)
        
        assert result.query_type == QueryType.SEMANTIC
        assert "強い" in result.search_keywords
        assert "ポケモン" in result.search_keywords

    @pytest.mark.asyncio
    async def test_classify_greeting_query(
        self, 
        classification_service,
        monkeypatch
    ):
        """挨拶クエリの分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="greeting",
            summary="挨拶",
            confidence=0.9,
            search_keywords=[],
            filter_keywords=[]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="こんにちは")
        result = await classification_service.classify_query(request)
        
        assert result.query_type == QueryType.GREETING
        assert len(result.search_keywords) == 0
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_classify_specific_filterable_query(
        self, 
        classification_service,
        monkeypatch
    ):
        """特定のフィルター可能クエリの分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="filterable",
            summary="ピカチュウの特定検索",
            confidence=0.95,
            search_keywords=["ピカチュウ", "でんき", "ポケモン"],
            filter_keywords=["ピカチュウ"]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="ピカチュウについて教えて")
        result = await classification_service.classify_query(request)
        
        assert result.query_type == QueryType.FILTERABLE
        assert "ピカチュウ" in result.filter_keywords
        assert "ピカチュウ" in result.search_keywords


class TestClassificationEdgeCases:
    """分類サービスのエッジケース・例外パターンテスト"""

    @pytest.mark.asyncio
    async def test_classify_inappropriate_content(
        self, 
        classification_service, 
        monkeypatch
    ):
        """不適切コンテンツの分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="greeting",
            summary="不適切な表現",
            confidence=0.9,
            search_keywords=[],
            filter_keywords=[]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        inappropriate_queries = [
            "お前バカか？",
            "クソゲーだな",
            "うざい",
            "死ね"
        ]
        
        for query in inappropriate_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # 不適切なコンテンツは検索をスキップ
            assert result.query_type == QueryType.GREETING
            assert len(result.search_keywords) == 0
            assert len(result.filter_keywords) == 0

    @pytest.mark.asyncio
    async def test_classify_off_topic_questions(
        self, 
        classification_service, 
        monkeypatch
    ):
        """ゲーム以外の話題の分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="greeting",
            summary="ゲーム外の話題",
            confidence=0.8,
            search_keywords=[],
            filter_keywords=[]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        off_topic_queries = [
            "今日の天気は？",
            "料理のレシピを教えて",
            "数学の問題を解いて",
            "プログラミングについて"
        ]
        
        for query in off_topic_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # オフトピックは挨拶として扱い、検索をスキップ
            assert result.query_type == QueryType.GREETING
            assert len(result.search_keywords) == 0

    @pytest.mark.asyncio
    async def test_classify_empty_or_invalid_queries(
        self, 
        classification_service, 
        monkeypatch
    ):
        """空または無効なクエリの分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="greeting",
            summary="無効なクエリ",
            confidence=0.1,
            search_keywords=[],
            filter_keywords=[]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        invalid_queries = [
            "",
            "   ",
            "aaaaaaaaa",
            "123456789",
            "!!!!!!!!!"
        ]
        
        for query in invalid_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # 無効なクエリは信頼度が低い
            assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_classify_very_long_queries(
        self, 
        classification_service, 
        monkeypatch
    ):
        """非常に長いクエリの分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="semantic",
            summary="長いクエリの要約",
            confidence=0.7,
            search_keywords=["ポケモン", "バトル", "戦略"],
            filter_keywords=["ポケモン"]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        # 非常に長いクエリ
        long_query = "ポケモンバトルにおいて" + "効果的な戦略について" * 50 + "教えてください"
        
        request = ClassificationRequest(query=long_query)
        result = await classification_service.classify_query(request)
        
        # 長いクエリでも適切に分類される
        assert result.query_type in [QueryType.SEMANTIC, QueryType.FILTERABLE]
        assert len(result.search_keywords) > 0

    @pytest.mark.asyncio 
    async def test_classify_multilingual_queries(
        self, 
        classification_service, 
        monkeypatch
    ):
        """多言語クエリの分類テスト"""
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="semantic",
            summary="英語でのポケモン検索",
            confidence=0.8,
            search_keywords=["Pokemon", "electric", "type"],
            filter_keywords=["Pokemon"]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        multilingual_queries = [
            "Tell me about Pokemon",
            "Pokemon电气类型",
            "포켓몬에 대해 알려주세요"
        ]
        
        for query in multilingual_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # 多言語でも適切に分類される
            assert isinstance(result, ClassificationResult)
            assert result.confidence > 0.5


class TestClassificationPerformance:
    """分類サービスのパフォーマンステスト"""

    @pytest.mark.asyncio
    async def test_classification_response_time(
        self, 
        classification_service, 
        monkeypatch
    ):
        """分類レスポンス時間テスト"""
        import time
        
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="semantic",
            summary="パフォーマンステスト",
            confidence=0.8,
            search_keywords=["テスト"],
            filter_keywords=[]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        request = ClassificationRequest(query="パフォーマンステスト")
        
        start_time = time.time()
        result = await classification_service.classify_query(request)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # レスポンス時間が1秒以内であることを確認
        assert response_time < 1.0
        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_batch_classification_performance(
        self, 
        classification_service, 
        monkeypatch
    ):
        """バッチ分類パフォーマンステスト"""
        import time
        
        # 新しいモックシステムを使用
        mock_response = MockOpenAIResponse.create_classification_response(
            query_type="semantic",
            summary="バッチテスト",
            confidence=0.8,
            search_keywords=["バッチ"],
            filter_keywords=[]
        )
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        # 複数のクエリを準備
        queries = [f"テストクエリ{i}" for i in range(10)]
        requests = [ClassificationRequest(query=q) for q in queries]
        
        start_time = time.time()
        results = []
        for request in requests:
            result = await classification_service.classify_query(request)
            results.append(result)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / len(requests)
        
        # 平均処理時間が0.5秒以内であることを確認
        assert avg_time < 0.5
        assert len(results) == len(requests)
        assert all(isinstance(r, ClassificationResult) for r in results)

    @pytest.mark.asyncio
    async def test_api_key_safety_check(self, classification_service):
        """APIキーの安全性チェック - 例外が発生することを確認"""
        # クライアントがNoneの場合の例外動作をテスト
        classification_service.client = None
        
        request = ClassificationRequest(query="テストクエリ")
        
        # ClassificationExceptionが発生することを確認
        from backend.app.core.exceptions import ClassificationException
        with pytest.raises(ClassificationException) as exc_info:
            await classification_service.classify_query(request)
        
        assert exc_info.value.code == "API_KEY_NOT_SET"
        assert "OpenAI APIキーが設定されていません" in str(exc_info.value)
