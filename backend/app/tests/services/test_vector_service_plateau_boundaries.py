import pytest
from unittest.mock import patch
from copy import deepcopy
from app.services.vector_service import VectorService
from app.core.config import settings


@pytest.fixture(autouse=True)
def reset_singleton():
    VectorService._instance = None
    yield
    VectorService._instance = None


class Match:
    def __init__(self, score: float, title: str):
        self.score = score
        self.metadata = {"title": title}


def _make_res(scores):  # helper to build mock response
    return type('Res', (), {"matches": [Match(s, f"T{i}") for i, s in enumerate(scores)]})


@pytest.mark.asyncio
@patch.dict('os.environ', {
    'TEST_MODE':'false', 'ENVIRONMENT':'development',
    'UPSTASH_VECTOR_REST_URL':'https://dummy', 'UPSTASH_VECTOR_REST_TOKEN':'tok'
})
@patch('app.services.vector_service.Index')
async def test_plateau_boundary_stddev_no_trigger(mock_index):
    # stddev just ABOVE threshold -> no plateau
    # Configure thresholds so only stddev matters (spread threshold extremely small)
    cfg_backup = deepcopy(settings.VECTOR_SEARCH_CONFIG)
    try:
        settings.VECTOR_SEARCH_CONFIG['plateau']['stddev'] = 0.00013
        settings.VECTOR_SEARCH_CONFIG['plateau']['score_spread'] = 0.000001  # very tight so spread condition won't trigger
        # scores with stddev ~= 0.00041 (> 0.00013) spread bigger than spread_thr but we disabled spread pathway
        stage0_scores = [0.8000, 0.7994, 0.7990]

        def _query(vector, top_k, namespace, include_metadata, include_vectors):  # noqa: ANN001
            # Only stage0 needed because plateau should NOT trigger; return same for any ns
            return _make_res(stage0_scores)
        mock_index.return_value.query.side_effect = _query

        svc = VectorService()
        with patch.object(svc, '_get_all_namespaces', return_value=['effect_combined','effect_1']):
            await svc.search([0.0]*10, top_k=5, namespaces=None)
        params = svc.last_params
        assert params.get('plateau_triggered') is False
        used = params.get('used_namespaces', [])
        # combined should not appear because not plateau
        assert 'effect_combined' not in used
    finally:
        settings.VECTOR_SEARCH_CONFIG = cfg_backup


@pytest.mark.asyncio
@patch.dict('os.environ', {
    'TEST_MODE':'false', 'ENVIRONMENT':'development',
    'UPSTASH_VECTOR_REST_URL':'https://dummy', 'UPSTASH_VECTOR_REST_TOKEN':'tok'
})
@patch('app.services.vector_service.Index')
async def test_plateau_boundary_stddev_trigger(mock_index):
    # stddev just BELOW threshold -> plateau triggers
    cfg_backup = deepcopy(settings.VECTOR_SEARCH_CONFIG)
    try:
        settings.VECTOR_SEARCH_CONFIG['plateau']['stddev'] = 0.00013
        settings.VECTOR_SEARCH_CONFIG['plateau']['score_spread'] = 0.000001
        # scores with stddev ~=0.000124 (<0.00013)
        stage0_scores = [0.8000, 0.7998, 0.7997]

        call_count = {"n": 0}
        def _query(vector, top_k, namespace, include_metadata, include_vectors):  # noqa: ANN001
            call_count['n'] += 1
            if call_count['n'] == 1:  # stage0
                return _make_res(stage0_scores)
            # stage1 after plateau injection: return same set (irrelevant for decision)
            return _make_res(stage0_scores)
        mock_index.return_value.query.side_effect = _query

        svc = VectorService()
        with patch.object(svc, '_get_all_namespaces', return_value=['effect_combined','effect_1']):
            await svc.search([0.0]*10, top_k=5, namespaces=None)
        params = svc.last_params
        assert params.get('plateau_triggered') is True
        used = params.get('used_namespaces', [])
        assert used and used[0] == 'effect_combined'
        # ensure second query happened
        assert call_count['n'] >= 2
    finally:
        settings.VECTOR_SEARCH_CONFIG = cfg_backup


@pytest.mark.asyncio
@patch.dict('os.environ', {
    'TEST_MODE':'false', 'ENVIRONMENT':'development',
    'UPSTASH_VECTOR_REST_URL':'https://dummy', 'UPSTASH_VECTOR_REST_TOKEN':'tok'
})
@patch('app.services.vector_service.Index')
async def test_plateau_boundary_spread_no_trigger(mock_index):
    # spread just ABOVE threshold -> no plateau
    cfg_backup = deepcopy(settings.VECTOR_SEARCH_CONFIG)
    try:
        settings.VECTOR_SEARCH_CONFIG['plateau']['stddev'] = 0.00000001  # practically never triggers
        settings.VECTOR_SEARCH_CONFIG['plateau']['score_spread'] = 0.004
        # spread = 0.012 (> 0.004)
        stage0_scores = [0.8000, 0.7940, 0.7880]

        def _query(vector, top_k, namespace, include_metadata, include_vectors):  # noqa: ANN001
            return _make_res(stage0_scores)
        mock_index.return_value.query.side_effect = _query

        svc = VectorService()
        with patch.object(svc, '_get_all_namespaces', return_value=['effect_combined','effect_1']):
            await svc.search([0.0]*10, top_k=5, namespaces=None)
        params = svc.last_params
        assert params.get('plateau_triggered') is False
    finally:
        settings.VECTOR_SEARCH_CONFIG = cfg_backup


@pytest.mark.asyncio
@patch.dict('os.environ', {
    'TEST_MODE':'false', 'ENVIRONMENT':'development',
    'UPSTASH_VECTOR_REST_URL':'https://dummy', 'UPSTASH_VECTOR_REST_TOKEN':'tok'
})
@patch('app.services.vector_service.Index')
async def test_plateau_boundary_spread_trigger(mock_index):
    # spread just BELOW (equal) threshold -> plateau triggers
    cfg_backup = deepcopy(settings.VECTOR_SEARCH_CONFIG)
    try:
        settings.VECTOR_SEARCH_CONFIG['plateau']['stddev'] = 1e-8  # effectively disable stddev path
        # Spread threshold: slightly above actual spread (0.0040000000000000036) to guarantee <= 判定
        settings.VECTOR_SEARCH_CONFIG['plateau']['score_spread'] = 0.00405
        # spread 実値 ≈0.0040000000000000036 < 0.00405 → 発火期待
        stage0_scores = [0.8000, 0.7980, 0.7960]
        call_count = {"n": 0}

        def _query(vector, top_k, namespace, include_metadata, include_vectors):  # noqa: ANN001
            call_count['n'] += 1
            return _make_res(stage0_scores)

        mock_index.return_value.query.side_effect = _query

        svc = VectorService()
        with patch.object(svc, '_get_all_namespaces', return_value=['effect_combined','effect_1']):
            await svc.search([0.0]*10, top_k=5, namespaces=None)
        params = svc.last_params
        assert params.get('plateau_triggered') is True
        assert call_count['n'] >= 2  # stage0 + stage1
    finally:
        settings.VECTOR_SEARCH_CONFIG = cfg_backup
