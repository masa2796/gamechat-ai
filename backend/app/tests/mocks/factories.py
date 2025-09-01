"""
ファクトリーパターンでのテストデータ生成
"""
from typing import List, Optional
from app.models.rag_models import ContextItem
from app.models.classification_models import ClassificationResult, QueryType


class ContextItemFactory:
    """ContextItemのファクトリークラス"""
    
    @staticmethod
    def create_high_score_items(count: int = 3, base_score: float = 0.9) -> List[ContextItem]:
        """高スコアのContextItemリストを生成"""
        return [
            ContextItem(
                title=f"高品質データ{i+1}",
                text=f"非常に関連性の高い情報{i+1}です。詳細な内容を含んでいます。",
                score=base_score - (i * 0.02)
            )
            for i in range(count)
        ]
    
    @staticmethod
    def create_game_card_items(count: int = 5) -> List[ContextItem]:
        """ゲームカード関連のContextItemを生成"""
        card_data = [
            {"title": "ピカチュウ", "text": "電気タイプのマスコットカード。10まんボルトが得意技。", "score": 0.95},
            {"title": "リザードン", "text": "炎/飛行タイプの最終進化。強力なかえんほうしゃを使う。", "score": 0.92},
            {"title": "フシギダネ", "text": "草タイプのたねカード。はっぱカッターで攻撃する。", "score": 0.90},
            {"title": "カメックス", "text": "水タイプの最終進化。ハイドロポンプが必殺技。", "score": 0.89},
            {"title": "フシギバナ", "text": "草/毒タイプの最終進化。はなびらのまいで攻撃。", "score": 0.88},
            {"title": "ゼニガメ", "text": "水タイプのかめカード。みずでっぽうを使う。", "score": 0.86},
            {"title": "ヒトカゲ", "text": "炎タイプのとかげカード。ひのこで攻撃する。", "score": 0.85}
        ]
        
        return [
            ContextItem(
                title=data["title"],
                text=data["text"],
                score=data["score"]
            )
            for data in card_data[:count]
        ]
    
    @staticmethod
    def create_mixed_quality_items(high_count: int = 2, low_count: int = 2) -> List[ContextItem]:
        """高品質と低品質が混在するContextItemを生成"""
        high_items = [
            ContextItem(
                title=f"高品質{i+1}",
                text=f"非常に関連性の高い詳細情報{i+1}",
                score=0.9 - (i * 0.02)
            )
            for i in range(high_count)
        ]
        
        low_items = [
            ContextItem(
                title=f"低品質{i+1}",
                text=f"関連性の低い情報{i+1}",
                score=0.3 + (i * 0.05)
            )
            for i in range(low_count)
        ]
        
        return high_items + low_items
    
    @staticmethod
    def create_db_search_items(count: int = 3) -> List[ContextItem]:
        """データベース検索結果風のContextItemを生成"""
        return [
            ContextItem(
                title=f"DB結果{i+1}",
                text=f"データベースから取得した情報{i+1}。正確性が高い。",
                score=0.85 - (i * 0.05)
            )
            for i in range(count)
        ]
    
    @staticmethod
    def create_vector_search_items(count: int = 3) -> List[ContextItem]:
        """ベクトル検索結果風のContextItemを生成"""
        return [
            ContextItem(
                title=f"Vector結果{i+1}",
                text=f"ベクトル検索で見つかった関連情報{i+1}。意味的類似度が高い。",
                score=0.92 - (i * 0.07)
            )
            for i in range(count)
        ]
    
    @staticmethod
    def create_empty_items() -> List[ContextItem]:
        """空のContextItemリストを生成"""
        return []
    
    @staticmethod
    def create_single_item(title: str = "単一アイテム", text: str = "テスト用の単一アイテム", score: float = 0.8) -> List[ContextItem]:
        """単一のContextItemを含むリストを生成"""
        return [ContextItem(title=title, text=text, score=score)]


class ClassificationResultFactory:
    """ClassificationResultのファクトリークラス"""
    
    @staticmethod
    def create_semantic_result(
        confidence: float = 0.85,
        summary: str = "意味的検索",
        search_keywords: Optional[List[str]] = None
    ) -> ClassificationResult:
        """セマンティック検索の分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.SEMANTIC,
            summary=summary,
            confidence=confidence,
            search_keywords=search_keywords or ["強い", "カード"],
            filter_keywords=[],
            reasoning="意味的な内容に基づく検索クエリとして分類"
        )
    
    @staticmethod
    def create_filterable_result(
        confidence: float = 0.9,
        summary: str = "フィルター検索",
        filter_keywords: Optional[List[str]] = None
    ) -> ClassificationResult:
        """フィルター検索の分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.FILTERABLE,
            summary=summary,
            confidence=confidence,
            search_keywords=[],
            filter_keywords=filter_keywords or ["HP", "100以上"],
            reasoning="数値や属性による具体的な条件検索として分類"
        )
    
    @staticmethod
    def create_hybrid_result(
        confidence: float = 0.8,
        summary: str = "ハイブリッド検索",
        search_keywords: Optional[List[str]] = None,
        filter_keywords: Optional[List[str]] = None
    ) -> ClassificationResult:
        """ハイブリッド検索の分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.HYBRID,
            summary=summary,
            confidence=confidence,
            search_keywords=search_keywords or ["強い"],
            filter_keywords=filter_keywords or ["炎タイプ"],
            reasoning="意味的検索と条件フィルターの両方が必要な複合クエリとして分類"
        )
    
    @staticmethod
    def create_greeting_result(confidence: float = 0.95) -> ClassificationResult:
        """挨拶の分類結果を生成"""
        return ClassificationResult(
            query_type=QueryType.GREETING,
            summary="挨拶",
            confidence=confidence,
            search_keywords=[],
            filter_keywords=[],
            reasoning="挨拶や日常会話として分類"
        )
    
    @staticmethod
    def create_low_confidence_result(
        confidence: float = 0.3,
        query_type: QueryType = QueryType.SEMANTIC
    ) -> ClassificationResult:
        """低信頼度の分類結果を生成"""
        return ClassificationResult(
            query_type=query_type,
            summary="不明確な検索",
            confidence=confidence,
            search_keywords=["不明"],
            filter_keywords=[],
            reasoning=f"信頼度が低く、明確な分類が困難: {confidence}"
        )


class TestScenarioFactory:
    """複合的なテストシナリオのファクトリー"""
    
    @staticmethod
    def create_successful_game_card_search():
        """成功するゲームカード検索シナリオ"""
        return {
            "query": "強いカードを教えて",
            "classification": ClassificationResultFactory.create_semantic_result(),
            "context_items": ContextItemFactory.create_game_card_items(3),
            "expected_response_keywords": ["ピカチュウ", "リザードン", "強力"]
        }
    
    @staticmethod
    def create_filter_search_scenario():
        """フィルター検索シナリオ"""
        return {
            "query": "HPが100以上のカード",
            "classification": ClassificationResultFactory.create_filterable_result(),
            "context_items": ContextItemFactory.create_high_score_items(3),
            "expected_response_keywords": ["HP", "100以上", "高い"]
        }
    
    @staticmethod
    def create_hybrid_search_scenario():
        """ハイブリッド検索シナリオ"""
        return {
            "query": "炎タイプで攻撃力の高いカード",
            "classification": ClassificationResultFactory.create_hybrid_result(),
            "context": ContextItemFactory.create_high_score_items(4),  # 詳細JSON形式
            "expected_response_keywords": ["炎", "攻撃力", "高い"]
        }
    
    @staticmethod
    def create_greeting_scenario():
        """挨拶シナリオ"""
        return {
            "query": "こんにちは",
            "classification": ClassificationResultFactory.create_greeting_result(),
            "context_items": [],
            "expected_response": "こんにちは！ゲームカードについて何か知りたいことはありますか？"
        }
    
    @staticmethod
    def create_low_quality_scenario():
        """低品質結果シナリオ"""
        return {
            "query": "よくわからない質問",
            "classification": ClassificationResultFactory.create_low_confidence_result(),
            "context_items": ContextItemFactory.create_mixed_quality_items(1, 2),
            "expected_fallback": True
        }
