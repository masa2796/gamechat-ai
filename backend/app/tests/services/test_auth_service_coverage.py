"""
AuthServiceの実機能テスト（カバレッジ向上）
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi import Request, Response
from app.services.auth_service import AuthService


class TestAuthServiceReCAPTCHA:
    """reCAPTCHA機能のテスト"""
    
    @pytest.fixture
    def auth_service(self):
        """AuthServiceのインスタンス"""
        return AuthService()
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_skip_flag(self, auth_service):
        """reCAPTCHAスキップフラグのテスト"""
        with patch.dict('os.environ', {'BACKEND_SKIP_RECAPTCHA': 'true'}):
            result = await auth_service.verify_recaptcha("any_token")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_test_token(self, auth_service):
        """テストトークンのテスト"""
        result = await auth_service.verify_recaptcha("test")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_dev_environment(self, auth_service):
        """開発環境でのreCAPTCHAバイパステスト"""
        with patch.dict('os.environ', {'BACKEND_ENVIRONMENT': 'development'}):
            result = await auth_service.verify_recaptcha("any_token")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_test_environment(self, auth_service):
        """テスト環境でのreCAPTCHAバイパステスト"""
        with patch.dict('os.environ', {'BACKEND_ENVIRONMENT': 'test'}):
            result = await auth_service.verify_recaptcha("any_token")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_no_secret_dev(self, auth_service):
        """開発環境で秘密鍵未設定のテスト"""
        with patch.dict('os.environ', {
            'BACKEND_ENVIRONMENT': 'development',
            'RECAPTCHA_SECRET_KEY': '',
            'RECAPTCHA_SECRET_KEY_TEST': ''
        }, clear=True):
            result = await auth_service.verify_recaptcha("token")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_no_secret_prod(self, auth_service):
        """本番環境で秘密鍵未設定のテスト（デバッグ用許可）"""
        with patch.dict('os.environ', {
            'BACKEND_ENVIRONMENT': 'production',
            'RECAPTCHA_SECRET_KEY': '',
            'RECAPTCHA_SECRET_KEY_TEST': ''
        }, clear=True):
            result = await auth_service.verify_recaptcha("token")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_http_success(self, auth_service):
        """reCAPTCHA API成功レスポンスのテスト"""
        with patch.dict('os.environ', {
            'BACKEND_ENVIRONMENT': 'production',
            'RECAPTCHA_SECRET_KEY': 'test_secret'
        }):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'score': 0.9,
                'action': 'login'
            }
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                result = await auth_service.verify_recaptcha("valid_token")
                assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_http_failure(self, auth_service):
        """reCAPTCHA API失敗レスポンスのテスト"""
        with patch.dict('os.environ', {
            'BACKEND_ENVIRONMENT': 'production',
            'RECAPTCHA_SECRET_KEY': 'test_secret'
        }):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': False,
                'error-codes': ['invalid-input-response']
            }
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                result = await auth_service.verify_recaptcha("invalid_token")
                assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_http_error_status(self, auth_service):
        """reCAPTCHA APIエラーステータスのテスト"""
        with patch.dict('os.environ', {
            'BACKEND_ENVIRONMENT': 'production',
            'RECAPTCHA_SECRET_KEY': 'test_secret'
        }):
            mock_response = Mock()
            mock_response.status_code = 500
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                result = await auth_service.verify_recaptcha("any_token")
                assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_exception_prod(self, auth_service):
        """reCAPTCHA API例外（本番環境）のテスト"""
        with patch.dict('os.environ', {
            'BACKEND_ENVIRONMENT': 'production',
            'RECAPTCHA_SECRET_KEY': 'test_secret'
        }):
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))
                
                result = await auth_service.verify_recaptcha("any_token")
                assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_recaptcha_exception_dev(self, auth_service):
        """reCAPTCHA API例外（開発環境）のテスト"""
        with patch.dict('os.environ', {'BACKEND_ENVIRONMENT': 'development'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Network error"))
                
                result = await auth_service.verify_recaptcha("any_token")
                assert result is True


class TestAuthServiceSuspicious:
    """疑わしいアクセス検知のテスト"""
    
    @pytest.fixture
    def auth_service(self):
        """AuthServiceのインスタンス"""
        return AuthService()
    
    def test_is_suspicious_bot_user_agents(self, auth_service):
        """疑わしいUser-Agentの検知テスト"""
        mock_request = Mock(spec=Request)
        
        bot_agents = ["bot", "crawler", "spider", "scraper", "curl", "wget"]
        
        for agent in bot_agents:
            mock_request.headers = {"user-agent": f"Test {agent} v1.0"}
            result = auth_service.is_suspicious(mock_request, "127.0.0.1")
            assert result is True
    
    def test_is_suspicious_normal_user_agent(self, auth_service):
        """正常なUser-Agentのテスト"""
        mock_request = Mock(spec=Request)
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        result = auth_service.is_suspicious(mock_request, "127.0.0.1")
        assert result is False
    
    def test_is_suspicious_missing_user_agent(self, auth_service):
        """User-Agent未設定のテスト"""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        
        result = auth_service.is_suspicious(mock_request, "127.0.0.1")
        assert result is False


class TestAuthServiceVerifyRequest:
    """統合認証検証のテスト"""
    
    @pytest.fixture
    def auth_service(self):
        """AuthServiceのインスタンス"""
        return AuthService()
    
    @pytest.mark.asyncio
    async def test_verify_request_already_passed(self, auth_service):
        """既に認証済みの場合のテスト"""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "Mozilla/5.0"}
        mock_response = Mock(spec=Response)
        
        with patch.object(auth_service, 'is_suspicious', return_value=False):
            result = await auth_service.verify_request(
                mock_request, mock_response, None, "true"
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_request_suspicious_with_token(self, auth_service):
        """疑わしいアクセスでトークンありのテスト"""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_response = Mock(spec=Response)
        
        with patch.object(auth_service, 'is_suspicious', return_value=True), \
             patch.object(auth_service, 'verify_recaptcha', return_value=True), \
             patch.object(auth_service, '_set_auth_cookie'):
            
            result = await auth_service.verify_request(
                mock_request, mock_response, "valid_token", "true"
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_request_suspicious_without_token(self, auth_service):
        """疑わしいアクセスでトークンなしのテスト"""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_response = Mock(spec=Response)
        
        with patch.object(auth_service, 'is_suspicious', return_value=True):
            result = await auth_service.verify_request(
                mock_request, mock_response, None, "true"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_request_suspicious_failed_verification(self, auth_service):
        """疑わしいアクセスで再検証失敗のテスト"""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_response = Mock(spec=Response)
        
        with patch.object(auth_service, 'is_suspicious', return_value=True), \
             patch.object(auth_service, 'verify_recaptcha', return_value=False):
            
            result = await auth_service.verify_request(
                mock_request, mock_response, "invalid_token", "true"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_request_first_time_success(self, auth_service):
        """初回認証成功のテスト"""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_response = Mock(spec=Response)
        
        with patch.object(auth_service, 'verify_recaptcha', return_value=True), \
             patch.object(auth_service, '_set_auth_cookie'):
            
            result = await auth_service.verify_request(
                mock_request, mock_response, "valid_token", None
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_request_first_time_no_token(self, auth_service):
        """初回認証でトークンなしのテスト"""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_response = Mock(spec=Response)
        
        result = await auth_service.verify_request(
            mock_request, mock_response, None, None
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_request_first_time_failed(self, auth_service):
        """初回認証失敗のテスト"""
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"
        mock_response = Mock(spec=Response)
        
        with patch.object(auth_service, 'verify_recaptcha', return_value=False):
            result = await auth_service.verify_request(
                mock_request, mock_response, "invalid_token", None
            )
            assert result is False


class TestAuthServiceCookie:
    """認証Cookie設定のテスト"""
    
    @pytest.fixture
    def auth_service(self):
        """AuthServiceのインスタンス"""
        return AuthService()
    
    def test_set_auth_cookie(self, auth_service):
        """認証Cookie設定のテスト"""
        mock_response = Mock(spec=Response)
        mock_response.set_cookie = Mock()
        
        auth_service._set_auth_cookie(mock_response)
        
        # Cookieが設定されたことを確認
        mock_response.set_cookie.assert_called_once()
        call_args = mock_response.set_cookie.call_args
        
        assert call_args[1]['key'] == 'recaptcha_passed'
        assert call_args[1]['value'] == 'true'
        assert call_args[1]['httponly'] is True
        assert call_args[1]['secure'] is True
        assert call_args[1]['samesite'] == 'none'
        assert call_args[1]['max_age'] == 60*60*24*7
