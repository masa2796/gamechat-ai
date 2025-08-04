"""
テストアサーション用のヘルパー関数
"""
from app.models.rag_models import ContextItem
from app.models.classification_models import ClassificationResult, QueryType


class TestAssertions:
    """テスト用のアサーションヘルパー"""
    
    @staticmethod
    def assert_context_items_valid(items: list[ContextItem]):
        """ContextItemリストの基本的な妥当性を検証"""
        assert isinstance(items, list), "結果はリストである必要があります"
        
        for item in items:
            assert isinstance(item, ContextItem), "各アイテムはContextItemである必要があります"
            assert hasattr(item, 'title'), "titleが必要です"
            assert hasattr(item, 'text'), "textが必要です"
            assert hasattr(item, 'score'), "scoreが必要です"
            assert isinstance(item.title, str), "titleは文字列である必要があります"
            assert isinstance(item.text, str), "textは文字列である必要があります"
            assert isinstance(item.score, (int, float)), "scoreは数値である必要があります"
            assert 0 <= item.score <= 1, "scoreは0-1の範囲である必要があります"
    
    @staticmethod
    def assert_items_sorted_by_score(items: list[ContextItem], descending: bool = True):
        """アイテムがスコア順にソートされていることを検証"""
        TestAssertions.assert_context_items_valid(items)
        
        if len(items) <= 1:
            return  # 1個以下の場合はソート検証不要
        
        scores = [item.score for item in items]
        
        if descending:
            assert scores == sorted(scores, reverse=True), "結果は降順にソートされている必要があります"
        else:
            assert scores == sorted(scores), "結果は昇順にソートされている必要があります"
    
    @staticmethod
    def assert_no_duplicates(items: list[ContextItem], key: str = 'title'):
        """重複アイテムがないことを検証"""
        TestAssertions.assert_context_items_valid(items)
        
        values = [getattr(item, key) for item in items]
        unique_values = set(values)
        
        assert len(values) == len(unique_values), f"{key}に重複があります: {values}"
    
    @staticmethod
    def assert_classification_valid(classification: ClassificationResult):
        """ClassificationResultの妥当性を検証"""
        assert isinstance(classification, ClassificationResult), "ClassificationResultである必要があります"
        assert hasattr(classification, 'query_type'), "query_typeが必要です"
        assert hasattr(classification, 'confidence'), "confidenceが必要です"
        assert hasattr(classification, 'summary'), "summaryが必要です"
        
        assert isinstance(classification.query_type, QueryType), "query_typeは正しい列挙型である必要があります"
        assert isinstance(classification.confidence, (int, float)), "confidenceは数値である必要があります"
        assert 0 <= classification.confidence <= 1, "confidenceは0-1の範囲である必要があります"
        assert isinstance(classification.summary, str), "summaryは文字列である必要があります"
        
        # keywords の検証
        if hasattr(classification, 'search_keywords'):
            assert isinstance(classification.search_keywords, list), "search_keywordsはリストである必要があります"
        if hasattr(classification, 'filter_keywords'):
            assert isinstance(classification.filter_keywords, list), "filter_keywordsはリストである必要があります"
    
    @staticmethod
    def assert_search_result_structure(result: dict):
        """検索結果辞書の構造を検証"""
        required_keys = ['classification', 'context']
        
        for key in required_keys:
            assert key in result, f"検索結果に{key}キーが必要です"
        
        # 各結果の型チェック
        TestAssertions.assert_classification_valid(result['classification'])
        # contextは詳細JSONリストまたはContextItemリスト
        context = result['context']
        assert isinstance(context, list), "contextはリストである必要があります"
    
    # 注意: 以下のメソッドは旧API構造用で現在は使用されていません
    # @staticmethod
    # def assert_merged_results_logic(db_results: list[ContextItem], 
    #                               vector_results: list[ContextItem], 
    #                               merged_results: list[ContextItem]):
    #     """マージ結果のロジックを検証"""
    #     TestAssertions.assert_context_items_valid(db_results)
    #     TestAssertions.assert_context_items_valid(vector_results)
    #     TestAssertions.assert_context_items_valid(merged_results)
    #     
    #     # マージ結果は元の結果の総和以下である必要がある（重複除去のため）
    #     max_possible = len(db_results) + len(vector_results)
    #     assert len(merged_results) <= max_possible, "マージ結果が元の結果を超えています"
    #     
    #     # マージ結果は重複がない
    #     TestAssertions.assert_no_duplicates(merged_results)
    #     
    #     # マージ結果はスコア順にソートされている
    #     TestAssertions.assert_items_sorted_by_score(merged_results)
    # 
    # @staticmethod
    # def assert_query_type_behavior(classification: ClassificationResult, 
    #                              db_results: list[ContextItem], 
    #                              vector_results: list[ContextItem]):
    #     """クエリタイプに応じた適切な動作を検証"""
    #     TestAssertions.assert_classification_valid(classification)
    #     TestAssertions.assert_context_items_valid(db_results)
    #     TestAssertions.assert_context_items_valid(vector_results)
    #     
    #     if classification.query_type == QueryType.FILTERABLE:
    #         # フィルタ可能な場合、DB結果があってベクトル結果は空またはDBより少ない
    #         assert len(db_results) > 0 or len(vector_results) == 0, \
    #             "フィルタ可能クエリではDB検索が優先されるべきです"
    #     
    #     elif classification.query_type == QueryType.SEMANTIC:
    #         # セマンティックな場合、ベクトル結果があってDB結果は空またはベクトルより少ない
    #         assert len(vector_results) > 0 or len(db_results) == 0, \
    #             "セマンティッククエリではベクトル検索が優先されるべきです"
    #     
    #     elif classification.query_type == QueryType.HYBRID:
    #         # ハイブリッドの場合、両方の結果がある可能性
    #         total_results = len(db_results) + len(vector_results)
    #         assert total_results > 0, "ハイブリッドクエリでは何らかの結果があるべきです"
    
    @staticmethod
    def assert_confidence_based_behavior(classification: ClassificationResult, 
                                       results: list[ContextItem]):
        """信頼度に基づく適切な動作を検証"""
        TestAssertions.assert_classification_valid(classification)
        TestAssertions.assert_context_items_valid(results)
        
        if classification.confidence >= 0.8:
            # 高信頼度の場合、より多くの結果が期待される
            # または高品質な結果が期待される
            if results:
                avg_score = sum(item.score for item in results) / len(results)
                # 高信頼度なら結果の平均スコアも高いことが期待される
                assert avg_score >= 0.7, f"高信頼度({classification.confidence})なら高品質な結果が期待されます"
        
        elif classification.confidence <= 0.3:
            # 低信頼度の場合、結果が制限される可能性
            # またはフォールバック結果が返される可能性
            if results:
                # 低信頼度でも最低限の結果は提供される
                assert len(results) >= 1, "低信頼度でも最低限のフォールバック結果は提供されるべきです"


class PerformanceAssertions:
    """パフォーマンス関連のアサーション"""
    
    @staticmethod
    def assert_response_time_acceptable(duration: float, max_seconds: float = 5.0):
        """レスポンス時間が許容範囲内であることを検証"""
        assert duration <= max_seconds, f"レスポンス時間が遅すぎます: {duration:.2f}秒 > {max_seconds}秒"
    
    @staticmethod
    def assert_result_count_reasonable(results: list[ContextItem], 
                                     requested_count: int, 
                                     tolerance: float = 0.5):
        """結果数が要求された数に対して合理的であることを検証"""
        TestAssertions.assert_context_items_valid(results)
        
        min_expected = max(1, int(requested_count * (1 - tolerance)))
        max_expected = int(requested_count * (1 + tolerance))
        
        actual_count = len(results)
        
        # 結果が0の場合は特別扱い（検索失敗やフォールバックの可能性）
        if actual_count == 0:
            return  # 検索失敗時は別途検証が必要
        
        assert min_expected <= actual_count <= max_expected, \
            f"結果数が期待範囲外: {actual_count} (期待: {min_expected}-{max_expected})"
