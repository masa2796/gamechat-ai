"""
ARCHIVE_CANDIDATE: Removed in MVP

This module is kept as a no-op placeholder to avoid import errors from
legacy scripts/tests. Use the /chat endpoint implemented in
backend/app/routers/rag.py for MVP.
"""
from __future__ import annotations
from typing import Any, Dict


class RagService:  # pragma: no cover
    async def process_query(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError("RagService is removed in MVP; use /chat endpoint.")

    async def process_query_optimized(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError("RagService is removed in MVP; use /chat endpoint.")