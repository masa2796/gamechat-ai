"""
サービス用のモッククラス定義
"""
from typing import List
from unittest.mock import MagicMock
from backend.app.models.classification_models import ClassificationResult, QueryType


class MockMatch:
    """Upstash検索結果のmatchオブジェクトのモック"""
    
    def __init__(self, score: float, title: str, text: str, id: str = None):
        self.score = score
        self.metadata = {"title": title, "text": text}
        self.id = id or f"id-{hash(title)}"


class MockUpstashResult:
    """Upstash検索結果全体のモック"""
    
    def __init__(self, matches: List[MockMatch]):
        self.matches = matches
    
    @classmethod
    def create_pokemon_results(cls, count: int = 3):
        """ポケモン関連の検索結果を生成"""
        pokemon_data = [
            {"title": "ピカチュウ", "text": "電気タイプのマスコットポケモン", "score": 0.95},
            {"title": "リザードン", "text": "炎/飛行タイプの最終進化", "score": 0.92},
            {"title": "フシギダネ", "text": "草タイプのたねポケモン", "score": 0.90},
            {"title": "カメックス", "text": "水タイプの最終進化", "score": 0.89},
            {"title": "フシギバナ", "text": "草/毒タイプの最終進化", "score": 0.88}
        ]
        
        matches = [
            MockMatch(
                score=data["score"],
                title=data["title"],
                text=data["text"]
            )
            for data in pokemon_data[:count]
        ]
        return cls(matches)
    
    @classmethod
    def create_high_score_results(cls, count: int = 3, base_score: float = 0.9):
        """高スコア検索結果を生成"""
        matches = [
            MockMatch(
                score=base_score - (i * 0.05),
                title=f"高品質データ{i+1}",
                text=f"非常に関連性の高い情報{i+1}"
            )
            for i in range(count)
        ]
        return cls(matches)
    
    @classmethod
    def create_empty_result(cls):
        """空の検索結果を生成"""
        return cls([])


class MockClassificationResult:
    """分類結果のモッククラス"""
    
    @classmethod
    def create_semantic(cls, confidence: float = 0.8, summary: str = None) -> ClassificationResult:
        """セマンティック分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary=summary or "意味的検索クエリ",
            confidence=confidence,
            search_keywords=["強い", "ポケモン"],
            filter_keywords=[],
            reasoning="意味的な検索として分類"
        )
    
    @classmethod
    def create_filterable(cls, confidence: float = 0.9, summary: str = None) -> ClassificationResult:
        """フィルター可能分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary=summary or "フィルター検索クエリ",
            confidence=confidence,
            search_keywords=[],
            filter_keywords=["HP", "100以上"],
            reasoning="数値条件による具体的フィルター"
        )
    
    @classmethod
    def create_hybrid(cls, confidence: float = 0.85, summary: str = None) -> ClassificationResult:
        """ハイブリッド分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.HYBRID,
            summary=summary or "ハイブリッド検索クエリ",
            confidence=confidence,
            search_keywords=["強い"],
            filter_keywords=["炎タイプ"],
            reasoning="タイプ条件と性能条件の複合"
        )
    
    @classmethod
    def create_greeting(cls, confidence: float = 0.95) -> ClassificationResult:
        """挨拶分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.GREETING,
            summary="挨拶",
            confidence=confidence,
            search_keywords=[],
            filter_keywords=[],
            reasoning="挨拶として検出"
        )
    
    @classmethod
    def create_low_confidence(cls, confidence: float = 0.3) -> ClassificationResult:
        """低信頼度分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="不明な検索",
            confidence=confidence,
            search_keywords=["不明"],
            filter_keywords=[],
            reasoning="分類できない低信頼度"
        )


class MockOpenAIResponse:
    """OpenAI APIレスポンスのモッククラス"""
    
    @classmethod
    def create_chat_response(cls, content: str):
        """チャットレスポンスのモック"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = content
        return mock_response
    
    @classmethod
    def create_embedding_response(cls, dimensions: int = 1536):
        """埋め込みレスポンスのモック"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * (dimensions // 3)
        return mock_response
    
    @classmethod
    def create_classification_response(
        cls,
        query_type: str = "semantic",
        summary: str = "テスト分類結果",
        confidence: float = 0.8,
        search_keywords: List[str] = None,
        filter_keywords: List[str] = None
    ):
        """分類レスポンスのモック"""
        import json
        content = {
            "query_type": query_type,
            "summary": summary,
            "confidence": confidence,
            "search_keywords": search_keywords if search_keywords is not None else ["テスト"],
            "filter_keywords": filter_keywords if filter_keywords is not None else [],
            "reasoning": f"{query_type}として分類"
        }
        return cls.create_chat_response(json.dumps(content))


class MockDatabaseConnection:
    """データベース接続のモッククラス"""
    
    @classmethod
    def create_successful_connection(cls):
        """成功するDB接続のモック"""
        mock_connection = MagicMock()
        mock_connection.execute.return_value = MagicMock()
        mock_connection.fetchall.return_value = [
            {"title": "DBポケモン1", "text": "データベースから取得1", "score": 0.9},
            {"title": "DBポケモン2", "text": "データベースから取得2", "score": 0.8}
        ]
        return mock_connection
    
    @classmethod
    def create_failed_connection(cls):
        """失敗するDB接続のモック"""
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = Exception("Database connection failed")
        return mock_connection
    
    @classmethod
    def create_empty_result_connection(cls):
        """空の結果を返すDB接続のモック"""
        mock_connection = MagicMock()
        mock_connection.execute.return_value = MagicMock()
        mock_connection.fetchall.return_value = []
        return mock_connection
