import os
import json
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# プロジェクトルートディレクトリを取得
project_root = Path(__file__).resolve().parent.parent.parent
dotenv_path = project_root / 'backend' / '.env'
load_dotenv(dotenv_path=dotenv_path)

def convert_to_namespace_grouped(card_data):
    grouped = defaultdict(list)
    base_id = card_data.get("id", "")
    card_name = card_data.get("name", "")

    # effect_1, effect_2, ...
    for key in card_data.keys():
        if key.startswith("effect_") and card_data[key]:
            grouped[key].append({
                "id": f"{base_id}:{key}",
                "text": f"{card_name}の効果は、「{card_data[key]}」"
            })

    # Q&A
    if "qa" in card_data and isinstance(card_data["qa"], list):
        for idx, qa_item in enumerate(card_data["qa"], 1):
            if "question" in qa_item and qa_item["question"]:
                grouped["qa_question"].append({
                    "id": f"{base_id}:qa_question_{idx}",
                    "text": f"Q{idx}: {qa_item['question']}"
                })

    # flavorText
    if "flavorText" in card_data and card_data["flavorText"]:
        grouped["flavorText"].append({
            "id": f"{base_id}:flavorText",
            "text": f"{card_name}のフレーバーテキストは、「{card_data['flavorText']}」"
        })

    return grouped

if __name__ == "__main__":
    sample_path = os.getenv("DATA_FILE_PATH", str(project_root / 'data' / 'data.json'))
    out_path = os.getenv("CONVERTED_DATA_FILE_PATH", str(project_root / 'data' / 'convert_data.json'))

    with open(sample_path, "r", encoding="utf-8") as f:
        card_list = json.load(f)

    # namespaceごとにまとめず、フラットなリスト形式で出力
    embedding_data = []
    for card in card_list:
        card_grouped = convert_to_namespace_grouped(card)
        for ns, items in card_grouped.items():
            for item in items:
                # namespace情報をitemに付与
                item["namespace"] = ns
                embedding_data.append(item)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(embedding_data, f, ensure_ascii=False, indent=2)

    print(f"{out_path} にフラットなリスト形式で出力しました。")
