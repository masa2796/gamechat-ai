"""MVP用の最小チャットエンドポイント

目的:
  - /chat に POST されたユーザー入力を受け取り
  - OpenAI Embedding (利用不可ならフォールバック擬似埋め込み)
  - Upstash Vector 経由のベクトル検索のみを実行（ハイブリッド/分類なし）
  - 取得タイトルに対応するカード簡易情報 (convert_data.json or data.json) を抽出
  - それらを簡易プロンプトとして LLMService (スタブ) に渡し回答を生成

非機能:
  - 認証 / reCAPTCHA / レート制限 / 詳細メトリクスは無効 (MVP範囲外)
  - 失敗時は 200 で汎用メッセージを返し UX を優先
"""

from __future__ import annotations

from fastapi import APIRouter
# Deprecated duplicate MVP chat (now in rag.py). Stub only.
router = APIRouter()
