# Minimal EmbeddingService for MVP
from __future__ import annotations
from typing import List
import os
import hashlib
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """MVP用: OpenAI未設定/テスト時は決定論的擬似ベクトルを返す簡易実装."""
    def __init__(self) -> None:
        self.api_key = os.getenv("BACKEND_OPENAI_API_KEY")
        # モック条件 (未設定 / テスト / モック外部サービス指定 / テスト用ダミーキー)
        self.is_mock = (
            os.getenv("BACKEND_TESTING", "false").lower() == "true"
            or os.getenv("BACKEND_MOCK_EXTERNAL_SERVICES", "false").lower() == "true"
            or not self.api_key
            or self.api_key in {"sk-test_openai_key", "test-api-key"}
        )
        try:
            if not self.is_mock:
                from openai import OpenAI  # type: ignore
                self.client = OpenAI(api_key=self.api_key)
                logger.info("EmbeddingService: OpenAI クライアント初期化成功 (mock=False)")
            else:
                self.client = None
                logger.warning("EmbeddingService: モックモードで初期化 (APIキー未設定またはテスト設定)")
        except Exception as e:
            self.client = None
            self.is_mock = True
            logger.warning("EmbeddingService: OpenAI 初期化失敗 -> モックへフォールバック", exc_info=e)

    async def get_embedding(self, query: str) -> List[float]:
        q = (query or "").strip()
        if not q:
            return []
        if self.is_mock or not self.client:
            # 決定論的 md5 ベース擬似ベクトル (128次元): 安定テスト用
            h = hashlib.md5(q.encode()).hexdigest()
            return [(int(h[i % len(h)], 16) - 7.5) / 7.5 for i in range(128)]
        try:  # 実API利用 (失敗してもフォールバック)
            resp = self.client.embeddings.create(input=q, model="text-embedding-3-small")
            emb = resp.data[0].embedding
            return emb[:128]
        except Exception as e:
            logger.warning("EmbeddingService: OpenAI 埋め込み取得失敗 -> sha256 擬似ベクトル", exc_info=e)
            h = hashlib.sha256(q.encode()).digest()
            return [(b - 128) / 128 for b in h[:128]]
