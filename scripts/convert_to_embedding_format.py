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
    for attack in card_data.get("attacks", []):
        cost_str = " ".join([f"{k}{v}" for k, v in attack.get("cost", {}).items()])
        attack_text = f"技名: {attack['name']} / ダメージ: {attack['damage']} / エネルギーコスト: {cost_str}"
        entries.append({
            "id": f"{base_id}:attack:{attack['name']}",
            "namespace": "attacks",
            "text": attack_text
        })

    # 3. 概要（種族、タイプ、弱点、HPなど）
    summary_text = (
        f"{card_data['name']}は{card_data['type']}タイプの{card_data['species']}。"
        f"進化先は{card_data['evolvesTo']}。"
        f"弱点は{card_data['weakness']}。"
        f"HPは{card_data['hp']}。"
        f"身長{card_data['height']}m、体重{card_data['weight']}kg。"
    )
    entries.append({
        "id": f"{base_id}:summary",
        "namespace": "summary",
        "text": summary_text
    })

    # 4. セット情報
    set_data = card_data.get("set")
    if set_data:
        set_text = f"このカードは「{set_data['name']}（{set_data['subName']}）」セットに属し、{set_data['releaseDate']}に発売された。"
        entries.append({
            "id": f"{base_id}:set-info",
            "namespace": "set-info",
            "text": set_text
        })
        
    # 5. メタデータ: category / evolvesTo / rarity
    category = card_data.get("category", "")
    evolves_to = card_data.get("evolvesTo", "")
    rarity = card_data.get("rarity", {})
    rarity_symbol = rarity.get("symbol", "")
    rarity_level = rarity.get("level", "")

    meta_text_parts = []
    if category:
        meta_text_parts.append(f"このカードは{category}カテゴリに属し")
    if evolves_to:
        meta_text_parts.append(f"進化先は{evolves_to}")
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
    sample_path = os.path.join(data_dir, 'sample_data.json')
    out_path = os.path.join(data_dir, 'embedding_data.json')

    with open(sample_path, "r", encoding="utf-8") as f:
        card_json = json.load(f)

    embedding_data = convert_to_embedding_format(card_json)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(embedding_data, f, ensure_ascii=False, indent=2)

    print(f"embedding_data.json を {out_path} に出力しました。")
