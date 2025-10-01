# Minimal VectorService for MVP
from __future__ import annotations
from typing import List
import os
import hashlib
import logging
logger = logging.getLogger(__name__)
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
                logger.info("VectorService: Upstash 接続成功")
            except Exception as e:
                self.enabled = False
                self.index = None
                logger.warning("VectorService: Upstash 初期化失敗 -> フォールバックのみ", exc_info=e)
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
                top_scores = []
                for m in matches:
                    meta = getattr(m, 'metadata', None)
                    score = getattr(m, 'score', None)
                    if isinstance(score, (int, float)):
                        top_scores.append(float(score))
                    title = meta.get('title') if meta and hasattr(meta, 'get') else None
                    if title and title not in titles:
                        titles.append(title)
                    if len(titles) >= top_k:
                        break
                if not titles:
                    logger.warning("VectorService: Upstash 検索結果 0 件 -> ダミータイトルへ")
                # 統計送信（MVP: 調整は行われない）
                # 動的閾値調整機能はMVP除外（top_score/spread算出も省略）
                return titles
            except Exception as e:
                logger.warning("VectorService: Upstash 検索失敗 -> ダミータイトルフォールバック", exc_info=e)
        # フォールバック: embedding からダミータイトル生成
        h = hashlib.sha1("|".join(str(round(v,4)) for v in embedding[:16]).encode()).hexdigest()
        base = [f"カード{int(h[i:i+3],16)%900+100}" for i in range(0, min(len(h), top_k*3), 3)]
        # 去重して top_k
        seen, out = set(), []
        for t in base:
            if t not in seen:
                seen.add(t)
                out.append(t)
            if len(out) >= top_k:
                break
    # 動的閾値調整機能はMVP除外
        logger.info("VectorService: フォールバック生成タイトル", {"count": len(out)})
        return out