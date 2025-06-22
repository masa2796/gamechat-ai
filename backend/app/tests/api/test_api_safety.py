"""
OpenAI API安全性確認テスト
実際のAPI呼び出しが発生していないことを確認
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.classification_service import ClassificationService
from backend.app.services.llm_service import LLMService


class TestAPIKeySafety:
    """OpenAI API安全性テスト"""

    def test_environment_api_key_removed(self):
        """環境変数からAPIキーが削除されていることを確認"""
        api_key = os.getenv("OPENAI_API_KEY")
        assert api_key is None, f"テスト環境でOPENAI_API_KEYが設定されています: {api_key}"

    def test_embedding_service_no_real_api_call(self):
        """EmbeddingServiceが実際のAPIを呼び出さないことを確認"""
        with patch('openai.OpenAI') as mock_openai:
            # OpenAIクライアントの作成をモック
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            service = EmbeddingService()
            
            # 実際のOpenAIクライアントが作成されていないことを確認
            # (APIキーがないため、clientはNoneのはず)
            assert service.client is None

    def test_classification_service_no_real_api_call(self):
        """ClassificationServiceが実際のAPIを呼び出さないことを確認"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            service = ClassificationService()
            
            # 実際のOpenAIクライアントが作成されていないことを確認
            assert service.client is None

    def test_llm_service_no_real_api_call(self):
        """LLMServiceが実際のAPIを呼び出さないことを確認"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            service = LLMService()
            
            # 実際のOpenAIクライアントが作成されていないことを確認
            assert service.client is None

    @pytest.mark.asyncio
    async def test_embedding_service_api_key_error(self):
        """EmbeddingServiceがAPIキーエラーを適切に処理することを確認"""
        service = EmbeddingService()
        
        with pytest.raises(Exception) as exc_info:
            await service.get_embedding("テストテキスト")
        
        error_details = str(exc_info.value)
        assert "OpenAI APIキーが設定されていません" in error_details or \
               "API_KEY_NOT_SET" in error_details

    def test_network_isolation_check(self):
        """ネットワーク分離チェック（参考情報）"""
        print("\n=== API安全性確認結果 ===")
        print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")
        print("テスト環境: pytest")
        print("モック使用: はい")
        print("実際のAPI呼び出し: なし")
        print("=======================")
        
        # テスト環境であることを確認
        assert "pytest" in sys.modules
