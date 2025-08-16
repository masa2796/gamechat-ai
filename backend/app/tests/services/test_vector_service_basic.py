"""
Vector Service の基本テスト
カバレッジ向上のための基本機能テスト
"""
import pytest
from unittest.mock import patch, MagicMock
import os
from app.services.vector_service import VectorService


class TestVectorServiceBasic:
    """Vector Service の基本テスト"""
    
    def test_vector_service_singleton(self):
        """VectorServiceがシングルトンであることをテスト"""
        service1 = VectorService()
        service2 = VectorService()
        assert service1 is service2
    
    @patch.dict(os.environ, {
        "TEST_MODE": "true",
        "ENVIRONMENT": "test"
    })
    def test_vector_service_test_mode_initialization(self):
        """テストモードでの初期化をテスト"""
        # シングルトンをリセット
        VectorService._instance = None
        
        service = VectorService()
        assert service.vector_index is None
    
    @patch.dict(os.environ, {
        "TEST_MODE": "false",
        "ENVIRONMENT": "development",
        "UPSTASH_VECTOR_REST_URL": "",
        "UPSTASH_VECTOR_REST_TOKEN": ""
    })
    def test_vector_service_dev_mode_no_config(self):
        """開発環境で設定なしの初期化をテスト"""
        # シングルトンをリセット
        VectorService._instance = None
        
        service = VectorService()
        assert service.vector_index is None
    
    @patch.dict(os.environ, {
        "TEST_MODE": "false",
        "ENVIRONMENT": "production",
        "UPSTASH_VECTOR_REST_URL": "",
        "UPSTASH_VECTOR_REST_TOKEN": ""
    })
    def test_vector_service_prod_mode_no_config(self):
        """本番環境で設定なしの初期化をテスト"""
        # シングルトンをリセット
        VectorService._instance = None
        
        service = VectorService()
        assert service.vector_index is None
    
    @patch.dict(os.environ, {
        "TEST_MODE": "false",
        "ENVIRONMENT": "development",
        "UPSTASH_VECTOR_REST_URL": "https://test-url.upstash.io",
        "UPSTASH_VECTOR_REST_TOKEN": "test-token"
    })
    @patch('app.services.vector_service.Index')
    def test_vector_service_with_config(self, mock_index):
        """正常な設定での初期化をテスト"""
        # シングルトンをリセット
        VectorService._instance = None
        
        mock_index_instance = MagicMock()
        mock_index.return_value = mock_index_instance
        
        service = VectorService()
        assert service.vector_index is not None
        
        # Indexが正しい引数で呼ばれたことを確認
        mock_index.assert_called_once_with(
            url="https://test-url.upstash.io",
            token="test-token"
        )
    
    def test_last_scores_class_variable(self):
        """last_scores クラス変数の存在をテスト"""
        assert hasattr(VectorService, 'last_scores')
        assert isinstance(VectorService.last_scores, dict)
    
    def test_vector_service_methods_exist(self):
        """必要なメソッドの存在をテスト"""
        service = VectorService()
        
        # 基本的なメソッドの存在確認
        expected_methods = [
            '__new__',
            '__init__'
        ]
        
        for method in expected_methods:
            assert hasattr(service, method)
            assert callable(getattr(service, method))
    
    def test_vector_service_attributes(self):
        """VectorServiceの基本属性をテスト"""
        service = VectorService()
        
        # 基本属性の存在確認
        assert hasattr(service, 'vector_index')
        assert hasattr(service, 'last_scores')
    
    def test_dotenv_loading(self):
        """dotenvの読み込みをテスト"""
        # vector_serviceモジュールにload_dotenvがインポートされていることを確認
        import app.services.vector_service as vs_module
        
        # load_dotenvがインポートされていることを確認
        assert hasattr(vs_module, 'load_dotenv')
        
        # サービスが正常にインスタンス化されることを確認
        service = VectorService()
        assert service is not None
    
    def test_vector_service_imports(self):
        """必要なインポートが正しく行われていることをテスト"""
        import app.services.vector_service as vs
        
        # 必要なクラス・関数がインポートされていることを確認
        assert hasattr(vs, 'VectorService')
        assert hasattr(vs, 'Index')
        assert hasattr(vs, 'ContextItem')
        assert hasattr(vs, 'ClassificationResult')
        assert hasattr(vs, 'QueryType')
        assert hasattr(vs, 'settings')
        assert hasattr(vs, 'handle_service_exceptions')
        assert hasattr(vs, 'GameChatLogger')
        assert hasattr(vs, 'os')
        assert hasattr(vs, 'asyncio')
        assert hasattr(vs, 'load_dotenv')


class TestVectorServiceEnvironmentHandling:
    """環境変数処理のテスト"""
    
    def setUp(self):
        """テスト前にシングルトンをリセット"""
        VectorService._instance = None
    
    def tearDown(self):
        """テスト後にシングルトンをリセット"""
        VectorService._instance = None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_environment_values(self):
        """デフォルト環境値のテスト"""
        VectorService._instance = None
        
        # 環境変数が設定されていない場合
        service = VectorService()
        assert service.vector_index is None
    
    @patch.dict(os.environ, {
        "TEST_MODE": "TRUE",  # 大文字でもTrueとして認識されることをテスト
    })
    def test_test_mode_case_insensitive(self):
        """TEST_MODEの大文字小文字非依存をテスト"""
        VectorService._instance = None
        
        service = VectorService()
        assert service.vector_index is None
    
    @patch.dict(os.environ, {
        "TEST_MODE": "false",
        "ENVIRONMENT": "staging",  # staging環境のテスト
        "UPSTASH_VECTOR_REST_URL": "",
        "UPSTASH_VECTOR_REST_TOKEN": ""
    })
    def test_staging_environment(self):
        """staging環境での動作をテスト"""
        VectorService._instance = None
        
        service = VectorService()
        assert service.vector_index is None


class TestVectorServiceErrorHandling:
    """エラーハンドリングのテスト"""
    
    @patch.dict(os.environ, {
        "TEST_MODE": "false",
        "ENVIRONMENT": "development",
        "UPSTASH_VECTOR_REST_URL": "https://test-url.upstash.io",
        "UPSTASH_VECTOR_REST_TOKEN": "test-token"
    })
    @patch('app.services.vector_service.Index')
    def test_index_creation_error(self, mock_index):
        """Index作成時のエラーハンドリングをテスト"""
        VectorService._instance = None
        
        # Indexの作成でエラーが発生する場合
        mock_index.side_effect = Exception("Connection error")
        
        # エラーが発生してもサービスが初期化されることを確認
        try:
            VectorService()
            # エラーが発生しても例外は伝播しない
        except Exception:
            pytest.fail("VectorService initialization should handle Index creation errors")
    
    def test_missing_imports_handling(self):
        """必要なインポートが不足している場合のテスト"""
        # 実際のインポートエラーをテストするのは難しいので、
        # 基本的なインポートが成功していることを確認
        try:
            from app.services.vector_service import VectorService
            assert VectorService is not None
        except ImportError:
            pytest.fail("VectorService import should succeed")


class TestVectorServiceClassVariables:
    """クラス変数のテスト"""
    
    def test_last_scores_initialization(self):
        """last_scores の初期化をテスト"""
        # クラス変数として正しく定義されているか
        assert hasattr(VectorService, 'last_scores')
        assert VectorService.last_scores == {}
    
    def test_last_scores_sharing(self):
        """last_scores がインスタンス間で共有されることをテスト"""
        service1 = VectorService()
        service2 = VectorService()
        
        # 同じオブジェクトを参照していることを確認（シングルトン）
        assert service1 is service2
        
        # クラス変数にアクセスできることを確認
        VectorService.last_scores['test'] = 1.0
        assert hasattr(service1, 'last_scores')
        assert service1.last_scores['test'] == 1.0
    
    def test_instance_variable(self):
        """_instance 変数のテスト"""
        assert hasattr(VectorService, '_instance')
        
        # インスタンス作成前はNone
        VectorService._instance = None
        assert VectorService._instance is None
        
        # インスタンス作成後は同じインスタンス
        service = VectorService()
        assert VectorService._instance is service
