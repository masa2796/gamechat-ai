#!/usr/bin/env python3
"""ARCHIVE_CANDIDATE: 運用向けメトリクス集計でMVPでは未使用。

Feedback 簡易集計スクリプト

In-memory 保存 (MVP) を前提に FastAPI の /api/feedback/recent を叩いて
negative_rate / zero_hit_rate を CSV 1行で出力。

使い方:
  python scripts/data-processing/feedback_summary.py --base-url http://localhost:8000 --limit 500 \
      > feedback_metrics.csv

CSV ヘッダ: timestamp,total,negative_count,negative_rate
zero_hit_rate は今後 query ログ蓄積後に拡張予定（現時点では未計測のため空列）。
"""
from __future__ import annotations
import argparse
import csv
import sys
import json
from datetime import datetime
import urllib.request
import urllib.parse


def fetch_feedback(base_url: str, limit: int) -> list[dict]:
    url = f"{base_url.rstrip('/')}/api/feedback/recent?limit={limit}"
    with urllib.request.urlopen(url, timeout=10) as resp:  # nosec B310 (信頼内部用)
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("items", [])


def summarize(items: list[dict]) -> dict:
    total = len(items)
    neg = sum(1 for x in items if x.get("rating") == -1)
    neg_rate = (neg / total) if total else 0.0
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total": total,
        "negative_count": neg,
        "negative_rate": f"{neg_rate:.4f}",
        "zero_hit_rate": ""  # 将来拡張
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000", help="API ベースURL")
    ap.add_argument("--limit", type=int, default=200, help="取得件数")
    args = ap.parse_args()

    try:
        items = fetch_feedback(args.base_url, args.limit)
        summary = summarize(items)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    writer = csv.DictWriter(sys.stdout, fieldnames=["timestamp","total","negative_count","negative_rate","zero_hit_rate"])
    writer.writeheader()
    writer.writerow(summary)

if __name__ == "__main__":
    main()
