import pytest
from unittest.mock import patch
from app.services.vector_service import VectorService


@pytest.fixture(autouse=True)
def reset_singleton():
    VectorService._instance = None
    yield
    VectorService._instance = None


def test_calc_top3_stats_empty():
    assert VectorService.calc_top3_stats({}) is None


def test_calc_top3_stats_single():
    res = VectorService.calc_top3_stats({'A':0.7})
    assert res == {'values':[0.7], 'stddev':0.0, 'spread':0.0}


def test_calc_top3_stats_boundary():
    # values: 0.700,0.702,0.703 -> spread=0.003 stddev small
    res = VectorService.calc_top3_stats({'A':0.703,'B':0.702,'C':0.700,'D':0.650})
    assert set(res.keys()) == {'values','stddev','spread'}
    assert res['values'][0] >= res['values'][-1]
    assert res['spread'] == pytest.approx(0.003, rel=1e-3)


def test_calc_top3_stats_non_plateau():
    # clearly wide spread
    res = VectorService.calc_top3_stats({'A':0.90,'B':0.80,'C':0.60})
    assert res['spread'] == pytest.approx(0.30, rel=1e-3)


@pytest.mark.asyncio
@patch.dict('os.environ', {
    'TEST_MODE':'false', 'ENVIRONMENT':'development',
    'UPSTASH_VECTOR_REST_URL':'https://dummy', 'UPSTASH_VECTOR_REST_TOKEN':'tok'
})
@patch('app.services.vector_service.Index')
async def test_plateau_injection(mock_index):
    # Mock vector index query behavior: first pass returns narrow top3 -> triggers plateau
    class Match:
        def __init__(self, score, title):
            self.score = score
            self.metadata = {'title': title}

    # Stage0 (no combined in list) will query effect_1/effect_2 etc. We'll simulate two namespaces.
    stage0_calls = []
    def _query(vector, top_k, namespace, include_metadata, include_vectors):  # noqa: ANN001
        stage0_calls.append(namespace)
        # Return narrow distribution
        return type('Res', (), {'matches':[Match(0.701,'T1'), Match(0.700,'T2'), Match(0.699,'T3')]})
    mock_index.return_value.query.side_effect = _query

    svc = VectorService()
    # Force namespaces: include combined so logic can inject it; _get_all_namespaces mocked
    with patch.object(svc, '_get_all_namespaces', return_value=['effect_combined','effect_1','effect_2']):
        res = await svc.search([0.0]*10, top_k=5, namespaces=None)
    # After search, plateau should have triggered (narrow scores)
    params = svc.last_params
    assert params.get('plateau_triggered') is True
    assert 'effect_combined' in params.get('used_namespaces', [])
    assert isinstance(res, list)
    assert len(res) <= 5

@pytest.mark.asyncio
@patch.dict('os.environ', {
    'TEST_MODE':'false', 'ENVIRONMENT':'development',
    'UPSTASH_VECTOR_REST_URL':'https://dummy', 'UPSTASH_VECTOR_REST_TOKEN':'tok'
})
@patch('app.services.vector_service.Index')
async def test_no_plateau_when_diverse(mock_index):
    class Match:
        def __init__(self, score, title):
            self.score = score
            self.metadata = {'title': title}

    def _query(vector, top_k, namespace, include_metadata, include_vectors):  # noqa: ANN001
        # Return wide spread
        return type('Res', (), {'matches':[Match(0.90,'A'), Match(0.75,'B'), Match(0.50,'C')]})
    mock_index.return_value.query.side_effect = _query
    svc = VectorService()
    with patch.object(svc, '_get_all_namespaces', return_value=['effect_combined','effect_1']):
        res = await svc.search([0.0]*10, top_k=5, namespaces=None)
    params = svc.last_params
    assert params.get('plateau_triggered') is False
    # combined should NOT have been used because not plateau and we exclude at stage0
    used = params.get('used_namespaces', [])
    assert used and used[0] != 'effect_combined'
    assert isinstance(res, list)
