import pytest
from backend.app.services.llm_service import LLMService
from backend.app.models.rag_models import ContextItem

@pytest.mark.asyncio
async def test_generate_answer_with_context(monkeypatch):
    # 環境変数でAPIキーを設定
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    
    llm = LLMService()
    context = [ContextItem(title="テスト", text="これはテストです。", score=0.9)]

    class DummyResponse:
        class Choice:
            class Message:
                content = "これはテストです。"
            message = Message()
        choices = [Choice()]
    
    def dummy_create(*args, **kwargs):
        return DummyResponse()
    
    # LLMサービスのクライアントを直接モック
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.chat.completions.create = dummy_create
    llm.client = mock_client

    answer = await llm.generate_answer("テストとは？", context)
    assert isinstance(answer, str)
    assert "テスト" in answer or "情報がありません" in answer

@pytest.mark.asyncio
async def test_generate_answer_greeting(monkeypatch):
    # 環境変数でAPIキーを設定
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    
    llm = LLMService()

    class DummyResponse:
        class Choice:
            class Message:
                content = "こんにちは！ご質問があればどうぞ"
            message = Message()
        choices = [Choice()]
    
    def dummy_create(*args, **kwargs):
        return DummyResponse()
    
    # LLMサービスのクライアントを直接モック
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.chat.completions.create = dummy_create
    llm.client = mock_client

    answer = await llm.generate_answer("おはようございます", [])
    assert "こんにちは" in answer or "ご質問があればどうぞ" in answer

@pytest.mark.asyncio
async def test_generate_answer_with_classification(monkeypatch):
    """分類結果を含む新しい回答生成機能のテスト"""
    # 環境変数でAPIキーを設定
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    
    llm = LLMService()
    context = [ContextItem(title="テストカード", text="これは強力なカードです。", score=0.8)]
    
    # 分類結果のモック
    from backend.app.models.classification_models import ClassificationResult, QueryType
    classification = ClassificationResult(
        query_type=QueryType.SEMANTIC,
        summary="強いカードについて",
        confidence=0.9,
        search_keywords=["強い", "カード"],
        reasoning="意味的検索が適切"
    )
    
    search_info = {
        "db_results_count": 2,
        "vector_results_count": 3,
        "search_quality": {"overall_score": 0.8}
    }

    class DummyResponse:
        class Choice:
            class Message:
                content = "強力なカードについて説明します。"
            message = Message()
        choices = [Choice()]
    
    def dummy_create(*args, **kwargs):
        return DummyResponse()
    
    # LLMサービスのクライアントを直接モック
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.chat.completions.create = dummy_create
    llm.client = mock_client

    answer = await llm.generate_answer(
        query="強いカードを教えて",
        context_items=context,
        classification=classification,
        search_info=search_info
    )
    
    assert isinstance(answer, str)
    assert "強力なカード" in answer or "説明します" in answer

@pytest.mark.asyncio
async def test_format_context_items():
    """コンテキストアイテムのフォーマット機能テスト"""
    llm = LLMService()
    context = [
        ContextItem(title="カード1", text="これは炎タイプです。", score=0.9),
        ContextItem(title="カード2", text="これは水タイプです。", score=0.7)
    ]
    
    formatted = llm._format_context_items(context)
    
    assert "【参考情報 1】" in formatted
    assert "【参考情報 2】" in formatted
    assert "カード1" in formatted
    assert "カード2" in formatted
    assert "関連度: 0.90" in formatted
    assert "関連度: 0.70" in formatted

@pytest.mark.asyncio
async def test_format_classification_info():
    """分類情報のフォーマット機能テスト"""
    llm = LLMService()
    
    from backend.app.models.classification_models import ClassificationResult, QueryType
    classification = ClassificationResult(
        query_type=QueryType.FILTERABLE,
        summary="炎タイプのカード検索",
        confidence=0.85,
        filter_keywords=["炎", "タイプ"],
        search_keywords=[],
        reasoning="フィルター検索が適切"
    )
    
    formatted = llm._format_classification_info(classification)
    
    assert "【質問の分析結果】" in formatted
    assert "filterable" in formatted
    assert "炎タイプのカード検索" in formatted
    assert "0.85" in formatted
    assert "フィルター検索が適切" in formatted

@pytest.mark.asyncio
async def test_legacy_compatibility(monkeypatch):
    """下位互換性のテスト"""
    # 環境変数でAPIキーを設定
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    
    llm = LLMService()
    context = [ContextItem(title="レガシーテスト", text="下位互換性テスト", score=0.8)]

    class DummyResponse:
        class Choice:
            class Message:
                content = "下位互換性が保たれています。"
            message = Message()
        choices = [Choice()]
    
    def dummy_create(*args, **kwargs):
        return DummyResponse()
    
    # LLMサービスのクライアントを直接モック
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.chat.completions.create = dummy_create
    llm.client = mock_client

    # 旧メソッドの呼び出しをテスト
    answer = await llm.generate_answer_legacy("レガシーテスト", context)
    assert isinstance(answer, str)
    assert "下位互換性" in answer or "保たれています" in answer

@pytest.mark.asyncio
async def test_generate_greeting_response(monkeypatch):
    """挨拶応答生成のテスト"""
    # 環境変数でAPIキーを設定
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    
    llm = LLMService()
    
    # 挨拶の分類結果を作成
    from backend.app.models.classification_models import ClassificationResult, QueryType
    classification = ClassificationResult(
        query_type=QueryType.GREETING,
        summary="挨拶",
        confidence=0.9,
        filter_keywords=[],
        search_keywords=[],
        reasoning="挨拶検出"
    )
    
    # 各種挨拶パターンをテスト
    test_cases = [
        "こんにちは",
        "おはよう", 
        "ありがとう",
        "よろしく",
        "お疲れさま",
        "未知の挨拶パターン"
    ]
    
    for query in test_cases:
        answer = await llm.generate_answer(query, [], classification=classification)
        assert isinstance(answer, str)
        assert len(answer) > 0
        # 挨拶応答であることを確認（ポケモンカードに関する内容が含まれている）
        assert "ポケモンカード" in answer or "カード" in answer
        print(f"✅ クエリ「{query}」→ 応答「{answer}」")