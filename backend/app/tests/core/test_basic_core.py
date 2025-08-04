"""
コアモジュールのテスト
"""
from app.core.config import settings
from app.core.exceptions import (
    GameChatError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    RateLimitError,
    SecurityError,
    DataNotFoundError
)


class TestConfig:
    """設定のテスト"""
    
    def test_settings_loaded(self):
        """設定が正常に読み込まれることをテスト"""
        assert settings is not None
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'UPSTASH_VECTOR_URL')
    
    def test_testing_environment(self):
        """テスト環境の設定確認"""
        # テスト環境ではTESTING=trueが設定されるべき
        assert hasattr(settings, 'BACKEND_TESTING')


class TestExceptions:
    """例外クラスのテスト"""
    
    def test_gamechat_error(self):
        """GameChatError基底クラスのテスト"""
        error = GameChatError("テストエラー")
        assert str(error) == "テストエラー"
        assert error.message == "テストエラー"
    
    def test_validation_error(self):
        """ValidationErrorのテスト"""
        error = ValidationError("バリデーションエラー")
        assert str(error) == "バリデーションエラー"
        assert isinstance(error, GameChatError)
    
    def test_authentication_error(self):
        """AuthenticationErrorのテスト"""
        error = AuthenticationError("認証エラー")
        assert str(error) == "認証エラー"
        assert isinstance(error, GameChatError)
    
    def test_authorization_error(self):
        """AuthorizationErrorのテスト"""
        error = AuthorizationError("認可エラー")
        assert str(error) == "認可エラー"
        assert isinstance(error, GameChatError)
    
    def test_external_service_error(self):
        """ExternalServiceErrorのテスト"""
        error = ExternalServiceError("外部サービスエラー")
        assert str(error) == "外部サービスエラー"
        assert isinstance(error, GameChatError)
    
    def test_rate_limit_error(self):
        """RateLimitErrorのテスト"""
        error = RateLimitError("レート制限エラー")
        assert str(error) == "レート制限エラー"
        assert isinstance(error, GameChatError)
    
    def test_security_error(self):
        """SecurityErrorのテスト"""
        error = SecurityError("セキュリティエラー")
        assert str(error) == "セキュリティエラー"
        assert isinstance(error, GameChatError)
    
    def test_data_not_found_error(self):
        """DataNotFoundErrorのテスト"""
        error = DataNotFoundError("データが見つかりません")
        assert str(error) == "データが見つかりません"
        assert isinstance(error, GameChatError)
