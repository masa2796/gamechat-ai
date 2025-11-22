from fastapi import APIRouter, Body
from typing import Dict, Any, List
from pydantic import BaseModel
import json
import threading
import logging
from ..services.embedding_service import EmbeddingService
from ..services.vector_service import VectorService
from ..services.llm_service import LLMService
from ..services.storage_service import StorageService
import os

logger = logging.getLogger(__name__)

router = APIRouter()
## 旧RAG/検索テストエンドポイント削除（MVP）

############################
# MVP シンプルチャット (/chat)
#  - 認証 / reCAPTCHA / ハイブリッド検索を排除
#  - Embedding + Vector 検索 + 最小カード情報 + スタブLLM
############################

class MVPChatRequest(BaseModel):
    message: str
    top_k: int | None = 5
    with_context: bool | None = True

_mvp_card_index_lock = threading.Lock()
_mvp_card_index: Dict[str, Dict[str, Any]] | None = None

def _mvp_load_card_index() -> Dict[str, Dict[str, Any]]:
    global _mvp_card_index
    if _mvp_card_index is not None:
        return _mvp_card_index
    with _mvp_card_index_lock:
        if _mvp_card_index is not None:
            return _mvp_card_index
        storage = StorageService()
        paths = [storage.get_file_path("convert_data"), storage.get_file_path("data")]
        idx: Dict[str, Dict[str, Any]] = {}
        for p in paths:
            if not p or not os.path.exists(p):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if not isinstance(item, dict):
                            continue
                        title = item.get("title") or item.get("name")
                        if title and title not in idx:
                            idx[title] = {k: v for k, v in item.items() if k in {"title","name","effect_1","rarity","class","cost","attack","hp"}}
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, dict):
                            title = v.get("title") or k
                            if title and title not in idx:
                                idx[title] = {kk: vv for kk, vv in v.items() if kk in {"title","name","effect_1","rarity","class","cost","attack","hp"}}
            except Exception:
                continue
        _mvp_card_index = idx
        return _mvp_card_index

@router.post("/chat")
async def chat(req: MVPChatRequest = Body(...)) -> Dict[str, Any]:
    question = (req.message or "").strip()
    if not question:
        return {"answer": "質問を入力してください。", "context": None}

    embedding_service = EmbeddingService()
    vector_service = VectorService()
    llm_service = LLMService()

    # Embedding 取得（サービス内でモック/フォールバック可能）
    try:
        embedding = await embedding_service.get_embedding(question)
        if not embedding:
            raise ValueError("empty embedding")
    except Exception as e:
        logger.warning("/chat: Embedding 取得失敗 -> sha256 擬似ベクトル", exc_info=e)
        import hashlib
        h = hashlib.sha256(question.encode()).digest()
        embedding = [(b - 128) / 128 for b in h][:128]

    # Vector search
    try:
        titles: List[str] = await vector_service.search(embedding, top_k=req.top_k or 5)
    except Exception as e:
        logger.warning("/chat: Vector 検索失敗 -> 空リスト", exc_info=e)
        titles = []

    context_items: List[Dict[str, Any]] = []
    if titles and req.with_context:
        idx = _mvp_load_card_index()
        for t in titles:
            item = idx.get(t)
            if item:
                context_items.append(item)
            if len(context_items) >= (req.top_k or 5):
                break

    try:
        answer = await llm_service.generate_answer(question, context_items)
    except Exception:
        answer = (f"{len(context_items)}件のカード情報を参照しました。質問: {question}" if context_items else
                  "検索結果が得られませんでした。別の聞き方を試してください。")

    return {
        "answer": answer,
        "context": context_items if req.with_context else None,
        "retrieved_titles": titles
    }


############################
# 管理/診断用（MVPデフォルト無効）
############################
# 将来の管理/診断系エンドポイント (動的閾値/高度監視等) は MVP では非搭載