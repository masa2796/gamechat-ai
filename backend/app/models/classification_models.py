from pydantic import BaseModel
from typing import Optional, List, Any
from enum import Enum

class QueryType(str, Enum):
    """クエリの分類タイプ"""
    FILTERABLE = "filterable"  # フィルター可能（通常DBでクエリ検索）
    SEMANTIC = "semantic"      # 意味検索（ベクトルDBで意味検索）
    HYBRID = "hybrid"          # 両方を使用
    GREETING = "greeting"      # 挨拶・雑談（検索不要）

class ClassificationRequest(BaseModel):
    """LLMによる分類リクエスト"""
    query: str

class ClassificationResult(BaseModel):
    """LLMによる分類結果"""
    query_type: QueryType
    summary: str  # 要約されたクエリ
    confidence: float  # 分類の信頼度 (0.0-1.0)
    filter_keywords: Optional[List[str]] = None  # フィルター用キーワード
    search_keywords: Optional[List[str]] = None  # 検索用キーワード
    reasoning: Optional[str] = None  # 分類の理由

class SearchStrategy(BaseModel):
    """検索戦略"""
    use_db_filter: bool
    use_vector_search: bool
    db_filter_params: Optional[dict[str, Any]] = None
    vector_search_params: Optional[dict[str, Any]] = None
