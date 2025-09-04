"""
テスト用の共通フィクスチャ定義
"""
# テスト環境での設定を最初に行う
import os
os.environ["BACKEND_ENVIRONMENT"] = "test"
os.environ["BACKEND_LOG_LEVEL"] = "CRITICAL"

import pytest
import json
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import MagicMock, patch


# アプリケーションモジュールのインポート
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.tests.mocks.vector_service_mock import MockVectorService

# ヘルパークラスのインポート
from app.tests.fixtures.mock_factory import TestDataFactory, MockResponseFactory
from app.tests.fixtures.test_helpers import TestAssertions

# 新しいモックシステムのインポート
from app.tests.mocks import (
    MockUpstashResult,
    MockClassificationResult,
    MockOpenAIResponse,
    MockDatabaseConnection,
    ContextItemFactory,
    ClassificationResultFactory,
    TestScenarioFactory
)

# logging.basicConfig(level=logging.CRITICAL, format='%(message)s')  # ← Cloud Run/本番と同じロギング構成に統一
from app.core.logging import GameChatLogger
GameChatLogger.configure_logging()

# テスト実行時に環境変数を読み込み
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=True)

# テスト環境変数を設定
os.environ["BACKEND_TESTING"] = "true"
# テスト用のダミーAPIキーを設定（実際のAPIコールは発生しない）
os.environ["BACKEND_OPENAI_API_KEY"] = "test-api-key-for-testing"
os.environ["BACKEND_UPSTASH_VECTOR_REST_URL"] = "https://test-vector-db.upstash.io"
os.environ["BACKEND_UPSTASH_VECTOR_REST_TOKEN"] = "test-vector-token"


# ==============================================================================
# 新しいモックシステム用フィクスチャ
# ==============================================================================

@pytest.fixture
def context_item_factory():
    """ContextItemファクトリーのインスタンス"""
    return ContextItemFactory()


@pytest.fixture
def classification_result_factory():
    """ClassificationResultファクトリーのインスタンス"""
    return ClassificationResultFactory()


@pytest.fixture
def mock_upstash_result():
    """MockUpstashResultのインスタンス"""
    return MockUpstashResult


@pytest.fixture
def mock_classification_result():
    """MockClassificationResultのインスタンス"""
    return MockClassificationResult


@pytest.fixture
def mock_openai_response():
    """MockOpenAIResponseのインスタンス"""
    return MockOpenAIResponse


@pytest.fixture
def mock_database_connection():
    """MockDatabaseConnectionのインスタンス"""
    return MockDatabaseConnection


@pytest.fixture
def test_scenario_factory():
    """TestScenarioFactoryのインスタンス"""
    return TestScenarioFactory


# ==============================================================================
# 共通フィクスチャ
# ==============================================================================

@pytest.fixture
def test_data_factory():
    """テストデータファクトリーのインスタンス"""
    return TestDataFactory()


@pytest.fixture
def mock_response_factory():
    """モックレスポンスファクトリーのインスタンス"""
    return MockResponseFactory()


@pytest.fixture
def test_assertions():
    """テストアサーションヘルパーのインスタンス"""
    return TestAssertions()


# サービスインスタンス系フィクスチャ（分類/ハイブリッド/RAGはMVPから除外）


@pytest.fixture
def embedding_service():
    """埋め込みサービスのインスタンス（テスト用の非モックモード）"""
    # 直接サービスインスタンスを作成し、必要なプロパティを設定
    service = EmbeddingService()
    
    # 強制的に非モック状態に設定
    service.is_mocked = False
    
    # ダミーのOpenAIクライアントを設定（実際のAPIは呼び出されない）
    import openai
    try:
        service.client = openai.OpenAI(api_key="sk-test-dummy-key-for-testing")
    except Exception:
        # OpenAIクライアント作成に失敗した場合もダミークライアントを設定
        from unittest.mock import MagicMock
        service.client = MagicMock()
    
    return service


@pytest.fixture
def vector_service():
    """ベクトルサービスのインスタンス（テスト用モック）"""
    return MockVectorService()


## database_service / hybrid_search_service / rag_service は削除


@pytest.fixture
def llm_service():
    """LLMサービスのインスタンス"""
    return LLMService()


# ContextItem系フィクスチャ
@pytest.fixture
def sample_context_items(test_data_factory):
    """基本的なContextItemのサンプル"""
    return test_data_factory.create_context_items()


@pytest.fixture
def game_card_context_items(test_data_factory):
    """ゲームカード関連のContextItem"""
    return test_data_factory.create_game_card_context_items()


@pytest.fixture
def high_quality_context_items(test_data_factory):
    """高品質なContextItem"""
    return test_data_factory.create_high_quality_context_items()


@pytest.fixture
def low_quality_context_items(test_data_factory):
    """低品質なContextItem"""
    return test_data_factory.create_low_quality_context_items()


@pytest.fixture
def db_search_results(test_data_factory):
    """データベース検索結果"""
    return test_data_factory.create_db_search_results()


@pytest.fixture
def vector_search_results(test_data_factory):
    """ベクトル検索結果"""
    return test_data_factory.create_vector_search_results()


## 分類系フィクスチャは全削除（MVP）


# モック系フィクスチャ
@pytest.fixture
def mock_openai_embedding_response():
    """OpenAI埋め込みレスポンスのモック"""
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536次元
    return mock_response


@pytest.fixture
def mock_openai_chat_response():
    """OpenAI チャットレスポンスのモック"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "これはテストレスポンスです。"
    return mock_response


@pytest.fixture
def mock_openai_classification_response():
    """OpenAI 分類レスポンスのモック"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """{
        "query_type": "semantic",
        "summary": "テスト分類結果",
        "confidence": 0.8,
        "filter_keywords": [],
        "search_keywords": ["テスト"],
        "reasoning": "テスト用の分類"
    }"""
    return mock_response


@pytest.fixture
def mock_upstash_response():
    """Upstash検索レスポンスのモック"""
    class MockResult:
        def __init__(self, score: float, metadata: dict):
            self.score = score
            self.metadata = metadata
    
    return [
        MockResult(0.95, {"title": "テスト1", "text": "テスト内容1"}),
        MockResult(0.85, {"title": "テスト2", "text": "テスト内容2"}),
        MockResult(0.75, {"title": "テスト3", "text": "テスト内容3"})
    ]


# ==============================================================================
# テスト環境の共通設定
# ==============================================================================

@pytest.fixture(autouse=True)
def mock_openai_api_key(monkeypatch):
    """
    全テストでOpenAI APIキーを無効化し、実際のAPI呼び出しを防ぐ
    autouse=Trueにより、すべてのテストで自動的に適用される
    """
    # 環境変数のOPENAI_API_KEY/BACKEND_OPENAI_API_KEYを削除またはダミー値に
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("BACKEND_OPENAI_API_KEY", "sk-test-dummy-key-for-testing")
    # propertyではなく実体の変数をパッチする
    monkeypatch.setattr("app.core.config.settings.BACKEND_OPENAI_API_KEY", None)


# ==============================================================================
# OpenAI APIモック用フィクスチャ
# ==============================================================================

@pytest.fixture
def mock_openai_client():
    """OpenAI APIクライアントのモック"""
    
    with patch('openai.OpenAI') as mock_openai:
        # モッククライアントのインスタンスを作成
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # ChatCompletion のモック設定
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "query_type": "semantic",
            "summary": "テスト用セマンティック検索",
            "confidence": 0.8,
            "search_keywords": ["テスト"],
            "filter_keywords": [],
            "reasoning": "テスト用分類"
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Embedding のモック設定
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536  # 1536次元のベクトル
        
        mock_client.embeddings.create.return_value = mock_embedding_response
        
        yield mock_client


## mock_classification_service 不要


@pytest.fixture
def mock_embedding_service(mock_openai_client):
    """モック化されたEmbeddingServiceのフィクスチャ"""
    
    with patch('app.services.embedding_service.EmbeddingService') as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        
        # generate_embedding メソッドのモック設定
        async def mock_generate_embedding(text):
            return [0.1] * 1536  # 1536次元のベクトル
        
        mock_instance.generate_embedding = mock_generate_embedding
        
        yield mock_instance


@pytest.fixture
def mock_llm_service(mock_openai_client):
    """モック化されたLLMServiceのフィクスチャ"""
    
    with patch('app.services.llm_service.LLMService') as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        
        # generate_response メソッドのモック設定
        async def mock_generate_response(context_items, original_query, summary=None):
            return "これはモックからの応答です。テスト用の回答を提供します。"
        
        mock_instance.generate_response = mock_generate_response
        
        yield mock_instance


## mock_all_services 不要


## mock_rag_service 不要


@pytest.fixture
def game_card_titles(test_data_factory):
    """ゲームカード名リスト"""
    return test_data_factory.create_game_card_titles()
