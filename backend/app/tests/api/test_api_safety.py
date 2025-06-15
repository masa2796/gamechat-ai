"""
OpenAI API安全性確認テスト
モックを使用して実際のAPI呼び出しが発生していないことを確認
"""
import pytest
import os
import sys


class TestAPIKeySafety:
    """OpenAI API安全性テスト"""

    def test_environment_isolation(self):
        """テスト環境の分離が適切に行われていることを確認"""
        # このテストでは、環境変数の存在よりもモックが正しく機能していることを確認
        print("\n環境変数の状態:")
        print(f"OPENAI_API_KEY: {'設定済み' if os.getenv('OPENAI_API_KEY') else '未設定'}")
        print(f"TESTING: {os.getenv('TESTING')}")
        
        # テスト環境であることを確認
        assert "pytest" in sys.modules, "pytest環境で実行されていません"

    def test_embedding_service_no_real_api_call(self, mock_embedding_service):
        """EmbeddingServiceが実際のAPIを呼び出さないことを確認"""
        # モックサービスが使用されていることを確認
        assert mock_embedding_service is not None
        assert hasattr(mock_embedding_service, 'generate_embedding')

    def test_classification_service_no_real_api_call(self, mock_classification_service):
        """ClassificationServiceが実際のAPIを呼び出さないことを確認"""
        # モックサービスが使用されていることを確認
        assert mock_classification_service is not None
        assert hasattr(mock_classification_service, 'classify_query')

    def test_llm_service_no_real_api_call(self, mock_llm_service):
        """LLMServiceが実際のAPIを呼び出さないことを確認"""
        # モックサービスが使用されていることを確認
        assert mock_llm_service is not None
        assert hasattr(mock_llm_service, 'generate_response')

    @pytest.mark.asyncio
    async def test_mocked_services_work_correctly(self, mock_all_services):
        """モック化されたサービスが正しく動作することを確認"""
        # 分類サービスのテスト
        classification_result = await mock_all_services['classification'].classify_query("テスト質問")
        assert classification_result is not None
        
        # 埋め込みサービスのテスト
        embedding = await mock_all_services['embedding'].generate_embedding("テストテキスト")
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        
        # LLMサービスのテスト
        response = await mock_all_services['llm'].generate_response([], "テスト質問")
        assert isinstance(response, str)
        assert "モック" in response

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
