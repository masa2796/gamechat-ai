#!/usr/bin/env python3
"""ARCHIVE_CANDIDATE: 高度な閾値デバッグ向けでMVPでは未使用。

Quick debug script to probe raw vector scores with min_score=0.0.

Usage:
  python scripts/data-processing/debug_vector_threshold.py --query "継続ダメージ" --top-k 10

It bypasses HybridSearch and calls VectorService directly after producing an embedding
(with mock hash embedding if OpenAI client not configured).
"""
from __future__ import annotations
import os
import sys
import argparse
import asyncio
import hashlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.append(ROOT)
BACKEND_DIR = os.path.join(ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from app.services.vector_service import VectorService  # type: ignore  # noqa: E402
from app.services.embedding_service import EmbeddingService  # type: ignore  # noqa: E402
from app.models.classification_models import ClassificationResult, QueryType  # type: ignore  # noqa: E402

async def main_async(args: argparse.Namespace):
    # Minimal mock classification
    classification = ClassificationResult(
        query_type=QueryType.SEMANTIC,
        summary=args.query,
        confidence=0.85,
        filter_keywords=[],
        search_keywords=[]
    )
    emb_service = EmbeddingService()
    # If real client missing, provide deterministic mock embedding
    try:
        emb = await emb_service.get_embedding(args.query)  # type: ignore
    except Exception:
        h = hashlib.sha1(args.query.encode()).hexdigest()
        emb = [((int(h[i % len(h)], 16) / 15.0) * 2 - 1) for i in range(1536)]
    vs = VectorService()
    # Force namespaces discovery
    namespaces = vs._get_default_namespaces(classification)
    print(f"Namespaces ({len(namespaces)}): {namespaces}")
    # Call search with min_score=0.0
    titles = await vs.search(emb, top_k=args.top_k, namespaces=namespaces, classification=classification, min_score=0.0)
    print(f"Returned {len(titles)} titles (top_k={args.top_k})")
    if not titles:
        print("No titles even at min_score=0.0")
    else:
        print("Top titles:")
        for t in titles[:min(10, len(titles))]:
            score = vs.last_scores.get(t)
            print(f"  {t}  score={score}")
    # Inspect per-namespace stats from last_params if available
    print("Raw last_params:", vs.last_params)

def parse_args(argv: list[str]):
    ap = argparse.ArgumentParser()
    ap.add_argument('--query', required=True)
    ap.add_argument('--top-k', type=int, default=20)
    return ap.parse_args(argv)

if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    asyncio.run(main_async(args))
