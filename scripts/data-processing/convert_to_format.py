import os
import json
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートディレクトリを取得
project_root = Path(__file__).parent.parent
dotenv_path = project_root / 'backend' / '.env'  # backend/.envのみ参照
load_dotenv(dotenv_path=dotenv_path)

def convert_to_embedding_format(card_data):
    entries = []
    base_id = card_data.get("id", "")
    card_name = card_data.get("name", "")

    # effect_1, effect_2, ...
    for key in card_data.keys():
        if key.startswith("effect_") and card_data[key]:
            entries.append({
                "id": f"{base_id}:{key}",
                "namespace": key,
                "text": f"{card_name}の{key}は、「{card_data[key]}」"
            })

    # Q&A
    if "qa" in card_data and isinstance(card_data["qa"], list):
        for idx, qa_item in enumerate(card_data["qa"], 1):
            if "question" in qa_item and qa_item["question"]:
                entries.append({
                    "id": f"{base_id}:qa_question_{idx}",
                    "namespace": "qa_question",
                    "text": f"Q{idx}: {qa_item['question']}"
                })
            if "answer" in qa_item and qa_item["answer"]:
                entries.append({
                    "id": f"{base_id}:qa_answer_{idx}",
                    "namespace": "qa_answer",
                    "text": f"A{idx}: {qa_item['answer']}"
                })

    # flavorText
    if "flavorText" in card_data and card_data["flavorText"]:
        entries.append({
            "id": f"{base_id}:flavorText",
            "namespace": "flavorText",
            "text": f"{card_name}のフレーバーテキストは、「{card_data['flavorText']}」"
        })

    return entries


if __name__ == "__main__":
    # 環境変数からパスを取得、なければデフォルトパスを使用
    sample_path = os.getenv("DATA_FILE_PATH", str(project_root / 'data' / 'data.json'))
    out_path = os.getenv("CONVERTED_DATA_FILE_PATH", str(project_root / 'data' / 'convert_data.json'))

    with open(sample_path, "r", encoding="utf-8") as f:
        card_list = json.load(f)

    embedding_data = []
    for card in card_list:
        embedding_data.extend(convert_to_embedding_format(card))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(embedding_data, f, ensure_ascii=False, indent=2)

    print(f"{out_path} に出力しました。")
