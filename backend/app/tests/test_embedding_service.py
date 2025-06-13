import pytest
from unittest.mock import MagicMock, patch
from backend.app.services.embedding_service import EmbeddingService
from backend.app.models.classification_models import ClassificationResult, QueryType


class TestEmbeddingService:
    """EmbeddingServiceのテスト"""

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService()

    @pytest.fixture
    def mock_openai_embedding_response(self):
        """OpenAI埋め込みレスポンスのモック"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536次元のモック
        return mock_response

    @pytest.mark.asyncio
    async def test_get_embedding_from_classification_high_confidence(self, embedding_service, mock_openai_embedding_response):
        """高信頼度の分類結果で要約を使用するテスト"""
        with patch.object(embedding_service, 'client') as mock_client:
            mock_client.embeddings.create.return_value = mock_openai_embedding_response
            
            classification = ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="強いポケモンの検索",
                confidence=0.9,
                search_keywords=["強い", "ポケモン"],
                reasoning="高信頼度での要約"
            )
            
            result = await embedding_service.get_embedding_from_classification(
                "強いポケモンを教えて", classification
            )
            
            # 埋め込み生成が呼ばれることを確認
            mock_client.embeddings.create.assert_called_once()
            # 要約が使用されることを確認
            call_args = mock_client.embeddings.create.call_args
            assert call_args[1]['input'] == "強いポケモンの検索"
            assert len(result) == 1536

    @pytest.mark.asyncio
    async def test_get_embedding_from_classification_medium_confidence_semantic(self, embedding_service, mock_openai_embedding_response):
        """中信頼度のセマンティック検索でキーワード組み合わせを使用するテスト"""
        with patch.object(embedding_service, 'client') as mock_client:
            mock_client.embeddings.create.return_value = mock_openai_embedding_response
            
            classification = ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="ポケモン検索",
                confidence=0.6,
                search_keywords=["強い", "おすすめ"],
                reasoning="中信頼度での分類"
            )
            
            await embedding_service.get_embedding_from_classification(
                "強いポケモンはありますか", classification
            )
            
            # キーワード + 元質問の組み合わせが使用されることを確認
            call_args = mock_client.embeddings.create.call_args
            expected_text = "強い おすすめ 強いポケモンはありますか"
            assert call_args[1]['input'] == expected_text

    @pytest.mark.asyncio
    async def test_get_embedding_from_classification_low_confidence_fallback(self, embedding_service, mock_openai_embedding_response):
        """低信頼度での元質問フォールバックテスト"""
        with patch.object(embedding_service, 'client') as mock_client:
            mock_client.embeddings.create.return_value = mock_openai_embedding_response
            
            classification = ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="検索",
                confidence=0.3,
                search_keywords=["検索"],
                reasoning="低信頼度"
            )
            
            original_query = "HPが高いポケモンを探しています"
            await embedding_service.get_embedding_from_classification(
                original_query, classification
            )
            
            # 元質問が使用されることを確認
            call_args = mock_client.embeddings.create.call_args
            assert call_args[1]['input'] == original_query

    @pytest.mark.asyncio
    async def test_get_embedding_from_classification_hybrid_type(self, embedding_service, mock_openai_embedding_response):
        """ハイブリッドタイプでのキーワード組み合わせテスト"""
        with patch.object(embedding_service, 'client') as mock_client:
            mock_client.embeddings.create.return_value = mock_openai_embedding_response
            
            classification = ClassificationResult(
                query_type=QueryType.HYBRID,
                summary="炎タイプの強いポケモン",
                confidence=0.7,
                filter_keywords=["炎", "タイプ"],
                search_keywords=["強い"],
                reasoning="ハイブリッド検索"
            )
            
            await embedding_service.get_embedding_from_classification(
                "炎タイプで強いポケモンを教えて", classification
            )
            
            # 全キーワード + 元質問の組み合わせが使用されることを確認
            call_args = mock_client.embeddings.create.call_args
            input_text = call_args[1]['input']
            assert "強い" in input_text
            assert "炎" in input_text
            assert "タイプ" in input_text
            assert "炎タイプで強いポケモンを教えて" in input_text

    def test_is_summary_quality_good_valid_summary(self, embedding_service):
        """有効な要約の品質テスト"""
        original_query = "HPが100以上のポケモンを探しています"
        summary = "HP100以上のポケモン検索"
        
        result = embedding_service._is_summary_quality_good(summary, original_query)
        assert result is True

    def test_is_summary_quality_good_too_short(self, embedding_service):
        """短すぎる要約の品質テスト"""
        original_query = "HPが100以上のポケモンを探しています"
        summary = "HP"
        
        result = embedding_service._is_summary_quality_good(summary, original_query)
        assert result is False

    def test_is_summary_quality_good_too_long(self, embedding_service):
        """長すぎる要約の品質テスト"""
        original_query = "強いポケモン"
        summary = "非常に強力で戦闘能力が高く、バトルで活躍できる優秀なポケモンの詳細な検索クエリ"
        
        result = embedding_service._is_summary_quality_good(summary, original_query)
        assert result is False

    def test_is_summary_quality_good_missing_keywords(self, embedding_service):
        """重要キーワードが欠落した要約の品質テスト"""
        original_query = "炎タイプのポケモンを探しています"
        summary = "検索クエリ"  # タイプやポケモンの情報が失われている
        
        result = embedding_service._is_summary_quality_good(summary, original_query)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_embedding_from_classification_api_error_fallback(self, embedding_service):
        """API エラー時のフォールバックテスト"""
        with patch.object(embedding_service, 'client') as mock_client:
            # 最初の呼び出しでエラー、2回目は成功
            mock_client.embeddings.create.side_effect = [
                Exception("API Error"),
                MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
            ]
            
            classification = ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="強いポケモン検索",
                confidence=0.9,
                reasoning="テスト"
            )
            
            result = await embedding_service.get_embedding_from_classification(
                "強いポケモンを教えて", classification
            )
            
            # フォールバックで元の get_embedding が呼ばれることを確認
            assert mock_client.embeddings.create.call_count == 2
            assert len(result) == 1536
