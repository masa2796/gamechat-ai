#!/usr/bin/env python3
"""ARCHIVE_CANDIDATE: 監査用の解析スクリプト（MVPでは未使用）。

Analyze namespace distribution from vector_index_effects.jsonl (and convert_data.json fallback).
Print counts per namespace and list namespaces missing vs expected pattern effect_1..effect_9, qa_question, qa_answer, flavorText, effect_combined.
"""
from __future__ import annotations
import os
import sys
import json
import collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.append(ROOT)

def iter_lines(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            yield line

def collect_namespaces() -> dict[str,int]:
    data_dir = os.path.join(ROOT, 'data')
    counts: dict[str,int] = collections.Counter()
    audit = os.path.join(data_dir, 'vector_index_effects.jsonl')
    if os.path.exists(audit):
        for line in iter_lines(audit):
            try:
                obj = json.loads(line)
                ns = obj.get('namespace')
                if ns:
                    counts[ns]+=1
            except Exception:
                continue
    convert_path = os.path.join(data_dir, 'convert_data.json')
    if os.path.exists(convert_path):
        # detect json array vs jsonl
        with open(convert_path,'r',encoding='utf-8') as f:
            head = f.read(1024)
        if head.lstrip().startswith('['):
            try:
                data = json.loads(open(convert_path,'r',encoding='utf-8').read())
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            ns=item.get('namespace')
                            if ns:
                                counts[ns]+=1
            except Exception:
                pass
        else:
            for line in iter_lines(convert_path):
                try:
                    obj=json.loads(line)
                    ns=obj.get('namespace')
                    if ns:
                        counts[ns]+=1
                except Exception:
                    continue
    return dict(counts)

def main():
    counts = collect_namespaces()
    if not counts:
        print('No namespaces found.')
        return
    print(f"Total namespaces discovered: {len(counts)}")
    for ns,c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{ns}: {c}")
    expected = [f"effect_{i}" for i in range(1,10)] + ["qa_question","qa_answer","flavorText","effect_combined"]
    missing = [ns for ns in expected if ns not in counts]
    if missing:
        print("\nMissing (expected but not present):", ', '.join(missing))
    else:
        print("\nAll expected namespaces present.")

if __name__ == '__main__':
    main()
