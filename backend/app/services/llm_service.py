from __future__ import annotations
from typing import List, Any
import os

class LLMService:
    def __init__(self) -> None:
        self.mock = (os.getenv("BACKEND_TESTING","false").lower()=="true" or
                     os.getenv("BACKEND_MOCK_EXTERNAL_SERVICES","false").lower()=="true")
    async def generate_answer(self, query: str, context_items: List[dict[str, Any]]):
        q = (query or "").strip()
        if not q:
            return "質問を入力してください。"
        if context_items:
            names = ", ".join(ci.get('title') or ci.get('name','?') for ci in context_items[:3])
            return f"{len(context_items)}件参照: {names} / 質問: {q}"
        if any(w in q.lower() for w in ["hello","hi","こんにちは"]):
            return "こんにちは！カードについて何でも聞いてください。"
        return f"質問を受け付けました: {q}"
