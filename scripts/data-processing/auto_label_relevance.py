#!/usr/bin/env python
"""ARCHIVE_CANDIDATE: 非MVP向けの関連度自動ラベリングスクリプト。

Heuristic helper to propose relevance labels for evaluation queries.

This script scans `data/data.json` card effects and tries to map predefined
evaluation queries to card titles by simple keyword / pattern rules.

It DOES NOT overwrite the official labels file automatically; instead it
prints a JSON structure you can review and then copy into
`data/eval/relevance_labels.json` after domain validation.

Usage:
  python scripts/data-processing/auto_label_relevance.py \
      --queries-file data/eval/relevance_labels.json \
      --data-file data/data.json \
      --min-per-query 3 > /tmp/proposed_labels.json

Limitations:
 - Purely keyword based; nuanced domain intent (e.g. 継続ダメージ vs 単発) is
   not distinguished.
 - Some queries (守護無視, 継続ダメージ) are approximated; please manually
   curate if the suggestions are semantically off.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import List, Dict, Any


def load_cards(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_queries(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("queries", [])


def extract_effect_text(card: Dict[str, Any]) -> str:
    parts: List[str] = []
    for i in range(1, 10):
        key = f"effect_{i}"
        v = card.get(key)
        if v:
            parts.append(str(v))
    return "\n".join(parts)


def build_patterns():
    # Each query maps to list of regex patterns; card is selected if ALL groups have at least one match (AND of pattern groups)
    return {
        "継続ダメージ": [r"ターン終了時", r"ダメージ"],  # fallback: if few hits, a second pass with just ダメージ & ランダム
        "守護無視": [r"守護.*失う|守護.*無視"],  # ward removal or ignore
        "手札ドロー": [r"デッキから[0-9一二三四五六七八九]*枚?を引"],
        "全体強化": [r"すべては\+\d/\+\d|すべては\+\d\+/\+\d|場の他のフォロワー.*\+"],
        "リーダー直接ダメージ": [r"相手のリーダー.*ダメージ"],
        "単体破壊": [r"1枚を選ぶ。それを破壊|破壊。$"],
        "全体ダメージ": [r"(すべて|すべてに).+ダメージ"],
        "疾走": [r"【疾走】"],
        "守護付与": [r"【守護】を持つ|は【守護】"],
        "ラストワードでトークン or カード追加": [r"【ラストワード】.*(手札に加える|場に出す)"],
        "進化時トークン生成": [r"【進化時】.*場に出す"],
        "デッキサーチ": [r"デッキから[0-9一二三四五六七八九]*枚?を引く.*(加える)?"],  # approximates draw/search
        "手札を捨てる・入替": [r"捨てる|デッキに戻す"],
        "コスト軽減": [r"コスト.*(減らす|-\d)"],
        "カウントダウン進める": [r"カウントを-1"],
        "守護を失わせる": [r"守護.*失う"],
    }


def match_card(effects: str, pattern_groups: List[str]) -> bool:
    for pat in pattern_groups:
        if not re.search(pat, effects):
            return False
    return True


def main():  # noqa: D401
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries-file", default="data/eval/relevance_labels.json")
    parser.add_argument("--data-file", default="data/data.json")
    parser.add_argument("--min-per-query", type=int, default=3)
    parser.add_argument("--max-per-query", type=int, default=8)
    args = parser.parse_args()

    cards = load_cards(args.data_file)
    queries = load_queries(args.queries_file)
    patterns = build_patterns()

    # Precompute effect text per card
    card_effects = []
    for c in cards:
        eff = extract_effect_text(c)
        if eff:
            card_effects.append((c["name"], eff))

    results = []
    for q in queries:
        query_text = q.get("query")
        pats = patterns.get(query_text)
        candidates: List[str] = []
        if pats:
            for title, eff in card_effects:
                if match_card(eff, pats):
                    candidates.append(title)
                if len(candidates) >= args.max_per_query:
                    break
        # Fallback heuristics for sparse categories
        if len(candidates) < args.min_per_query:
            if query_text == "継続ダメージ":
                # broaden: any effect mentioning ランダム and ダメージ or "ダメージ。" twice
                broad = []
                for title, eff in card_effects:
                    if re.search(r"ランダム", eff) and re.search(r"ダメージ", eff):
                        broad.append(title)
                    if len(broad) >= args.max_per_query:
                        break
                for b in broad:
                    if b not in candidates:
                        candidates.append(b)
            elif query_text == "リーダー直接ダメージ":
                # broaden: any effect healing/damaging leader (contains リーダー) + ダメージ
                for title, eff in card_effects:
                    if re.search(r"リーダー", eff) and re.search(r"ダメージ", eff):
                        if title not in candidates:
                            candidates.append(title)
                        if len(candidates) >= args.max_per_query:
                            break
        results.append({
            "query": query_text,
            "relevant": candidates[: args.max_per_query],
            "auto_labeled": True,
            "note": ("AUTO-GENERATED; PLEASE REVIEW")
        })

    print(json.dumps({"queries": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
