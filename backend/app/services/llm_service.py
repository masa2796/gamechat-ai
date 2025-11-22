from __future__ import annotations
from typing import List, Any
import os
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """
    MVP用のLLMサービス。
    - デフォルトはスタブ回答（テストやキー未設定時）
    - BACKEND_OPENAI_API_KEY が設定され、かつモック無効のときは OpenAI Chat Completions を利用
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("BACKEND_OPENAI_API_KEY")
        self.mock = (
            os.getenv("BACKEND_TESTING", "false").lower() == "true"
            or os.getenv("BACKEND_MOCK_EXTERNAL_SERVICES", "false").lower() == "true"
            or not self.api_key
            or self.api_key in {"sk-test_openai_key", "test-api-key"}
        )
        self.client = None
        if not self.mock:
            try:
                from openai import OpenAI  # type: ignore
                self.client = OpenAI(api_key=self.api_key)
                logger.info("LLMService: OpenAI クライアント初期化成功 (mock=False)")
            except Exception as e:
                logger.warning("LLMService: OpenAI 初期化失敗 -> スタブにフォールバック", exc_info=e)
                self.client = None
                self.mock = True

    async def generate_answer(self, query: str, context_items: List[dict[str, Any]]):
        q = (query or "").strip()
        if not q:
            return "質問を入力してください。"

        # OpenAI が使える場合は簡易プロンプトで応答生成
        if not self.mock and self.client is not None:
            try:
                context_summary = "\n".join(
                    f"- タイトル: {ci.get('title') or ci.get('name','?')} / 効果: {ci.get('effect_1','(不明)')}"
                    for ci in context_items[:5]
                )
                system_prompt = (
                    "あなたはカードゲームのアシスタントです。与えられたカード候補を参考に日本語で簡潔に回答してください。"
                )
                user_prompt = (
                    (f"候補カード:\n{context_summary}\n\n質問: {q}" if context_items else f"質問: {q}")
                )
                # モデルは軽量を優先（MVP）。失敗時はスタブにフォールバック
                resp = self.client.chat.completions.create(  # type: ignore
                    model=os.getenv("BACKEND_OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "256")),
                )
                content = resp.choices[0].message.content if resp and resp.choices else None
                if content:
                    return content
                logger.warning("LLMService: OpenAI 応答が空 -> スタブへ")
            except Exception as e:
                logger.warning("LLMService: OpenAI 応答生成失敗 -> スタブへ", exc_info=e)

        # スタブ応答（従来どおり）
        if context_items:
            names = ", ".join(ci.get('title') or ci.get('name','?') for ci in context_items[:3])
            return f"{len(context_items)}件参照: {names} / 質問: {q}"
        if any(w in q.lower() for w in ["hello", "hi", "こんにちは"]):
            return "こんにちは！カードについて何でも聞いてください。"
        return f"質問を受け付けました: {q}"
