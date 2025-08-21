import pytest
from unittest.mock import patch
from app.services.database_service import DatabaseService

@pytest.fixture
def database_service():
    with patch('app.services.database_service.os.path.exists') as mock_exists, \
         patch.object(DatabaseService, 'reload_data') as mock_reload:
        mock_exists.return_value = True
        mock_reload.return_value = None
        service = DatabaseService()
        # テストデータ: effect_5 のみに効果語を持つカード
        service.data_cache = [
            {"name": "カードA", "effect_1": None, "effect_2": None, "effect_3": None, "effect_4": None, "effect_5": "相手リーダーに3ダメージ"},
            {"name": "カードB", "effect_1": "ドローする", "effect_2": None, "effect_3": None, "effect_4": None, "effect_5": None},
        ]
        return service

@pytest.mark.asyncio
async def test_match_filterable_llm_effect_extended(database_service, monkeypatch):
    """effect_5 のみの効果でも検索条件(effect)がマッチすることを確認"""
    # query_analysis をモック
    query_analysis = {
        "conditions": {"effect": "リーダー 3ダメージ"}
    }
    # AND 条件: "リーダー" と "3ダメージ" の両方が effect_5 に含まれるカードA がマッチする
    a = await database_service._match_filterable_llm(database_service.data_cache[0], query_analysis)
    b = await database_service._match_filterable_llm(database_service.data_cache[1], query_analysis)
    assert a is True
    assert b is False
