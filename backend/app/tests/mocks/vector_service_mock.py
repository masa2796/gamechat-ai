"""
VectorService用のモッククラス
"""
from typing import List, Optional
from unittest.mock import MagicMock
from backend.app.models.rag_models import ContextItem
from backend.app.models.classification_models import ClassificationResult


class MockVectorService:
    """テスト用のVectorServiceモック"""
    
    def __init__(self) -> None:
        self._test_mode = True
        self.vector_index = MagicMock()  # テスト用のモックインデックス
        self.vector_index.name = "test_index"  # テスト用の名前を設定
        self._mock_results = []
        self._setup_default_results()
    
    def _setup_default_results(self) -> None:
        """デフォルトのモック結果を設定"""
        self._mock_results = [
            ContextItem(
                title="テスト用ポケモン1",
                text="これはテスト用のモックデータです。HP: 100, タイプ: 炎",
                score=0.9
            ),
            ContextItem(
                title="テスト用ポケモン2", 
                text="これもテスト用のモックデータです。HP: 80, タイプ: 水",
                score=0.8
            ),
            ContextItem(
                title="テスト用ポケモン3",
                text="さらにテスト用のモックデータです。HP: 120, タイプ: 草",
                score=0.7
            )
        ]
    
    def set_mock_results(self, results: List[ContextItem]) -> None:
        """テスト用の結果を設定"""
        self._mock_results = results
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 50,
        namespaces: Optional[List[str]] = None,
        classification: Optional[ClassificationResult] = None,
        min_score: Optional[float] = None
    ) -> List[ContextItem]:
        """モック検索結果を返す"""
        results = self._mock_results.copy()
        
        # min_scoreフィルタリング
        if min_score is not None:
            results = [r for r in results if r.score >= min_score]
        
        # top_kに制限
        return results[:min(top_k, len(results))]
