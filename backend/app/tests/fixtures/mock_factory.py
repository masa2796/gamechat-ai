"""
テストデータのモックファクトリー
"""
from unittest.mock import MagicMock
from backend.app.models.rag_models import ContextItem
from backend.app.models.classification_models import ClassificationResult, QueryType


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
    def create_pokemon_context_items() -> list[ContextItem]:
        """ポケモン関連のContextItemを生成"""
        return [
            ContextItem(title="ピカチュウ", text="電気タイプのマスコットポケモン", score=0.95),
            ContextItem(title="リザードン", text="炎/飛行タイプの最終進化", score=0.92),
            ContextItem(title="フシギダネ", text="草タイプのたねポケモン", score=0.90),
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
            ContextItem(title="関連性低1", text="あまり関連のない情報", score=0.35),
            ContextItem(title="関連性低2", text="別の関連のない情報", score=0.28),
            ContextItem(title="関連性低3", text="ほぼ無関係な情報", score=0.20)
        ]
    
    @staticmethod
    def create_db_search_results() -> list[ContextItem]:
        """データベース検索結果を生成"""
        return [
            ContextItem(title="DB結果1", text="データベースからの結果", score=0.9),
            ContextItem(title="DB結果2", text="データベースからの結果2", score=0.8),
            ContextItem(title="DB結果3", text="データベースからの結果3", score=0.7)
        ]
    
    @staticmethod
    def create_vector_search_results() -> list[ContextItem]:
        """ベクトル検索結果を生成"""
        return [
            ContextItem(title="Vector結果1", text="ベクトル検索の結果", score=0.95),
            ContextItem(title="Vector結果2", text="ベクトル検索の結果2", score=0.85),
            ContextItem(title="Vector結果3", text="ベクトル検索の結果3", score=0.75)
        ]
    
    @staticmethod
    def create_classification_result(
        query_type: QueryType = QueryType.SEMANTIC,
        confidence: float = 0.8,
        summary: str = "テスト分類結果",
        search_keywords: list[str] = None,
        filter_keywords: list[str] = None
    ) -> ClassificationResult:
        """ClassificationResultを生成"""
        return ClassificationResult(
            query_type=query_type,
            summary=summary,
            confidence=confidence,
            search_keywords=search_keywords or [],
            filter_keywords=filter_keywords or [],
            reasoning=f"{query_type.value}として分類"
        )
    
    @staticmethod
    def create_semantic_classification() -> ClassificationResult:
        """セマンティック分類結果を生成"""
        return TestDataFactory.create_classification_result(
            query_type=QueryType.SEMANTIC,
            confidence=0.85,
            summary="強いポケモンの検索",
            search_keywords=["強い", "ポケモン"]
        )
    
    @staticmethod
    def create_filterable_classification() -> ClassificationResult:
        """フィルタ可能分類結果を生成"""
        return TestDataFactory.create_classification_result(
            query_type=QueryType.FILTERABLE,
            confidence=0.90,
            summary="HP100以上のポケモン",
            filter_keywords=["HP", "100"]
        )
    
    @staticmethod
    def create_hybrid_classification() -> ClassificationResult:
        """ハイブリッド分類結果を生成"""
        return TestDataFactory.create_classification_result(
            query_type=QueryType.HYBRID,
            confidence=0.85,
            summary="炎タイプで強いポケモン",
            search_keywords=["強い"],
            filter_keywords=["炎"]
        )
    
    @staticmethod
    def create_low_confidence_classification() -> ClassificationResult:
        """低信頼度分類結果を生成"""
        return TestDataFactory.create_classification_result(
            query_type=QueryType.SEMANTIC,
            confidence=0.3,
            summary="不明な検索",
            search_keywords=["不明"]
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
    
    @staticmethod
    def create_openai_classification_response(
        query_type: str = "semantic",
        summary: str = "テスト分類結果",
        confidence: float = 0.8,
        search_keywords: list = None,
        filter_keywords: list = None
    ):
        """OpenAI分類レスポンスのモック"""
        content = {
            "query_type": query_type,
            "summary": summary,
            "confidence": confidence,
            "search_keywords": search_keywords or ["テスト"],
            "filter_keywords": filter_keywords or [],
            "reasoning": f"{query_type}として分類"
        }
        import json
        return MockResponseFactory.create_openai_chat_response(json.dumps(content))
    
    @staticmethod
    def create_upstash_search_response(results: list = None):
        """Upstash検索レスポンスのモック"""
        if results is None:
            results = [
                {"score": 0.95, "title": "テスト1", "text": "テスト内容1"},
                {"score": 0.85, "title": "テスト2", "text": "テスト内容2"},
                {"score": 0.75, "title": "テスト3", "text": "テスト内容3"}
            ]
        
        matches = []
        for i, result in enumerate(results):
            match = MagicMock()
            match.score = result["score"]
            match.metadata = {"title": result["title"], "text": result["text"]}
            match.id = f"id-{i}"
            matches.append(match)
        
        response = MagicMock()
        response.matches = matches
        return response


class TestScenarioFactory:
    """テストシナリオ用のデータ生成ファクトリー"""
    
    @staticmethod
    def create_pokemon_search_scenario():
        """ポケモン検索のテストシナリオ"""
        return {
            "query": "強いポケモンを教えて",
            "classification": ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="強力なポケモンの検索",
                confidence=0.85,
                search_keywords=["強い", "ポケモン"],
                filter_keywords=[],
                reasoning="戦闘力に関する意味的検索"
            ),
            "expected_results": [
                ContextItem(title="リザードン", text="炎/飛行タイプの強力なポケモン", score=0.95),
                ContextItem(title="カメックス", text="水タイプの頼もしいポケモン", score=0.90),
                ContextItem(title="フシギバナ", text="草/毒タイプの安定したポケモン", score=0.85)
            ]
        }
    
    @staticmethod
    def create_filter_search_scenario():
        """フィルター検索のテストシナリオ"""
        return {
            "query": "HPが100以上のポケモン",
            "classification": ClassificationResult(
                query_type=QueryType.FILTERABLE,
                summary="HP数値条件でのポケモン検索",
                confidence=0.90,
                search_keywords=[],
                filter_keywords=["HP", "100以上"],
                reasoning="数値条件による具体的フィルター"
            ),
            "expected_results": [
                ContextItem(title="ケッキング", text="HP150の超高HPポケモン", score=1.0),
                ContextItem(title="ハピナス", text="HP255の圧倒的なHPを持つ", score=1.0),
                ContextItem(title="ソーナンス", text="HP190の高耐久ポケモン", score=0.95)
            ]
        }
    
    @staticmethod
    def create_hybrid_search_scenario():
        """ハイブリッド検索のテストシナリオ"""
        return {
            "query": "炎タイプで攻撃力が高いポケモン",
            "classification": ClassificationResult(
                query_type=QueryType.HYBRID,
                summary="炎タイプで攻撃的なポケモン",
                confidence=0.80,
                search_keywords=["攻撃力", "高い"],
                filter_keywords=["炎タイプ"],
                reasoning="タイプ条件と性能条件の複合"
            ),
            "expected_db_results": [
                ContextItem(title="リザードン", text="炎/飛行タイプ", score=0.85),
                ContextItem(title="ブースター", text="炎タイプの進化ポケモン", score=0.80)
            ],
            "expected_vector_results": [
                ContextItem(title="エンテイ", text="攻撃力の高い伝説の炎ポケモン", score=0.92),
                ContextItem(title="ファイヤー", text="強力な攻撃技を持つ", score=0.88)
            ]
        }
    
    @staticmethod
    def create_error_scenario():
        """エラーハンドリングのテストシナリオ"""
        return {
            "query": "検索できない内容",
            "classification": ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="不明な検索",
                confidence=0.20,
                search_keywords=["不明"],
                filter_keywords=[],
                reasoning="分類できない低信頼度"
            ),
            "expected_error": "低信頼度による検索失敗",
            "expected_fallback": [
                ContextItem(
                    title="検索のご提案", 
                    text="より具体的なポケモン名や条件を教えてください。", 
                    score=0.1
                )
            ]
        }


class DatabaseMockFactory:
    """データベース関連のモック生成ファクトリー"""
    
    @staticmethod
    def create_successful_db_connection():
        """成功するDB接続のモック"""
        mock_connection = MagicMock()
        mock_connection.execute.return_value = MagicMock()
        mock_connection.fetchall.return_value = [
            {"title": "DBポケモン1", "text": "データベースから取得1", "score": 0.9},
            {"title": "DBポケモン2", "text": "データベースから取得2", "score": 0.8}
        ]
        return mock_connection
    
    @staticmethod
    def create_failed_db_connection():
        """失敗するDB接続のモック"""
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = Exception("Database connection failed")
        return mock_connection


# よく使用される組み合わせフィクスチャ
COMMON_TEST_COMBINATIONS = {
    "high_quality_semantic": {
        "classification": TestScenarioFactory.create_pokemon_search_scenario()["classification"],
        "context_items": TestScenarioFactory.create_pokemon_search_scenario()["expected_results"]
    },
    "high_quality_filterable": {
        "classification": TestScenarioFactory.create_filter_search_scenario()["classification"],
        "context_items": TestScenarioFactory.create_filter_search_scenario()["expected_results"]
    },
    "low_quality_results": {
        "classification": TestScenarioFactory.create_error_scenario()["classification"],
        "context_items": TestScenarioFactory.create_error_scenario()["expected_fallback"]
    }
}
