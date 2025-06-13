import pytest
from backend.app.services.vector_service import VectorService
from backend.app.models.rag_models import ContextItem

@pytest.mark.asyncio
async def test_search_returns_context(monkeypatch):
    class DummyMatch:
        def __init__(self):
            self.score = 0.9
            self.metadata = {"title": "テストタイトル", "text": "テストテキスト"}
            self.id = "dummy-id"
    class DummyResult:
        matches = [DummyMatch()]
    def dummy_query(*args, **kwargs):
        return DummyResult()
    vs = VectorService()
    vs.vector_index.query = dummy_query

    result = await vs.search([0.1]*1536, top_k=1)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], ContextItem)
    assert result[0].title == "テストタイトル"