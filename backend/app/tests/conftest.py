"""
テスト用の共通フィクスチャ定義
"""
import pytest
from unittest.mock import MagicMock
from backend.app.services.classification_service import ClassificationService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_service import VectorService
from backend.app.services.database_service import DatabaseService
from backend.app.services.hybrid_search_service import HybridSearchService
from backend.app.services.rag_service import RagService
from backend.app.services.llm_service import LLMService
from backend.app.models.classification_models import ClassificationResult, QueryType

# ヘルパークラスのインポート
from backend.app.tests.fixtures.mock_factory import TestDataFactory, MockResponseFactory
from backend.app.tests.fixtures.test_helpers import TestAssertions

# 新しいモックシステムのインポート
from backend.app.tests.mocks import (
    MockUpstashResult,
    MockClassificationResult,
    MockOpenAIResponse,
    MockDatabaseConnection,
    ContextItemFactory,
    ClassificationResultFactory,
    TestScenarioFactory
)


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


# サービスインスタンス系フィクスチャ
@pytest.fixture
def classification_service():
    """分類サービスのインスタンス"""
    return ClassificationService()


@pytest.fixture
def embedding_service():
    """埋め込みサービスのインスタンス"""
    return EmbeddingService()


@pytest.fixture
def vector_service():
    """ベクトルサービスのインスタンス"""
    return VectorService()


@pytest.fixture
def database_service():
    """データベースサービスのインスタンス"""
    return DatabaseService()


@pytest.fixture
def hybrid_search_service():
    """ハイブリッド検索サービスのインスタンス"""
    return HybridSearchService()


@pytest.fixture
def rag_service():
    """RAGサービスのインスタンス"""
    return RagService()


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
def pokemon_context_items(test_data_factory):
    """ポケモン関連のContextItem"""
    return test_data_factory.create_pokemon_context_items()


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


# ClassificationResult系フィクスチャ
@pytest.fixture
def semantic_classification(test_data_factory):
    """セマンティック分類結果"""
    return test_data_factory.create_semantic_classification()


@pytest.fixture
def greeting_classification():
    """挨拶分類結果のフィクスチャ"""
    return ClassificationResult(
        query_type=QueryType.GREETING,
        summary="挨拶",
        confidence=0.9,
        search_keywords=[],
        filter_keywords=[],
        reasoning="挨拶として分類"
    )


@pytest.fixture
def specific_classification():
    """特定検索分類結果のフィクスチャ"""
    return ClassificationResult(
        query_type=QueryType.FILTERABLE,
        summary="特定のポケモンに関する検索",
        confidence=0.95,
        search_keywords=["ピカチュウ", "でんき"],
        filter_keywords=["ピカチュウ"],
        reasoning="特定のポケモンに関する検索"
    )


@pytest.fixture  
def filterable_classification():
    """フィルター可能分類結果のフィクスチャ"""
    return ClassificationResult(
        query_type=QueryType.FILTERABLE,
        summary="フィルター検索",
        confidence=0.8,
        search_keywords=["ピカチュウ"],
        filter_keywords=["ピカチュウ"],
        reasoning="フィルター可能として分類"
    )


@pytest.fixture
def hybrid_classification(test_data_factory):
    """ハイブリッド分類結果"""
    return test_data_factory.create_hybrid_classification()


@pytest.fixture
def low_confidence_classification(test_data_factory):
    """低信頼度分類結果"""
    return test_data_factory.create_low_confidence_classification()


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
    # 環境変数のOPENAI_API_KEYを削除
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # configからも削除
    monkeypatch.setattr("backend.app.core.config.settings.OPENAI_API_KEY", None)


@pytest.fixture
def mock_openai_client():
    """モックOpenAIクライアントを提供"""
    mock_client = MagicMock()
    
    # 埋め込みレスポンスのモック
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock()]
    mock_embedding_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536次元
    mock_client.embeddings.create.return_value = mock_embedding_response
    
    # チャットレスポンスのモック
    mock_chat_response = MagicMock()
    mock_chat_response.choices = [MagicMock()]
    mock_chat_response.choices[0].message.content = """{
        "query_type": "semantic",
        "summary": "テスト分類結果",
        "confidence": 0.8,
        "filter_keywords": [],
        "search_keywords": ["テスト"],
        "reasoning": "テスト用の分類"
    }"""
    mock_client.chat.completions.create.return_value = mock_chat_response
    
    return mock_client
