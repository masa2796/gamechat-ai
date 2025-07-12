"""
VectorService用のモッククラス
"""
from typing import Optional
from unittest.mock import MagicMock
from app.models.rag_models import ContextItem
from app.models.classification_models import ClassificationResult


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
                title="テスト用カード1",
                text="これはテスト用のモックデータです。HP: 100, タイプ: 炎",
                score=0.9
            ),
            ContextItem(
                title="テスト用カード2", 
                text="これもテスト用のモックデータです。HP: 80, タイプ: 水",
                score=0.8
            ),
            ContextItem(
                title="テスト用カード3",
                text="さらにテスト用のモックデータです。HP: 120, タイプ: 草",
                score=0.7
            )
        ]
    
    def set_mock_results(self, results: list[str]) -> None:
        """テスト用のカード名リストを設定"""
        self._mock_results = results
    
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 50,
        namespaces: Optional[list[str]] = None,
        classification: Optional[ClassificationResult] = None,
        min_score: Optional[float] = None
    ) -> list[str]:
        """モック検索結果（カード名リスト）を返す"""
        results = self._mock_results.copy()
        return results[:min(top_k, len(results))]
