"""
Core moduleの基本テスト
カバレッジ向上のための基本機能テスト
"""


class TestCoreConfigurationBasics:
    """Core設定の基本テスト"""
    
    def test_config_import(self):
        """config.pyの基本インポートテスト"""
        from app.core.config import settings
        assert settings is not None
        
    def test_logging_import(self):
        """logging.pyの基本インポートテスト"""
        from app.core.logging import GameChatLogger
        assert GameChatLogger is not None
        
    def test_exceptions_import(self):
        """exceptions.pyの基本インポートテスト"""
        from app.core.exceptions import (
            GameChatException,
            AuthenticationException,
            ValidationException
        )
        assert GameChatException is not None
        assert AuthenticationException is not None
        assert ValidationException is not None


class TestCoreExceptions:
    """例外クラスの基本テスト"""
    
    def test_gamechat_exception_creation(self):
        """GameChatExceptionの作成テスト"""
        from app.core.exceptions import GameChatException
        
        error = GameChatException("Test error")
        assert str(error) == "Test error"
        assert error.code == "INTERNAL_ERROR"
        
    def test_authentication_exception_creation(self):
        """AuthenticationExceptionの作成テスト"""
        from app.core.exceptions import AuthenticationException
        
        error = AuthenticationException("Auth failed")
        assert str(error) == "Auth failed"
        assert error.code == "AUTH_ERROR"
        
    def test_validation_exception_creation(self):
        """ValidationExceptionの作成テスト"""
        from app.core.exceptions import ValidationException
        
        error = ValidationException("Invalid input")
        assert str(error) == "Invalid input"
        assert error.code == "VALIDATION_ERROR"


class TestCoreLogging:
    """ロギング機能の基本テスト"""
    
    def test_logger_configuration(self):
        """ロガー設定のテスト"""
        from app.core.logging import GameChatLogger
        
        # ロガー設定実行
        GameChatLogger.configure_logging()
        
        # ロガー取得
        logger = GameChatLogger.get_logger("test")
        assert logger is not None
        assert logger.name == "test"
        
    def test_logger_methods_exist(self):
        """ロガーメソッドの存在確認"""
        from app.core.logging import GameChatLogger
        
        assert hasattr(GameChatLogger, 'configure_logging')
        assert hasattr(GameChatLogger, 'get_logger')
        assert hasattr(GameChatLogger, 'log_error')
        assert hasattr(GameChatLogger, 'log_info')


class TestCoreDecorators:
    """デコレータの基本テスト"""
    
    def test_decorators_import(self):
        """デコレータのインポートテスト"""
        from app.core.decorators import (
            handle_exceptions,
            handle_service_exceptions,
            handle_api_exceptions
        )
        
        assert handle_exceptions is not None
        assert handle_service_exceptions is not None
        assert handle_api_exceptions is not None


class TestCoreSecurityModules:
    """セキュリティモジュールの基本テスト"""
    
    def test_security_audit_import(self):
        """セキュリティ監査モジュールのインポート"""
        from app.core.security_audit import SeverityLevel
        assert SeverityLevel is not None
        
    def test_intrusion_detection_import(self):
        """侵入検知システムのインポート"""
        from app.core.intrusion_detection import IntrusionDetectionSystem
        ids = IntrusionDetectionSystem()
        assert ids is not None
        
    def test_security_audit_manager_import(self):
        """セキュリティ監査マネージャのインポート"""
        from app.core.security_audit_manager import SecurityAuditManager
        manager = SecurityAuditManager()
        assert manager is not None
