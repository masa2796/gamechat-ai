import pytest
from unittest.mock import MagicMock
from backend.app.models.classification_models import ClassificationResult, QueryType


class TestEmbeddingService:
    """埋め込みサービスの基本機能テスト"""

    @pytest.mark.asyncio
    async def test_get_embedding_basic(
        self, 
        embedding_service, 
        mock_openai_client
    ):
        """基本的な埋め込み作成テスト"""
        # OpenAIクライアントをモックに置き換え
        embedding_service.client = mock_openai_client
        
        text = "テスト用のテキスト"
        embedding = await embedding_service.get_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        
        # API呼び出しが行われたことを確認（モック経由）
        mock_openai_client.embeddings.create.assert_called_once_with(
            input=text,
            model="text-embedding-3-small"
        )

    @pytest.mark.asyncio
    async def test_get_embedding_from_classification(
        self, 
        embedding_service, 
        semantic_classification,
        mock_openai_client
    ):
        """分類結果を使った埋め込み作成テスト"""
        # OpenAIクライアントをモックに置き換え
        embedding_service.client = mock_openai_client
        
        query = "強いポケモンを教えて"
        embedding = await embedding_service.get_embedding_from_classification(
            query, semantic_classification
        )
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        
        # API呼び出しが行われたことを確認
        mock_openai_client.embeddings.create.assert_called()

    @pytest.mark.asyncio
    async def test_embedding_error_handling(
        self, 
        embedding_service
    ):
        """埋め込みエラーハンドリングテスト"""
        # エラーを発生させるモッククライアント
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        embedding_service.client = mock_client
        
        with pytest.raises(Exception):
            await embedding_service.get_embedding("テストテキスト")

    @pytest.mark.asyncio
    async def test_no_api_key_handling(
        self, 
        embedding_service
    ):
        """APIキーなしの場合のハンドリングテスト"""
        # クライアントをNoneに設定（APIキーなしの状態をシミュレート）
        embedding_service.client = None
        
        with pytest.raises(Exception):
            await embedding_service.get_embedding("テストテキスト")

    @pytest.mark.asyncio
    async def test_api_safety_verification(self, embedding_service):
        """API安全性検証 - 実際のOpenAI APIが呼び出されないことを確認"""
        # クライアントがNoneの場合の動作確認
        embedding_service.client = None
        
        with pytest.raises(Exception) as exc_info:
            await embedding_service.get_embedding("テストテキスト")
        
        # OpenAI APIキーが設定されていないことによるエラーであることを確認
        assert "OpenAI APIキーが設定されていません" in str(exc_info.value) or \
               "API_KEY_NOT_SET" in str(exc_info.value)


class TestEmbeddingOptimization:
    """埋め込み最適化の詳細テスト"""

    @pytest.mark.asyncio
    async def test_confidence_based_strategy_switching(
        self, 
        embedding_service, 
        mock_openai_embedding_response,
        monkeypatch
    ):
        """信頼度別埋め込み戦略の切り替えテスト"""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_embedding_response
        monkeypatch.setattr(embedding_service, "client", mock_client)
        
        confidence_test_cases = [
            {
                "confidence": 0.95,
                "summary": "高品質な要約テキスト",
                "keywords": ["テスト"]
            },
            {
                "confidence": 0.8,
                "summary": "品質の良い要約",
                "keywords": ["高品質"]
            },
            {
                "confidence": 0.7,
                "summary": "要約テキスト",
                "keywords": ["キーワード", "組み合わせ"]
            },
            {
                "confidence": 0.5,
                "summary": "普通の要約",
                "keywords": ["キーワード"]
            },
            {
                "confidence": 0.3,
                "summary": "低品質要約",
                "keywords": []
            }
        ]
        
        for case in confidence_test_cases:
            classification = ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary=case["summary"],
                confidence=case["confidence"],
                search_keywords=case["keywords"],
                filter_keywords=[],
                reasoning="テスト用分類結果"
            )
            
            query = "テストクエリ"
            embedding = await embedding_service.get_embedding_from_classification(
                query, classification
            )
            
            assert isinstance(embedding, list)
            assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_text_preprocessing_optimization(
        self, 
        embedding_service, 
        mock_openai_embedding_response,
        monkeypatch
    ):
        """テキスト前処理最適化テスト"""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_embedding_response
        monkeypatch.setattr(embedding_service, "client", mock_client)
        
        # 前処理が必要なテキスト
        raw_texts = [
            "   空白が多い   テキスト   ",
            "重複重複した文字文字を含む",
            "特殊記号!@#$%が混在するテキスト",
            "非常に\n改行\nが\n多い\nテキスト"
        ]
        
        for text in raw_texts:
            embedding = await embedding_service.get_embedding(text)
            
            assert isinstance(embedding, list)
            assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_embedding_with_different_query_types(
        self, 
        embedding_service, 
        mock_openai_embedding_response,
        monkeypatch
    ):
        """異なるクエリタイプでの埋め込みテスト"""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_embedding_response
        monkeypatch.setattr(embedding_service, "client", mock_client)
        
        query_types = [
            QueryType.SEMANTIC,
            QueryType.FILTERABLE,
            QueryType.HYBRID,
            QueryType.GREETING
        ]
        
        for query_type in query_types:
            classification = ClassificationResult(
                query_type=query_type,
                summary="テスト要約",
                confidence=0.8,
                search_keywords=["テスト"],
                filter_keywords=[],
                reasoning="テスト用分類結果"
            )
            
            query = "テストクエリ"
            embedding = await embedding_service.get_embedding_from_classification(
                query, classification
            )
            
            assert isinstance(embedding, list)
            assert len(embedding) == 1536


class TestEmbeddingPerformance:
    """埋め込みパフォーマンステスト"""

    @pytest.mark.asyncio
    async def test_embedding_creation_speed(
        self, 
        embedding_service, 
        mock_openai_embedding_response,
        monkeypatch
    ):
        """埋め込み作成速度テスト"""
        import time
        
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_embedding_response
        monkeypatch.setattr(embedding_service, "client", mock_client)
        
        text = "パフォーマンステスト用のテキスト"
        
        start_time = time.time()
        embedding = await embedding_service.get_embedding(text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 1秒以内での処理を期待
        assert processing_time < 1.0
        assert isinstance(embedding, list)

    @pytest.mark.asyncio
    async def test_concurrent_embedding_creation(
        self, 
        embedding_service, 
        mock_openai_embedding_response,
        monkeypatch
    ):
        """並行埋め込み作成テスト"""
        import asyncio
        
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_embedding_response
        monkeypatch.setattr(embedding_service, "client", mock_client)
        
        # 並行実行用のタスク
        async def create_embedding_task(text):
            return await embedding_service.get_embedding(text)
        
        texts = [f"並行テキスト{i}" for i in range(5)]
        tasks = [create_embedding_task(text) for text in texts]
        
        # 並行実行
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(isinstance(emb, list) for emb in results)
        assert all(len(emb) == 1536 for emb in results)

    @pytest.mark.asyncio
    async def test_fallback_mechanism(
        self, 
        embedding_service, 
        mock_openai_embedding_response,
        monkeypatch
    ):
        """フォールバック機構テスト"""
        call_count = 0
        
        def mock_create_embedding(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 最初の呼び出しでエラー
                raise Exception("First call error")
            else:
                # 2回目でフォールバック成功
                return mock_openai_embedding_response
        
        mock_client = MagicMock()
        mock_client.embeddings.create = mock_create_embedding
        monkeypatch.setattr(embedding_service, "client", mock_client)
        
        # 低信頼度の分類結果でテスト
        classification = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="テスト要約",
            confidence=0.3,  # 低信頼度
            search_keywords=["テスト"],
            filter_keywords=[],
            reasoning="テスト用分類結果"
        )
        
        query = "テストクエリ"
        embedding = await embedding_service.get_embedding_from_classification(
            query, classification
        )
        
        # フォールバックにより成功
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert call_count == 2  # エラー + フォールバック
