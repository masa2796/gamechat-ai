import pytest
from app.services.llm_service import LLMService
from app.models.rag_models import ContextItem

@pytest.mark.asyncio
async def test_generate_answer_with_context(monkeypatch):
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
    monkeypatch.setattr(
        "app.services.llm_service.openai.chat.completions.create",
        dummy_create
    )

    answer = await llm.generate_answer("テストとは？", context)
    assert isinstance(answer, str)
    assert "テスト" in answer or "情報がありません" in answer

@pytest.mark.asyncio
async def test_generate_answer_greeting(monkeypatch):
    llm = LLMService()

    class DummyResponse:
        class Choice:
            class Message:
                content = "こんにちは！ご質問があればどうぞ"
            message = Message()
        choices = [Choice()]
    def dummy_create(*args, **kwargs):
        return DummyResponse()
    monkeypatch.setattr(
        "app.services.llm_service.openai.chat.completions.create",
        dummy_create
    )

    answer = await llm.generate_answer("おはようございます", [])
    assert "こんにちは" in answer or "ご質問があればどうぞ" in answer