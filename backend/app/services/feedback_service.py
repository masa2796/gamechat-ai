from __future__ import annotations
from typing import Dict, Optional, List
import threading
from datetime import datetime, timedelta
from ..models.feedback_models import QueryContext, FeedbackStored, FeedbackCreate
from ..core.logging import GameChatLogger

class FeedbackService:
    """インメモリ簡易実装 (MVP)。将来RDB/Auditログへ移行予定。"""
    _instance: Optional['FeedbackService'] = None
    # インスタンス初期化済みフラグ（動的属性アクセスを避けてmypy対応）
    _initialized: bool = False

    def __new__(cls, *args: object, **kwargs: object) -> 'FeedbackService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # 既に初期化済みならスキップ
        if self._initialized:
            return
        self._initialized = True
        self._context_lock = threading.Lock()
        self._feedback_lock = threading.Lock()
        self._contexts: Dict[str, QueryContext] = {}
        self._feedbacks: List[FeedbackStored] = []
        self._ttl = timedelta(minutes=30)  # QueryContext 有効期間

    # QueryContext 操作
    def store_query_context(self, ctx: QueryContext) -> None:
        with self._context_lock:
            self._contexts[ctx.query_id] = ctx
        GameChatLogger.log_debug("feedback", "query_context_stored", {"query_id": ctx.query_id})

    def get_query_context(self, query_id: str) -> Optional[QueryContext]:
        with self._context_lock:
            ctx = self._contexts.get(query_id)
            if ctx and datetime.utcnow() - ctx.created_at > self._ttl:
                # TTL超過なら削除
                del self._contexts[query_id]
                return None
            return ctx

    def cleanup_expired(self) -> int:
        removed = 0
        with self._context_lock:
            for qid, ctx in list(self._contexts.items()):
                if datetime.utcnow() - ctx.created_at > self._ttl:
                    del self._contexts[qid]
                    removed += 1
        if removed:
            GameChatLogger.log_info("feedback", f"expired_contexts_removed={removed}")
        return removed

    # Feedback 保存
    def submit_feedback(self, fb: FeedbackCreate) -> FeedbackStored:
        ctx = self.get_query_context(fb.query_id)
        if not ctx:
            # コンテキストなし: 最低限で保存（将来: エラーにするか検討）
            stored = FeedbackStored(
                id=f"fb_{len(self._feedbacks)+1}",
                query_id=fb.query_id,
                rating=fb.rating,
                query_text="",
                answer_text="",
                query_type=None,
                classification_summary=None,
                vector_top_titles=[],
                namespaces=[],
                min_score=None,
                top_scores=[],
                created_at=datetime.utcnow(),
                user_reason=fb.user_reason
            )
        else:
            stored = FeedbackStored(
                id=f"fb_{len(self._feedbacks)+1}",
                query_id=ctx.query_id,
                rating=fb.rating,
                query_text=ctx.query_text,
                answer_text=ctx.answer_text,
                query_type=ctx.query_type,
                classification_summary=ctx.classification_summary,
                vector_top_titles=ctx.vector_top_titles,
                namespaces=ctx.namespaces,
                min_score=ctx.min_score,
                top_scores=ctx.top_scores,
                created_at=datetime.utcnow(),
                user_reason=fb.user_reason
            )
        with self._feedback_lock:
            self._feedbacks.append(stored)
    # モニタリング機能削除(MVP)に伴いメトリクス送信は無効化
        GameChatLogger.log_success("feedback", "submitted", {"query_id": stored.query_id, "rating": stored.rating})
        return stored

    def list_recent(self, limit: int = 50) -> List[FeedbackStored]:
        with self._feedback_lock:
            return list(self._feedbacks[-limit:])

feedback_service = FeedbackService()
