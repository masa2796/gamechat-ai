import os
import json

def convert_to_embedding_format(card_data):
    entries = []
    base_id = card_data["id"]

    # 1. フレーバー
    if "flavor" in card_data:
        entries.append({
            "id": f"{base_id}:flavor",
            "namespace": "flavor",
            "text": card_data["flavor"]
        })

    # 2. 攻撃
    for idx, attack in enumerate(card_data.get("attacks", []), 1):
        cost_str = "と".join([f"{k}{v}つ" for k, v in attack.get("cost", {}).items()])
        attack_text = f"技名は{attack['name']}。ダメージは{attack['damage']}。必要なエネルギーコストは{cost_str}。"
        entries.append({
            "id": f"{base_id}:attack-{idx}",
            "namespace": "attacks",
            "text": attack_text
        })

    # 3. 概要
    evolves_to = card_data.get("evolvesTo", "なし")
    if isinstance(evolves_to, list):
        evolves_to_str = "と".join(evolves_to)
    else:
        evolves_to_str = evolves_to    
    summary_text = (
        f"{card_data.get('name', '')}は{card_data.get('type', '')}タイプの{card_data.get('species', '')}。"
        f"進化先は{evolves_to_str}。"
        f"弱点は{card_data.get('weakness', '-')}。"
        f"HPは{card_data.get('hp', '-')}。"
        f"身長{card_data.get('height', '-')}m、体重{card_data.get('weight', '-')}kg。"
    )
    entries.append({
        "id": f"{base_id}:summary",
        "namespace": "summary",
        "text": summary_text
    })

    # 4. セット情報
    set_data = card_data.get("set")
    if set_data:
        set_text = f"このカードは「{set_data.get('name', '')}（{set_data.get('subName', '')}）」セットに属し、{set_data.get('releaseDate', '')}に発売された。"
        entries.append({
            "id": f"{base_id}:set-info",
            "namespace": "set-info",
            "text": set_text
        })
        
    # 5. メタデータ: category / evolvesTo / rarity
    category = card_data.get("category", "")
    rarity = card_data.get("rarity", {})
    rarity_symbol = rarity.get("symbol", "")
    rarity_level = rarity.get("level", "")

    meta_text_parts = []
    if category:
        meta_text_parts.append(f"このカードは{category}カテゴリに属し")
    if rarity_symbol or rarity_level:
        meta_text_parts.append(f"レアリティは{rarity_symbol}（レベル{rarity_level}）")

    if meta_text_parts:
        meta_text = "、".join(meta_text_parts) + "。"
        entries.append({
            "id": f"{base_id}:metadata",
            "namespace": "metadata",
            "text": meta_text
        })

    return entries

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    sample_path = os.path.join(data_dir, 'data.json')
    out_path = os.path.join(data_dir, 'convert_data.json')

    with open(sample_path, "r", encoding="utf-8") as f:
        card_list = json.load(f)

    embedding_data = []
    for card in card_list:
        embedding_data.extend(convert_to_embedding_format(card))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(embedding_data, f, ensure_ascii=False, indent=2)

    print(f"{out_path} に出力しました。")
