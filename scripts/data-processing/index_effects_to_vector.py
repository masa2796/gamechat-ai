"""ARCHIVE_CANDIDATE: 高度なインデックス作成スクリプト（MVPでは未使用）。"""

import os
import re
import json
import time
import argparse
from dataclasses import dataclass
from typing import Dict, List, Iterable, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from upstash_vector import Index, Vector
import openai


project_root = Path(__file__).resolve().parent.parent.parent
backend_env_path = project_root / 'backend' / '.env'


def load_env() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Load environment variables from backend/.env for OpenAI and Upstash."""
    load_dotenv(dotenv_path=backend_env_path, override=True)
    openai_key = os.getenv("BACKEND_OPENAI_API_KEY")
    upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
    upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    return openai_key, upstash_url, upstash_token


def normalize_text(text: str) -> str:
    """Light normalization: collapse whitespace, unify quotes, strip."""
    if not text:
        return ""
    # unify quotes
    t = text.replace('“', '"').replace('”', '"').replace("’", "'")
    # collapse whitespace
    t = re.sub(r"\s+", " ", t, flags=re.MULTILINE).strip()
    return t


def build_combined_text(card: Dict) -> str:
    """Mimic EmbeddingService.extract_embedding_text: effect_1..9, qa.q/a, flavorText."""
    texts: List[str] = []
    # effect_i
    for i in range(1, 10):
        key = f"effect_{i}"
        if key in card and card[key]:
            texts.append(str(card[key]))
    # QA
    if isinstance(card.get("qa"), list):
        for idx, qa in enumerate(card["qa"], 1):
            q = qa.get("question")
            a = qa.get("answer")
            if q:
                texts.append(str(q))
            if a:
                texts.append(str(a))
    # flavorText
    if card.get("flavorText"):
        texts.append(str(card["flavorText"]))
    return "\n".join([normalize_text(t) for t in texts if t])


@dataclass
class Record:
    id: str
    namespace: str
    title: str
    text: str
    card_id: str
    source: str  # effect|qa|flavor|combined


def iter_records_from_card(card: Dict, include_combined: bool, namespace_filter: Optional[set]) -> Iterable[Record]:
    card_id = str(card.get("id", ""))
    title = str(card.get("name", ""))

    # effect_i fragments
    for i in range(1, 10):
        key = f"effect_{i}"
        val = card.get(key)
        if val:
            ns = key
            if namespace_filter and ns not in namespace_filter:
                pass
            else:
                yield Record(
                    id=f"{card_id}:{key}",
                    namespace=ns,
                    title=title,
                    text=normalize_text(str(val)),
                    card_id=card_id,
                    source="effect",
                )

    # QA question/answer fragments
    qa_list = card.get("qa")
    if isinstance(qa_list, list) and qa_list:
        for idx, qa in enumerate(qa_list, 1):
            q = qa.get("question")
            a = qa.get("answer")
            if q:
                ns = "qa_question"
                if not namespace_filter or ns in namespace_filter:
                    yield Record(
                        id=f"{card_id}:qa_question_{idx}",
                        namespace=ns,
                        title=title,
                        text=normalize_text(str(q)),
                        card_id=card_id,
                        source="qa",
                    )
            if a:
                ns = "qa_answer"
                if not namespace_filter or ns in namespace_filter:
                    yield Record(
                        id=f"{card_id}:qa_answer_{idx}",
                        namespace=ns,
                        title=title,
                        text=normalize_text(str(a)),
                        card_id=card_id,
                        source="qa",
                    )

    # flavorText fragment (if any)
    if card.get("flavorText"):
        ns = "flavorText"
        if not namespace_filter or ns in namespace_filter:
            yield Record(
                id=f"{card_id}:flavorText",
                namespace=ns,
                title=title,
                text=normalize_text(str(card["flavorText"])),
                card_id=card_id,
                source="flavor",
            )

    # combined (optional)
    if include_combined:
        ns = "effect_combined"
        if not namespace_filter or ns in namespace_filter:
            combined = build_combined_text(card)
            if combined:
                yield Record(
                    id=f"{card_id}:effect_combined",
                    namespace=ns,
                    title=title,
                    text=combined,
                    card_id=card_id,
                    source="combined",
                )


def embed_text(text: str) -> List[float]:
    # Use same pattern as existing scripts for compatibility
    resp = openai.embeddings.create(input=text, model="text-embedding-3-small")
    return resp.data[0].embedding


def upsert_with_retry(index: Index, namespace: str, rec_id: str, vector: List[float], metadata: Dict, retries: int = 3) -> bool:
    backoff = 1.0
    for attempt in range(retries):
        try:
            index.upsert(vectors=[Vector(id=rec_id, vector=vector, metadata=metadata)], namespace=namespace)
            return True
        except Exception as e:
            if attempt == retries - 1:
                print(f"[Upstash][FAIL] id={rec_id} ns={namespace}: {e}")
                return False
            time.sleep(backoff)
            backoff *= 2
    return False


def main():
    parser = argparse.ArgumentParser(description="Index card effects to Upstash Vector")
    parser.add_argument("--dry-run", action="store_true", help="Don't upsert to Upstash; only write audit JSONL")
    # combined は Recall 改善のためデフォルト有効。無効化したい場合のみ --no-combined を指定。
    parser.add_argument("--no-combined", action="store_true", help="Do NOT index combined text (effect_combined) per card")
    parser.add_argument("--namespaces", type=str, default="", help="Comma-separated namespace filter (e.g., effect_1,qa_question)")
    parser.add_argument("--limit", type=int, default=0, help="Max number of cards to process (0=all)")
    parser.add_argument("--skip-embed", action="store_true", help="Do not call embedding API (text_len 0以外でも upsert せず高速監査用)")
    parser.add_argument("--output", type=str, default=str(project_root / 'data' / 'vector_index_effects.jsonl'), help="Audit JSONL output path")
    parser.add_argument("--stats-json", type=str, default="", help="Write field coverage stats to this JSON file")
    args = parser.parse_args()

    openai_key, upstash_url, upstash_token = load_env()
    if not openai_key:
        print("Error: BACKEND_OPENAI_API_KEY missing in backend/.env")
        return
    openai.api_key = openai_key

    index: Optional[Index] = None
    if not args.dry_run:
        if not upstash_url or not upstash_token:
            print("Error: UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN missing in backend/.env")
            return
        index = Index(url=upstash_url, token=upstash_token)

    data_path = project_root / 'data' / 'data.json'
    if not data_path.exists():
        print(f"Error: 入力ファイルが存在しません: {data_path}")
        return

    with open(data_path, encoding='utf-8') as f:
        cards: List[Dict] = json.load(f)

    ns_filter = None
    if args.namespaces:
        ns_filter = set([s.strip() for s in args.namespaces.split(',') if s.strip()])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # overwrite file to avoid uncontrolled growth
    with open(out_path, 'w', encoding='utf-8') as audit_f:
        pass

    processed_cards = 0
    total_records = 0
    ns_counts: Dict[str, int] = {}
    # coverage counters
    coverage = {
        "cards_total": 0,
        "with_name": 0,
        "with_flavorText": 0,
        "with_qa": 0,
        "qa_questions": 0,
        "qa_answers": 0,
        "effects_present": {f"effect_{i}": 0 for i in range(1,10)},
        "missing_name_samples": [],
        "missing_effect_1_samples": [],
    }

    include_combined = not args.no_combined

    for card in cards:
        if args.limit and processed_cards >= args.limit:
            break
        coverage["cards_total"] += 1
        name = card.get("name")
        if name:
            coverage["with_name"] += 1
        else:
            if len(coverage["missing_name_samples"]) < 5:
                coverage["missing_name_samples"].append(card.get("id"))
        # effects coverage
        has_effect1 = False
        for i in range(1,10):
            key = f"effect_{i}"
            if card.get(key):
                coverage["effects_present"][key] += 1
                if i == 1:
                    has_effect1 = True
        if not has_effect1 and len(coverage["missing_effect_1_samples"]) < 5:
            coverage["missing_effect_1_samples"].append(card.get("id"))
        # qa coverage
        qa_list = card.get("qa")
        if isinstance(qa_list, list) and qa_list:
            coverage["with_qa"] += 1
            for qa in qa_list:
                if qa.get("question"):
                    coverage["qa_questions"] += 1
                if qa.get("answer"):
                    coverage["qa_answers"] += 1
        if card.get("flavorText"):
            coverage["with_flavorText"] += 1
        records = list(iter_records_from_card(card, include_combined=include_combined, namespace_filter=ns_filter))
        if not records:
            processed_cards += 1
            continue
        for rec in records:
            if not rec.text:
                # skip empty
                audit = {
                    "id": rec.id,
                    "namespace": rec.namespace,
                    "title": rec.title,
                    "text_len": 0,
                    "upserted": False,
                    "skipped_reason": "empty_text",
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                with open(out_path, 'a', encoding='utf-8') as audit_f:
                    audit_f.write(json.dumps(audit, ensure_ascii=False) + "\n")
                continue

            if args.skip_embed:
                vec = None  # type: ignore
            else:
                try:
                    vec = embed_text(rec.text)
                except Exception as e:
                    audit = {
                        "id": rec.id,
                        "namespace": rec.namespace,
                        "title": rec.title,
                        "text_len": len(rec.text),
                        "upserted": False,
                        "skipped_reason": f"embed_error: {e}",
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    with open(out_path, 'a', encoding='utf-8') as audit_f:
                        audit_f.write(json.dumps(audit, ensure_ascii=False) + "\n")
                    continue

            metadata = {
                "title": rec.title,
                "text": rec.text,
                "namespace": rec.namespace,
                "card_id": rec.card_id,
                "source": rec.source,
            }

            ok = True
            if index is not None and (not args.skip_embed) and vec is not None:
                ok = upsert_with_retry(index, rec.namespace, rec.id, vec, metadata)

            audit = {
                "id": rec.id,
                "namespace": rec.namespace,
                "title": rec.title,
                "text_len": len(rec.text),
                "upserted": bool(ok and index is not None),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            with open(out_path, 'a', encoding='utf-8') as audit_f:
                audit_f.write(json.dumps(audit, ensure_ascii=False) + "\n")

            ns_counts[rec.namespace] = ns_counts.get(rec.namespace, 0) + 1
            total_records += 1

        processed_cards += 1

    # Summary
    print("=== Indexing Summary ===")
    print(f"cards_processed: {processed_cards}")
    print(f"records_generated: {total_records}")
    for ns, cnt in sorted(ns_counts.items()):
        print(f"  {ns}: {cnt}")
    print(f"audit_file: {out_path}")
    # coverage summary percentages
    if coverage["cards_total"]:
        def pct(x: int) -> str:
            return f"{(x/coverage['cards_total']*100):.1f}%"
        print("--- Field Coverage ---")
        print(f" name_present: {coverage['with_name']}/{coverage['cards_total']} ({pct(coverage['with_name'])})")
        print(f" flavorText_present: {coverage['with_flavorText']}/{coverage['cards_total']} ({pct(coverage['with_flavorText'])})")
        print(f" qa_present: {coverage['with_qa']}/{coverage['cards_total']} ({pct(coverage['with_qa'])}) questions={coverage['qa_questions']} answers={coverage['qa_answers']}")
        for i in range(1,10):
            key = f"effect_{i}"
            val = coverage['effects_present'][key]
            if val:
                print(f" {key}: {val}/{coverage['cards_total']} ({pct(val)})")
        if coverage['missing_name_samples']:
            print(f" missing_name_sample_ids: {coverage['missing_name_samples']}")
        if coverage['missing_effect_1_samples']:
            print(f" missing_effect_1_sample_ids: {coverage['missing_effect_1_samples']}")
    # write stats json if requested
    if args.stats_json:
        try:
            stats_out = Path(args.stats_json)
            stats_out.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_out, 'w', encoding='utf-8') as sf:
                json.dump(coverage, sf, ensure_ascii=False, indent=2)
            print(f"stats_json: {stats_out}")
        except Exception as e:  # pragma: no cover
            print(f"[WARN] failed writing stats json: {e}")


if __name__ == "__main__":
    main()
