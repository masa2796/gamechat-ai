"""
型エイリアス定義
"""
from typing import Dict, List, Any, Optional, Tuple

# 基本型エイリアス
JsonDict = Dict[str, Any]
StringList = List[str]
OptionalString = Optional[str]
OptionalFloat = Optional[float]
OptionalInt = Optional[int]

# 検索関連の型エイリアス
SearchResult = Dict[str, Any]
SearchParams = Dict[str, Any]
FilterKeywords = List[str]
SearchKeywords = List[str]

# スコア関連の型エイリアス
ScoreFloat = float
ScoreTuple = Tuple[float, bool]
ScoreDict = Dict[str, float]

# 設定関連の型エイリアス
ConfigDict = Dict[str, Any]
LimitsDict = Dict[str, int]
ThresholdDict = Dict[str, float]

# ベクトル検索関連の型エイリアス
EmbeddingVector = List[float]
VectorSearchResult = List[Dict[str, Any]]

# データベース関連の型エイリアス
DatabaseItem = Dict[str, Any]
DatabaseResults = List[DatabaseItem]

# 分類関連の型エイリアス
ClassificationData = Dict[str, Any]
ConfidenceScore = float

# OpenAI API関連の型エイリアス
OpenAIResponse = Dict[str, Any]
OpenAIMessage = Dict[str, str]

# エラーハンドリング関連の型エイリアス
ErrorCode = str
ErrorMessage = str
ErrorDetails = Dict[str, Any]
