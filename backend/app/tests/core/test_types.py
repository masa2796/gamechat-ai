"""
型エイリアス定義のテスト
"""
from app.core.types import (
    JsonDict,
    StringList,
    OptionalString,
    OptionalFloat,
    OptionalInt,
    SearchResult,
    SearchParams,
    FilterKeywords,
    SearchKeywords,
    ScoreFloat,
    ScoreTuple,
    ScoreDict,
    ConfigDict,
    LimitsDict,
    ThresholdDict,
    EmbeddingVector,
    VectorSearchResult,
    DatabaseItem,
    DatabaseResults,
    ClassificationData,
    ConfidenceScore,
    OpenAIResponse,
    OpenAIMessage,
    ErrorCode,
    ErrorMessage,
    ErrorDetails,
)


class TestTypeAliases:
    """型エイリアスのテストクラス"""
    
    def test_basic_type_aliases(self):
        """基本型エイリアスのテスト"""
        # JsonDict
        json_data: JsonDict = {"key": "value", "number": 123}
        assert isinstance(json_data, dict)
        
        # StringList
        string_list: StringList = ["item1", "item2", "item3"]
        assert isinstance(string_list, list)
        assert all(isinstance(item, str) for item in string_list)
        
        # Optional types
        optional_str: OptionalString = "test"
        assert isinstance(optional_str, str)
        optional_str = None
        assert optional_str is None
        
        optional_float: OptionalFloat = 3.14
        assert isinstance(optional_float, float)
        optional_float = None
        assert optional_float is None
        
        optional_int: OptionalInt = 42
        assert isinstance(optional_int, int)
        optional_int = None
        assert optional_int is None
    
    def test_search_type_aliases(self):
        """検索関連型エイリアスのテスト"""
        # SearchResult
        search_result: SearchResult = {
            "content": "test content",
            "score": 0.95,
            "metadata": {"source": "test"}
        }
        assert isinstance(search_result, dict)
        
        # SearchParams
        search_params: SearchParams = {
            "query": "test query",
            "top_k": 10,
            "filters": ["category1", "category2"]
        }
        assert isinstance(search_params, dict)
        
        # FilterKeywords
        filter_keywords: FilterKeywords = ["keyword1", "keyword2"]
        assert isinstance(filter_keywords, list)
        
        # SearchKeywords
        search_keywords: SearchKeywords = ["search1", "search2"]
        assert isinstance(search_keywords, list)
    
    def test_score_type_aliases(self):
        """スコア関連型エイリアスのテスト"""
        # ScoreFloat
        score_float: ScoreFloat = 0.85
        assert isinstance(score_float, float)
        
        # ScoreTuple
        score_tuple: ScoreTuple = (0.75, True)
        assert isinstance(score_tuple, tuple)
        assert len(score_tuple) == 2
        
        # ScoreDict
        score_dict: ScoreDict = {"similarity": 0.9, "relevance": 0.8}
        assert isinstance(score_dict, dict)
    
    def test_config_type_aliases(self):
        """設定関連型エイリアスのテスト"""
        # ConfigDict
        config_dict: ConfigDict = {
            "database_url": "test://localhost",
            "debug": True,
            "timeout": 30
        }
        assert isinstance(config_dict, dict)
        
        # LimitsDict
        limits_dict: LimitsDict = {"max_retries": 3, "rate_limit": 100}
        assert isinstance(limits_dict, dict)
        
        # ThresholdDict
        threshold_dict: ThresholdDict = {"min_score": 0.7, "max_score": 1.0}
        assert isinstance(threshold_dict, dict)
    
    def test_vector_type_aliases(self):
        """ベクトル検索関連型エイリアスのテスト"""
        # EmbeddingVector
        embedding_vector: EmbeddingVector = [0.1, 0.2, 0.3, -0.1, 0.5]
        assert isinstance(embedding_vector, list)
        assert all(isinstance(val, float) for val in embedding_vector)
        
        # VectorSearchResult
        vector_search_result: VectorSearchResult = [
            {"content": "result1", "score": 0.9},
            {"content": "result2", "score": 0.8}
        ]
        assert isinstance(vector_search_result, list)
        assert all(isinstance(item, dict) for item in vector_search_result)
    
    def test_database_type_aliases(self):
        """データベース関連型エイリアスのテスト"""
        # DatabaseItem
        database_item: DatabaseItem = {
            "id": "123",
            "title": "Test Item",
            "content": "Test content",
            "created_at": "2023-01-01"
        }
        assert isinstance(database_item, dict)
        
        # DatabaseResults
        database_results: DatabaseResults = [
            {"id": "1", "title": "Item 1"},
            {"id": "2", "title": "Item 2"}
        ]
        assert isinstance(database_results, list)
        assert all(isinstance(item, dict) for item in database_results)
    
    def test_classification_type_aliases(self):
        """分類関連型エイリアスのテスト"""
        # ClassificationData
        classification_data: ClassificationData = {
            "text": "sample text",
            "labels": ["label1", "label2"],
            "confidence": 0.95
        }
        assert isinstance(classification_data, dict)
        
        # ConfidenceScore
        confidence_score: ConfidenceScore = 0.87
        assert isinstance(confidence_score, float)
    
    def test_openai_type_aliases(self):
        """OpenAI API関連型エイリアスのテスト"""
        # OpenAIResponse
        openai_response: OpenAIResponse = {
            "choices": [{"message": {"content": "response"}}],
            "usage": {"total_tokens": 100}
        }
        assert isinstance(openai_response, dict)
        
        # OpenAIMessage
        openai_message: OpenAIMessage = {
            "role": "user",
            "content": "Hello, how are you?"
        }
        assert isinstance(openai_message, dict)
    
    def test_error_type_aliases(self):
        """エラーハンドリング関連型エイリアスのテスト"""
        # ErrorCode
        error_code: ErrorCode = "VALIDATION_ERROR"
        assert isinstance(error_code, str)
        
        # ErrorMessage
        error_message: ErrorMessage = "Invalid input provided"
        assert isinstance(error_message, str)
        
        # ErrorDetails
        error_details: ErrorDetails = {
            "code": "400",
            "message": "Bad Request",
            "field": "email",
            "details": "Invalid email format"
        }
        assert isinstance(error_details, dict)
    
    def test_type_compatibility(self):
        """型の互換性テスト"""
        # JsonDict はDict[str, Any]と互換性があることを確認
        def process_json_dict(data: JsonDict) -> JsonDict:
            return data
        
        test_data = {"test": "value", "number": 123}
        result = process_json_dict(test_data)
        assert result == test_data
        
        # StringList はList[str]と互換性があることを確認
        def process_string_list(items: StringList) -> int:
            return len(items)
        
        test_list = ["a", "b", "c"]
        result = process_string_list(test_list)
        assert result == 3
