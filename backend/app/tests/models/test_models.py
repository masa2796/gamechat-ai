"""
モデルクラスのテスト
"""
from app.models.rag_models import RagRequest, RagResponse, ContextItem
from app.models.classification_models import (
    ClassificationRequest,
    ClassificationResult,
    QueryType
)


class TestRagModels:
    """RAGモデルのテスト"""
    
    def test_rag_request_creation(self):
        """RagRequestの作成テスト"""
        request = RagRequest(question="テストクエリ")
        
        assert request.question == "テストクエリ"
        assert hasattr(request, 'question')
    
    def test_rag_request_validation(self):
        """RagRequestのバリデーションテスト"""
        # 空白文字列のテスト（バリデーションエラーが期待される）
        try:
            request = RagRequest(question="   ")
            assert False, "空白のみの文字列でバリデーションエラーが発生するはず"
        except ValueError:
            # 期待されるエラー
            pass
        
        # 有効な文字列でのテスト
        request = RagRequest(question="有効なクエリ")
        assert request.question == "有効なクエリ"
    
    def test_context_item_creation(self):
        """ContextItemの作成テスト"""
        item = ContextItem(
            title="テストタイトル",
            text="テストコンテンツ",
            score=0.85
        )
        
        assert item.title == "テストタイトル"
        assert item.text == "テストコンテンツ"
        assert item.score == 0.85
    
    def test_context_item_score_validation(self):
        """ContextItemのスコアバリデーションテスト"""
        # 正常な範囲のスコア
        item = ContextItem(title="テスト", text="テスト", score=0.5)
        assert item.score == 0.5
        
        # 境界値テスト
        item_min = ContextItem(title="テスト", text="テスト", score=0.0)
        assert item_min.score == 0.0
        
        item_max = ContextItem(title="テスト", text="テスト", score=1.0)
        assert item_max.score == 1.0
    
    def test_rag_response_creation(self):
        """RagResponseの作成テスト"""
        context_items = [
            ContextItem(title="カード1", text="内容1", score=0.9),
            ContextItem(title="カード2", text="内容2", score=0.8)
        ]
        
        response = RagResponse(
            answer="テスト回答",
            context=context_items
        )
        
        assert response.answer == "テスト回答"
        assert len(response.context) == 2
        assert response.context[0].title == "カード1"
        assert response.context[0].text == "内容1"
    
    def test_rag_response_empty_context(self):
        """空のコンテキストでのRagResponseテスト"""
        response = RagResponse(
            answer="コンテキストなしの回答",
            context=[]
        )
        
        assert response.answer == "コンテキストなしの回答"
        assert len(response.context) == 0


class TestClassificationModels:
    """分類モデルのテスト"""
    
    def test_classification_request_creation(self):
        """ClassificationRequestの作成テスト"""
        request = ClassificationRequest(query="炎タイプのカード")
        
        assert request.query == "炎タイプのカード"
        assert hasattr(request, 'query')
    
    def test_classification_result_creation(self):
        """ClassificationResultの作成テスト"""
        result = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            confidence=0.9,
            summary="フィルター検索クエリ",
            filter_keywords=["炎", "タイプ"],
            search_keywords=["強い", "カード"],
            reasoning="タイプ指定があるためフィルター検索が適切"
        )
        
        assert result.query_type == QueryType.FILTERABLE
        assert result.confidence == 0.9
        assert result.summary == "フィルター検索クエリ"
        assert result.filter_keywords == ["炎", "タイプ"]
        assert result.search_keywords == ["強い", "カード"]
        assert result.reasoning == "タイプ指定があるためフィルター検索が適切"
    
    def test_classification_result_optional_fields(self):
        """ClassificationResultのオプションフィールドテスト"""
        result = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            confidence=0.7,
            summary="意味検索クエリ"
        )
        
        assert result.query_type == QueryType.SEMANTIC
        assert result.confidence == 0.7
        assert result.summary == "意味検索クエリ"
        # オプションフィールドの確認
        assert hasattr(result, 'filter_keywords')
        assert hasattr(result, 'search_keywords')
        assert hasattr(result, 'reasoning')
    
    def test_query_type_enum(self):
        """QueryType列挙型のテスト"""
        # 各QueryTypeの値を確認
        assert QueryType.GREETING is not None
        assert QueryType.SEMANTIC is not None
        assert QueryType.FILTERABLE is not None
        
        # 文字列での比較テスト
        assert isinstance(QueryType.GREETING, QueryType)
        assert isinstance(QueryType.SEMANTIC, QueryType)
        assert isinstance(QueryType.FILTERABLE, QueryType)
    
    def test_classification_confidence_bounds(self):
        """分類の信頼度境界値テスト"""
        # 最小値
        result_min = ClassificationResult(
            query_type=QueryType.SEMANTIC,
            confidence=0.0,
            summary="最小信頼度"
        )
        assert result_min.confidence == 0.0
        
        # 最大値
        result_max = ClassificationResult(
            query_type=QueryType.GREETING,
            confidence=1.0,
            summary="最大信頼度"
        )
        assert result_max.confidence == 1.0
        
        # 中間値
        result_mid = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            confidence=0.5,
            summary="中間信頼度"
        )
        assert result_mid.confidence == 0.5


class TestModelIntegration:
    """モデル統合テスト"""
    
    def test_rag_workflow_models(self):
        """RAGワークフローでのモデル連携テスト"""
        # 分類結果
        classification_result = ClassificationResult(
            query_type=QueryType.FILTERABLE,
            confidence=0.85,
            summary="炎タイプのフィルター検索",
            filter_keywords=["炎", "タイプ"],
            search_keywords=["強い"]
        )
        
        # コンテキストアイテム
        context_items = [
            ContextItem(title="リザードン", text="強力な炎タイプ", score=0.95),
            ContextItem(title="ファイヤー", text="伝説の炎タイプ", score=0.90)
        ]
        
        # RAGレスポンス
        rag_response = RagResponse(
            answer="強い炎タイプのカードについて説明します。",
            context=context_items
        )
        
        # モデル間の一貫性を確認
        assert len(rag_response.context) == 2
        assert all(isinstance(item, ContextItem) for item in rag_response.context)
        assert rag_response.context[0].title == "リザードン"
        assert rag_response.context[1].title == "ファイヤー"
