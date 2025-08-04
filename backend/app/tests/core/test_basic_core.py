"""
コアモジュールのテスト
"""
from app.core.config import settings
from app.core.exceptions import (
    GameChatException,
    ValidationException,
    AuthenticationException,
    DatabaseServiceException,
    DatabaseException,
    VectorSearchException,
    EmbeddingException,
    ClassificationException,
    LLMException,
    StorageException
)


class TestConfig:
    """設定のテスト"""
    
    def test_settings_loaded(self):
        """設定が正常に読み込まれることをテスト"""
        assert settings is not None
        assert hasattr(settings, 'BACKEND_OPENAI_API_KEY')
        assert hasattr(settings, 'UPSTASH_VECTOR_REST_URL')
    
    def test_testing_environment(self):
        """テスト環境の設定確認"""
        # テスト環境では実際に存在する設定を確認
        assert hasattr(settings, 'ENVIRONMENT')
        assert hasattr(settings, 'DEBUG')


class TestExceptions:
    """例外クラスのテスト"""
    
    def test_gamechat_exception(self):
        """GameChatException基底クラスのテスト"""
        error = GameChatException("テストエラー")
        assert str(error) == "テストエラー"
        assert error.message == "テストエラー"
    
    def test_validation_exception(self):
        """ValidationExceptionのテスト"""
        error = ValidationException("バリデーションエラー")
        assert str(error) == "バリデーションエラー"
        assert isinstance(error, GameChatException)
    
    def test_authentication_exception(self):
        """AuthenticationExceptionのテスト"""
        error = AuthenticationException("認証エラー")
        assert str(error) == "認証エラー"
        assert isinstance(error, GameChatException)
    
    def test_database_service_exception(self):
        """DatabaseServiceExceptionのテスト"""
        error = DatabaseServiceException("データベースサービスエラー")
        assert str(error) == "データベースサービスエラー"
        assert isinstance(error, GameChatException)
    
    def test_vector_search_exception(self):
        """VectorSearchExceptionのテスト"""
        error = VectorSearchException("ベクトル検索エラー")
        assert str(error) == "ベクトル検索エラー"
        assert isinstance(error, GameChatException)
    
    def test_embedding_exception(self):
        """EmbeddingExceptionのテスト"""
        error = EmbeddingException("埋め込み生成エラー")
        assert str(error) == "埋め込み生成エラー"
        assert isinstance(error, GameChatException)
    
    def test_classification_exception(self):
        """ClassificationExceptionのテスト"""
        error = ClassificationException("分類処理エラー")
        assert str(error) == "分類処理エラー"
        assert isinstance(error, GameChatException)
    
    def test_llm_exception(self):
        """LLMExceptionのテスト"""
        error = LLMException("LLM処理エラー")
        assert str(error) == "LLM処理エラー"
        assert isinstance(error, GameChatException)
    
    def test_storage_exception(self):
        """StorageExceptionのテスト"""
        error = StorageException("ストレージ操作エラー")
        assert str(error) == "ストレージ操作エラー"
        assert isinstance(error, GameChatException)
