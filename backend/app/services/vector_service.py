# Minimal VectorService for MVP
from __future__ import annotations
from typing import List
import os, hashlib
try:
    from upstash_vector import Index  # type: ignore
except Exception:
    Index = None  # type: ignore

class VectorService:
    def __init__(self) -> None:
        self.url = os.getenv("UPSTASH_VECTOR_REST_URL")
        self.token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        self.enabled = bool(self.url and self.token and Index)
        if self.enabled:
            try:
                self.index = Index(url=self.url, token=self.token)  # type: ignore
            except Exception:
                self.enabled = False
                self.index = None
        else:
            self.index = None

    async def search(self, embedding: List[float], top_k: int = 5) -> List[str]:
        if not embedding:
            return []
        if self.enabled and self.index:
            try:
                res = self.index.query(vector=embedding, top_k=top_k, include_metadata=True)  # type: ignore
                matches = getattr(res, 'matches', res) or []
                titles = []
                for m in matches:
                    meta = getattr(m, 'metadata', None)
                    title = meta.get('title') if meta and hasattr(meta,'get') else None
                    if title and title not in titles:
                        titles.append(title)
                    if len(titles) >= top_k:
                        break
                return titles
            except Exception:
                pass
        # フォールバック: embedding からダミータイトル生成
        h = hashlib.sha1("|".join(str(round(v,4)) for v in embedding[:16]).encode()).hexdigest()
        base = [f"カード{int(h[i:i+3],16)%900+100}" for i in range(0, min(len(h), top_k*3), 3)]
        # 去重して top_k
        seen, out = set(), []
        for t in base:
            if t not in seen:
                seen.add(t); out.append(t)
            if len(out) >= top_k:
                break
        return out