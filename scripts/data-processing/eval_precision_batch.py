#!/usr/bin/env python
"""Batch evaluation for vector/hybrid card effect search.

Features:
 - Loads labeled relevance data (JSON) containing queries and relevant card titles.
 - Executes HybridSearchService for each query (offline-friendly mock by default).
 - Computes per-query metrics: P@K (default K=10), Recall@K, MRR, hit_count.
 - Aggregates overall averages and zero-hit rate.
 - Writes a timestamped CSV under logs/eval and prints a concise summary for KPI table.

Usage examples:
  python scripts/data-processing/eval_precision_batch.py \
      --labels data/eval/relevance_labels.json

  # Real mode (requires proper OpenAI + Upstash env vars)
  python scripts/data-processing/eval_precision_batch.py --real

  # Custom top-k
  python scripts/data-processing/eval_precision_batch.py --top-k 20

Label file format (JSON):
{
  "queries": [
    {"query": "リーダー直接ダメージ", "relevant": ["カード名1", "カード名2"]},
    ...
  ]
}

Notes:
 - If a query has an empty relevant list, Recall@K is reported as '' (blank) to avoid misleading division.
 - In offline (default) mode:
     * Classification is mocked as semantic with confidence 0.85.
     * Vector search is mocked when Upstash is not configured, returning deterministic dummy titles.
 - Once labels are populated with true relevant titles and real mode is used, metrics form the baseline.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any

# Ensure backend app importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.append(ROOT)
BACKEND_DIR = os.path.join(ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

try:
    from app.services.hybrid_search_service import HybridSearchService  # type: ignore
except Exception as e:  # pragma: no cover
    print(f"[WARN] Failed to import backend services: {e}")
    HybridSearchService = None  # type: ignore


@dataclass
class QueryEvalResult:
    query: str
    top_k: int
    retrieved: List[str]
    relevant: List[str]
    hits: List[str]
    p_at_k: float
    recall_at_k: float | None
    mrr: float


def mock_classification_response():
    """Return a mock OpenAI chat completion style object for semantic classification."""
    resp = type("MockResponse", (), {})()
    resp.choices = [type("Choice", (), {})()]
    resp.choices[0].message = type("Message", (), {})()
    resp.choices[0].message.content = json.dumps({
        "query_type": "semantic",
        "summary": "効果検索",
        "confidence": 0.85,
        "filter_keywords": [],
        "search_keywords": []
    }, ensure_ascii=False)
    return resp


def ensure_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def compute_metrics(query: str, retrieved: List[str], relevant: List[str], k: int) -> QueryEvalResult:
    rel_set = set(relevant)
    top_k_list = retrieved[:k]
    hits = [t for t in top_k_list if t in rel_set]
    p_at_k = len(hits) / float(k) if k > 0 else 0.0
    recall_at_k: float | None
    if relevant:
        recall_at_k = len(hits) / float(len(rel_set)) if rel_set else 0.0
    else:
        recall_at_k = None  # undefined when no labels
    # MRR
    mrr = 0.0
    for rank, title in enumerate(top_k_list, start=1):
        if title in rel_set:
            mrr = 1.0 / rank
            break
    return QueryEvalResult(
        query=query,
        top_k=k,
        retrieved=top_k_list,
        relevant=relevant,
        hits=hits,
        p_at_k=p_at_k,
        recall_at_k=recall_at_k,
        mrr=mrr,
    )


def average(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_labels(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Labels file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "queries" not in data:
        raise ValueError("Label file must contain a 'queries' list.")
    queries = data["queries"]
    if not isinstance(queries, list):
        raise ValueError("'queries' must be a list.")
    # normalize
    norm = []
    for item in queries:
        if not isinstance(item, dict):
            continue
        q = str(item.get("query", "")).strip()
        relevant = item.get("relevant", [])
        if not isinstance(relevant, list):
            relevant = []
        norm.append({"query": q, "relevant": [str(r) for r in relevant]})
    return norm


def run_evaluation(args: argparse.Namespace) -> int:
    labels = load_labels(args.labels)
    service = HybridSearchService() if HybridSearchService else None
    if service is None:
        print("[ERROR] HybridSearchService unavailable. Aborting.")
        return 1

    # Optionally prepare mock clients
    if not args.real:
        # Patch classification & embedding calls
        mock_client = type("MockOpenAI", (), {})()
        mock_client.chat = type("Chat", (), {})()
        mock_client.chat.completions = type("Completions", (), {})()
        mock_client.chat.completions.create = lambda *a, **kw: mock_classification_response()
        service.classification_service.client = mock_client  # type: ignore
        service.embedding_service.client = mock_client  # type: ignore

        # Stub embedding methods to bypass real OpenAI embeddings (return deterministic vector)
        import hashlib

        async def _stub_get_embedding_from_classification(original_query: str, classification):  # type: ignore
            h = hashlib.md5(original_query.encode()).hexdigest()
            return [((int(h[i % len(h)], 16) / 15.0) * 2 - 1) for i in range(1536)]

        async def _stub_get_embedding(query: str):  # type: ignore
            h = hashlib.sha1(query.encode()).hexdigest()
            return [((int(h[i % len(h)], 16) / 15.0) * 2 - 1) for i in range(1536)]

        service.embedding_service.get_embedding_from_classification = _stub_get_embedding_from_classification  # type: ignore
        service.embedding_service.get_embedding = _stub_get_embedding  # type: ignore

        # If Upstash is not configured, patch vector search as deterministic dummy output
        if getattr(service.vector_service, "vector_index", None) is None:
            dummy = [f"ダミーカード{i}" for i in range(1, 51)]

            async def mock_vector_search(*_a, **_kw):  # noqa: ANN001
                return dummy[: _kw.get("top_k", 10)]

            service.vector_service.search = mock_vector_search  # type: ignore

    top_k = args.top_k
    per_query: List[QueryEvalResult] = []
    raw_topk_store: list[dict[str, any]] = []  # dump-scores 用
    plateau_trigger_count = 0
    plateau_applicable_count = 0  # scoresが存在したクエリで判定対象数 (approx)
    for item in labels:
        query = item["query"]
        relevant = item["relevant"]
        if args.skip_unlabeled and not relevant:
            print(f"[EVAL] Skip unlabeled query: {query}")
            continue
        print(f"[EVAL] Processing {len(per_query)+1}/{len(labels)}: {query}", flush=True)
        try:
            # HybridSearchService.search is async
            import asyncio
            retrieved_dict = asyncio.run(service.search(query, top_k=top_k))  # type: ignore
            # Extract context titles
            context = retrieved_dict.get("context", []) if isinstance(retrieved_dict, dict) else []
            titles: List[str] = []
            for c in context:
                # 検索提案 (suggestion) 行はゼロヒット扱いのため除外
                if isinstance(c, dict):
                    if "suggestion" in c or c.get("name") == "検索のご提案":
                        continue
                    title = c.get("name") or c.get("title")
                    if title:
                        titles.append(str(title))
            # fallback: search_info has counts but not titles; keep as is
            eval_res = compute_metrics(query, titles, relevant, top_k)
            # Collect plateau stats always
            try:
                vs = getattr(service, 'vector_service', None)
                last_params = getattr(vs, 'last_params', {}) if vs else {}
                if isinstance(last_params, dict) and 'plateau_stats' in last_params:
                    plateau_applicable_count += 1
                    if last_params.get('plateau_triggered'):
                        plateau_trigger_count += 1
                if args.dump_scores:
                    last_scores = getattr(vs, 'last_scores', {}) if vs else {}
                    ranked = sorted(last_scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
                    for rank, (title, score) in enumerate(ranked, start=1):
                        raw_topk_store.append({
                            'query': query,
                            'rank': rank,
                            'title': title,
                            'score': f"{score:.4f}",
                            'min_score': f"{(last_params.get('min_score') or 0):.4f}" if isinstance(last_params.get('min_score'), (int,float)) else "",
                            'stage': last_params.get('final_stage'),
                            'namespaces': ';'.join(last_params.get('used_namespaces', [])[:10]) if isinstance(last_params.get('used_namespaces'), list) else ''
                        })
            except Exception as e:  # pragma: no cover
                if args.dump_scores:
                    print(f"[WARN] dump-scores capture failed: {e}")
            per_query.append(eval_res)
        except Exception as e:  # pragma: no cover
            print(f"[WARN] Query failed '{query}': {e}")
            per_query.append(
                compute_metrics(query, [], relevant, top_k)
            )

    # Aggregate
    p_list = [r.p_at_k for r in per_query]
    recall_list = [r.recall_at_k for r in per_query if r.recall_at_k is not None]
    mrr_list = [r.mrr for r in per_query]
    # zero-hit: 実カード (suggestion 除く) が取得 0 のクエリ
    zero_hits = sum(1 for r in per_query if len(r.retrieved) == 0)

    overall_p = average(p_list)
    overall_recall = average(recall_list) if recall_list else 0.0
    overall_mrr = average(mrr_list)
    zero_hit_rate = zero_hits / len(per_query) if per_query else 0.0

    # Output CSV
    out_dir = args.output
    ensure_dirs(out_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"batch_metrics_{ts}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "query",
            "p_at_k",
            "recall_at_k",
            "mrr",
            "hit_count",
            "total_relevant",
            "hits",
            "retrieved_top_k",
        ])
        for r in per_query:
            writer.writerow([
                r.query,
                f"{r.p_at_k:.4f}",
                (f"{r.recall_at_k:.4f}" if r.recall_at_k is not None else ""),
                f"{r.mrr:.4f}",
                len(r.hits),
                len(r.relevant),
                ";".join(r.hits),
                ";".join(r.retrieved),
            ])
        # Footer summary row
        writer.writerow([])
        writer.writerow(["OVERALL_P@K", f"{overall_p:.4f}"])
        writer.writerow(["OVERALL_Recall@K", f"{overall_recall:.4f}"])
        writer.writerow(["OVERALL_MRR", f"{overall_mrr:.4f}"])
        writer.writerow(["ZERO_HIT_RATE", f"{zero_hit_rate:.4f}"])

    # Optional dump-scores CSV
    if args.dump_scores and raw_topk_store:
        dump_path = os.path.join(out_dir, f"dump_scores_{ts}.csv")
        with open(dump_path, 'w', newline='', encoding='utf-8') as df:
            dw = csv.writer(df)
            dw.writerow(['query','rank','title','score','stage','min_score','namespaces'])
            for row in raw_topk_store:
                dw.writerow([
                    row['query'], row['rank'], row['title'], row['score'], row.get('stage',''), row.get('min_score',''), row.get('namespaces','')
                ])
        print(f"[DUMP] Raw top-k scores written: {dump_path}")

    # Summary stdout (KPI table paste-ready)
    print("\n=== Batch Evaluation Summary ===")
    print(f"Queries: {len(per_query)}  Top-K: {top_k}")
    print(f"P@{top_k}: {overall_p:.4f}")
    print(f"Recall@{top_k}: {overall_recall:.4f} (labels w/ relevance: {len(recall_list)})")
    print(f"MRR: {overall_mrr:.4f}")
    plateau_rate = (plateau_trigger_count / plateau_applicable_count) if plateau_applicable_count else 0.0
    print(f"Zero-Hit Rate: {zero_hit_rate:.4f}")
    print(f"Plateau Trigger Rate: {plateau_rate:.4f}  (triggered {plateau_trigger_count} / applicable {plateau_applicable_count})")
    print(f"CSV: {out_path}")
    print("================================")

    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate search precision/recall metrics batch.")
    parser.add_argument("--labels", default="data/eval/relevance_labels.json", help="Path to relevance labels JSON")
    parser.add_argument("--output", default="logs/eval", help="Directory to write CSV")
    parser.add_argument("--top-k", type=int, default=10, help="Top-K cutoff (default=10)")
    parser.add_argument("--real", action="store_true", help="Use real classification/vector search (requires env)")
    parser.add_argument("--dump-scores", action="store_true", help="Dump per-query raw top-k scores & namespaces")
    parser.add_argument("--skip-unlabeled", action="store_true", help="Skip queries whose relevant list is empty (they don't affect Recall anyway)")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    return run_evaluation(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
