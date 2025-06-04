import pytest

@pytest.fixture(autouse=True)
def mock_openai(monkeypatch):
    class DummyResponse:
        class Choice:
            class Message:
                content = "ダミー応答"
            message = Message()
        choices = [Choice()]
    def dummy_create(*args, **kwargs):
        return DummyResponse()
    monkeypatch.setattr(
        "app.services.llm_service.openai.chat.completions.create",
        dummy_create
    )