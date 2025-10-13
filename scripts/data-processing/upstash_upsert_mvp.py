#!/usr/bin/env python3
"""Minimal Upstash upsert utility for MVP deployment.

Usage:
    python scripts/data-processing/upstash_upsert_mvp.py \
        --source data/convert_data.json --namespace mvp_effects

The script loads card records from either `data/convert_data.json` or
`data/data.json`, generates embeddings (using OpenAI when available,
otherwise a deterministic pseudo-embedding), and upserts them into the
configured Upstash Vector index.

Prerequisites:
    - `backend/.env` (or `.env.prod`) must contain the Upstash credentials.
    - Optional: `BACKEND_OPENAI_API_KEY` for real embeddings.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import random

from dotenv import load_dotenv

try:
    from upstash_vector import Index, Vector  # type: ignore
except ImportError as exc:  # pragma: no cover - guidance for setup
    raise SystemExit(
        "upstash-vector パッケージが見つかりません。\n"
        "pip install upstash-vector を実行してください。"
    ) from exc

OPENAI_AVAILABLE = False
try:  # pragma: no cover - optional dependency
    import openai  # type: ignore
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "convert_data.json"


def load_env() -> Tuple[str, str]:
    """Load environment variables required for Upstash access."""
    env_candidates = [
        PROJECT_ROOT / "backend" / ".env.prod",
        PROJECT_ROOT / "backend" / ".env.production",
        PROJECT_ROOT / "backend" / ".env",
        PROJECT_ROOT / ".env"
    ]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(env_path, override=False)

    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    if not url or not token:
        raise SystemExit(
            "UPSTASH_VECTOR_REST_URL または UPSTASH_VECTOR_REST_TOKEN が見つかりません。"
        )
    return url, token


def chunk(records: Iterable[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    """Yield fixed-size chunks from iterable."""
    batch: List[Dict[str, Any]] = []
    for record in records:
        batch.append(record)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def deterministic_embedding(text: str, dim: int = 1536) -> List[float]:
    """Fallback embedding when OpenAI API is unavailable."""
    seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest(), "big")
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(dim)]


def embed_text(text: str) -> List[float]:
    if OPENAI_AVAILABLE and os.getenv("BACKEND_OPENAI_API_KEY"):
        openai.api_key = os.getenv("BACKEND_OPENAI_API_KEY")
        response = openai.embeddings.create(  # type: ignore[attr-defined]
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding  # type: ignore[index]
    return deterministic_embedding(text)


def load_from_convert(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        items = json.load(f)
    for row in items:
        text = row.get("text", "").strip()
        if not text:
            continue
        namespace = row.get("namespace", "default")
        yield {
            "id": row.get("id"),
            "namespace": namespace,
            "text": text,
            "metadata": {
                "source": namespace,
                "snippet": text[:240],
            },
        }


def load_from_data_json(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        cards = json.load(f)
    for card in cards:
        card_id = card.get("id") or card.get("card_id")
        name = card.get("name", "")
        effect = card.get("effect_1") or card.get("effect") or ""
        summary_parts = [name, effect]
        # include optional stats if available
        for key in ("class", "rarity", "type"):
            value = card.get(key)
            if value:
                summary_parts.append(f"{key}: {value}")
        for key in ("cost", "attack", "hp"):
            if card.get(key) is not None:
                summary_parts.append(f"{key}: {card[key]}")
        keywords = card.get("keywords") or []
        if keywords:
            summary_parts.append("keywords: " + ", ".join(keywords))
        qa_list = card.get("qa") or []
        if qa_list:
            q = qa_list[0]
            summary_parts.append(f"Q: {q.get('question','')} A: {q.get('answer','')}")
        text = "\n".join(part for part in summary_parts if part).strip()
        if not text:
            continue
        yield {
            "id": f"card:{card_id}",
            "namespace": "mvp_cards",
            "text": text,
            "metadata": {
                "card_id": card_id,
                "title": name,
                "effect_1": effect,
                "class": card.get("class"),
                "rarity": card.get("rarity"),
            },
        }


def load_records(source: Path) -> Iterable[Dict[str, Any]]:
    if source.name == "convert_data.json":
        return load_from_convert(source)
    if source.name == "data.json":
        return load_from_data_json(source)
    raise SystemExit(f"サポートされていない入力ファイルです: {source}")


def upsert_records(records: Iterable[Dict[str, Any]], namespace_override: str | None, batch_size: int, index: Index) -> None:
    count = 0
    for batch in chunk(records, batch_size):
        vectors: List[Vector] = []
        namespaces: List[str] = []
        for row in batch:
            text = row["text"]
            embedding = embed_text(text)
            namespace = namespace_override or row.get("namespace", "default")
            namespaces.append(namespace)
            vectors.append(
                Vector(
                    id=row.get("id"),
                    vector=embedding,
                    metadata=row.get("metadata", {}),
                )
            )
        # 迅速対応（MVP）: --namespace 未指定時は Upstash のデフォルトnamespaceへ投入（namespace引数を渡さない）
        batch_namespace = namespace_override or (namespaces[0] if namespaces else None)
        if batch_namespace:
            index.upsert(vectors=vectors, namespace=batch_namespace)
        else:
            index.upsert(vectors=vectors)
        count += len(batch)
        ns_label = batch_namespace or "<default>"
        print(f"Upserted {count} records so far (namespace={ns_label})")
    print(f"完了: 合計 {count} 件をアップサートしました")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upstash Vector upsert helper for MVP data")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="入力データのパス (convert_data.json または data.json)",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default=None,
        help="Upstashの名前空間を指定（未指定時は各レコードのnamespaceを使用）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Upstashへまとめて送る件数",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        print(f"入力ファイルが見つかりません: {args.source}", file=sys.stderr)
        return 1

    url, token = load_env()
    index = Index(url=url, token=token)

    records = list(load_records(args.source))
    if not records:
        print("アップサート対象が見つかりませんでした。", file=sys.stderr)
        return 1

    upsert_records(records, args.namespace, args.batch_size, index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
