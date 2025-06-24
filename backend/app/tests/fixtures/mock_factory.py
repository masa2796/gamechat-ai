"""
テストデータのモックファクトリー
"""
from unittest.mock import MagicMock
from app.models.rag_models import ContextItem
from app.models.classification_models import ClassificationResult, QueryType


class TestDataFactory:
    """テストデータを生成するファクトリークラス"""
    
    @staticmethod
    def create_context_items(count: int = 3, base_score: float = 0.9) -> list[ContextItem]:
        """ContextItemのリストを生成"""
        return [
            ContextItem(
                title=f"テストアイテム{i+1}",
                text=f"これはテスト用のアイテム{i+1}です。",
                score=base_score - (i * 0.1)
            )
            for i in range(count)
        ]
    
    @staticmethod
    def create_game_card_context_items() -> list[ContextItem]:
        """ゲームカード関連のContextItemを生成"""
        return [
            ContextItem(title="ピカチュウ", text="電気タイプのマスコットカード", score=0.95),
            ContextItem(title="リザードン", text="炎/飛行タイプの最終進化", score=0.92),
            ContextItem(title="フシギダネ", text="草タイプのたねカード", score=0.90),
            ContextItem(title="カメックス", text="水タイプの最終進化", score=0.89),
            ContextItem(title="フシギバナ", text="草/毒タイプの最終進化", score=0.88)
        ]
    
    @staticmethod
    def create_high_quality_context_items() -> list[ContextItem]:
        """高品質なContextItemを生成"""
        return [
            ContextItem(title="高品質データ1", text="非常に関連性の高い情報", score=0.95),
            ContextItem(title="高品質データ2", text="優れた品質の情報", score=0.92),
            ContextItem(title="高品質データ3", text="価値の高い情報", score=0.90)
        ]

    @staticmethod
    def create_low_quality_context_items() -> list[ContextItem]:
        """低品質なContextItemを生成"""
        return [
            ContextItem(title="低品質データ1", text="関連性の低い情報", score=0.45),
            ContextItem(title="低品質データ2", text="あまり価値のない情報", score=0.42),
            ContextItem(title="低品質データ3", text="品質の劣る情報", score=0.40)
        ]

    @staticmethod
    def create_semantic_classification() -> ClassificationResult:
        """セマンティック分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="セマンティック検索",
            confidence=0.85,
            search_keywords=["検索", "クエリ"],
            filter_keywords=[],
            reasoning="意味的な検索クエリとして分類されました"
        )

    @staticmethod
    def create_filter_classification() -> ClassificationResult:
        """フィルター分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.FILTER,
            summary="フィルター検索",
            confidence=0.90,
            search_keywords=[],
            filter_keywords=["HP", "100以上", "炎タイプ"],
            reasoning="フィルター条件を含む検索クエリとして分類されました"
        )

    @staticmethod
    def create_greeting_classification() -> ClassificationResult:
        """挨拶分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.GREETING,
            summary="挨拶",
            confidence=0.95,
            search_keywords=[],
            filter_keywords=[],
            reasoning="挨拶として分類されました"
        )

    @staticmethod
    def create_vector_search_results() -> list[ContextItem]:
        """ベクトル検索結果を生成"""
        return [
            ContextItem(title="検索結果1", text="ベクトル検索による関連情報1", score=0.92),
            ContextItem(title="検索結果2", text="ベクトル検索による関連情報2", score=0.89),
            ContextItem(title="検索結果3", text="ベクトル検索による関連情報3", score=0.86)
        ]

    @staticmethod
    def create_db_search_results() -> list[ContextItem]:
        """データベース検索結果を生成"""
        return [
            ContextItem(title="DB検索結果1", text="データベース検索による関連情報1", score=0.88),
            ContextItem(title="DB検索結果2", text="データベース検索による関連情報2", score=0.85),
            ContextItem(title="DB検索結果3", text="データベース検索による関連情報3", score=0.82)
        ]

    @staticmethod
    def create_hybrid_classification() -> ClassificationResult:
        """ハイブリッド分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.HYBRID,
            summary="ハイブリッド検索",
            confidence=0.88,
            search_keywords=["強い", "カード"],
            filter_keywords=["炎タイプ", "HP100以上"],
            reasoning="セマンティック検索とフィルターを組み合わせた検索として分類されました"
        )

    @staticmethod
    def create_low_confidence_classification() -> ClassificationResult:
        """低信頼度分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary="不明確な検索",
            confidence=0.45,
            search_keywords=["不明", "検索"],
            filter_keywords=[],
            reasoning="信頼度が低いセマンティック検索として分類されました"
        )


class MockResponseFactory:
    """外部APIレスポンスのモック生成ファクトリー"""
    
    @staticmethod
    def create_openai_embedding_response(dimensions: int = 1536):
        """OpenAI埋め込みAPIレスポンスのモック"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * (dimensions // 3)
        return mock_response
    
    @staticmethod
    def create_openai_chat_response(content: str):
        """OpenAI ChatAPIレスポンスのモック"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = content
        return mock_response


class TestScenarioFactory:
    """テストシナリオ用のデータ生成ファクトリー"""
    
    @staticmethod
    def create_game_card_search_scenario():
        """ゲームカード検索のテストシナリオ"""
        return {
            "query": "強いカードを教えて",
            "classification": ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="強力なカードの検索",
                confidence=0.85,
                search_keywords=["強い", "カード"],
                filter_keywords=[],
                reasoning="戦闘力に関する意味的検索"
            ),
            "expected_results": [
                ContextItem(title="リザードン", text="炎/飛行タイプの強力なカード", score=0.95),
                ContextItem(title="カメックス", text="水タイプの頼もしいカード", score=0.90),
                ContextItem(title="フシギバナ", text="草/毒タイプの安定したカード", score=0.85)
            ]
        }
