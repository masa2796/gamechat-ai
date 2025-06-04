import os
import json

def convert_to_embedding_format(card_data):
    entries = []
    base_id = card_data["id"]
    card_name = card_data["name"]

    # フレーバー
    if "flavor" in card_data:
        entries.append({
            "id": f"{base_id}:flavor",
            "namespace": "flavor",
            "text": f"{card_name}のフレーバーテキストは、「{card_data["flavor"]}」"
        })

    # 攻撃
    for idx, attack in enumerate(card_data.get("attacks", []), 1):
        cost_str = "と".join([f"{k}{v}つ" for k, v in attack.get("cost", {}).items()])
        attack_text = f"{card_name}は、{attack['name']}を持ち。ダメージは{attack['damage']}。必要なエネルギーコストは{cost_str}。"
        entries.append({
            "id": f"{base_id}:attack-{idx}",
            "namespace": "attacks",
            "text": attack_text
        })

    # 身長
    entries.append({
        "id": f"{base_id}:height",
        "namespace": "height",
        "text": f"{card_name}の身長は、{card_data.get('height', '-')}mです。"
    })

    # 体重
    entries.append({
        "id": f"{base_id}:weight",
        "namespace": "weight",
        "text": f"{card_name}の体重は、{card_data.get('weight', '-')}kgです。"
    })    
    
    # 進化先
    evolves_to = card_data.get("evolvesTo", "なし")
    if isinstance(evolves_to, list):
        evolves_to_str = "と".join(evolves_to)
    else:
        evolves_to_str = evolves_to            
    entries.append({
        "id": f"{base_id}:evolves",
        "namespace": "evolves",
        "text": f"{card_name}の進化先は、{evolves_to_str}です。"
    })    
    
    # HP
    entries.append({
        "id": f"{base_id}:hp",
        "namespace": "hp",
        "text": f"{card_name}のHPは、{card_data.get('hp', '-')}です。"
    })    
    
    # 弱点
    entries.append({
        "id": f"{base_id}:weakness",
        "namespace": "weakness",
        "text": f"{card_name}の弱点は、{card_data.get('weakness', '-')}です。"
    })    
    
    # タイプ
    entries.append({
        "id": f"{base_id}:type",
        "namespace": "type",
        "text": f"{card_name}は、{card_data.get('name', '')}は{card_data.get('type', '')}タイプの{card_data.get('species', '')}。"
    })    

    # セット情報
    set_data = card_data.get("set")
    if set_data:
        set_text = f"{card_name}は、「{set_data.get('name', '')}（{set_data.get('subName', '')}）」セットに属する。"
        entries.append({
            "id": f"{base_id}:set-info",
            "namespace": "set-info",
            "text": set_text
        })
        
    # 発売日
    if set_data:
        set_text = f"{card_name}は、{set_data.get('releaseDate', '')}に発売された。"
        entries.append({
            "id": f"{base_id}:releaseDate",
            "namespace": "releaseDate",
            "text": set_text
        })        
        
    # カテゴリ
    category = card_data.get("category", "")
    if category:
        category_text = f"{card_name}は、{category}カテゴリに属する。"        
    if category_text:
        entries.append({
            "id": f"{base_id}:category",
            "namespace": "category",
            "text": category_text
        })

    # レアリティ
    rarity = card_data.get("rarity", {})
    rarity_symbol = rarity.get("symbol", "")
    rarity_level = rarity.get("level", "")
    if rarity_symbol or rarity_level:
        rarity_text_parts = f"{card_name}のレアリティは、{rarity_symbol}（レベル{rarity_level}）"
    if rarity_text_parts:
        entries.append({
            "id": f"{base_id}:rarity",
            "namespace": "rarity",
            "text": rarity_text_parts
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
