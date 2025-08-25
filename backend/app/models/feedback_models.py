from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class FeedbackCreate(BaseModel):
    query_id: str = Field(..., description="サーバ側が発行した検索クエリID")
    rating: int = Field(..., ge=-1, le=1, description="-1=悪い,0=中立,1=良い")
    user_reason: Optional[str] = Field(None, max_length=500)

class FeedbackStored(BaseModel):
    id: str
    query_id: str
    rating: int
    query_text: str
    answer_text: str
    query_type: Optional[str]
    classification_summary: Optional[str]
    vector_top_titles: List[Dict[str, Any]] = []
    namespaces: List[str] = []
    min_score: Optional[float]
    top_scores: List[Dict[str, Any]] = []
    created_at: datetime
    user_reason: Optional[str]

class QueryContext(BaseModel):
    query_id: str
    query_text: str
    answer_text: str
    query_type: Optional[str]
    classification_summary: Optional[str]
    vector_top_titles: List[Dict[str, Any]] = []
    namespaces: List[str] = []
    min_score: Optional[float] = None
    top_scores: List[Dict[str, Any]] = []
    created_at: datetime

    @staticmethod
    def new(query_text: str, answer_text: str, query_type: Optional[str], classification_summary: Optional[str], vector_top_titles: List[Dict[str, Any]], namespaces: List[str], min_score: Optional[float], top_scores: List[Dict[str, Any]]) -> "QueryContext":
        return QueryContext(
            query_id=str(uuid.uuid4()),
            query_text=query_text,
            answer_text=answer_text,
            query_type=query_type,
            classification_summary=classification_summary,
            vector_top_titles=vector_top_titles,
            namespaces=namespaces,
            min_score=min_score,
            top_scores=top_scores,
            created_at=datetime.utcnow()
        )
