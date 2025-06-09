from typing import List, Dict, Any
import json
from ..models.rag_models import ContextItem

class DatabaseService:
    """通常のデータベース検索サービス（構造化データのフィルタリング）"""
    
    def __init__(self):
        # データファイルのパスを設定
        self.data_path = "/Users/masaki/Documents/gamechat-ai/data/data.json"
        self.converted_data_path = "/Users/masaki/Documents/gamechat-ai/data/convert_data.json"
        self.cache = None
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """データファイルを読み込む"""
        if self.cache is not None:
            return self.cache
        
        try:
            # data.jsonを優先して使用（構造化データ）
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
                return self.cache
        except FileNotFoundError:
            try:
                # フォールバックでconvert_data.jsonを使用
                with open(self.converted_data_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                    return self.cache
            except FileNotFoundError:
                print("データファイルが見つかりません")
                return []
        except Exception as e:
            print(f"データ読み込みエラー: {e}")
            return []
    
    async def filter_search(self, filter_keywords: List[str], top_k: int = 50) -> List[ContextItem]:
        """フィルターキーワードに基づいて構造化検索を実行"""
        try:
            data = self._load_data()
            if not data:
                return self._get_fallback_results()
            
            print("=== データベースフィルター検索 ===")
            print(f"検索キーワード: {filter_keywords}")
            print(f"総データ件数: {len(data)}")
            
            filtered_results = []
            
            for item in data:
                score = self._calculate_filter_score(item, filter_keywords)
                if score > 0:
                    title = self._extract_title(item)
                    text = self._extract_text(item)
                    
                    filtered_results.append({
                        "title": title,
                        "text": text,
                        "score": score,
                        "item": item
                    })
            
            # スコアでソートして上位を返す
            filtered_results.sort(key=lambda x: x["score"], reverse=True)
            
            print(f"フィルター結果: {len(filtered_results)}件")
            
            return [
                ContextItem(
                    title=result["title"],
                    text=result["text"],
                    score=result["score"]
                )
                for result in filtered_results[:top_k]
            ]
            
        except Exception as e:
            print(f"データベース検索エラー: {e}")
            return self._get_fallback_results()

    def _calculate_filter_score(self, item: Dict[str, Any], keywords: List[str]) -> float:
        """アイテムとキーワードのマッチスコアを計算"""
        if not keywords:
            return 0.0

        score = 0.0
        total_conditions = 0
        
        # アイテムの全テキストを結合
        searchable_text = ""
        
        # 一般的なフィールドをチェック
        text_fields = ["name", "title", "type", "category", "rarity", "series", "species", "stage"]
        
        for field in text_fields:
            if field in item and item[field]:
                if isinstance(item[field], str):
                    searchable_text += f" {item[field]}"
                elif isinstance(item[field], list):
                    searchable_text += f" {' '.join(str(x) for x in item[field])}"
                elif isinstance(item[field], dict):
                    searchable_text += f" {' '.join(str(v) for v in item[field].values())}"
        
        searchable_text_lower = searchable_text.lower()
        
        # 条件別スコア計算
        type_matched = False
        damage_matched = False
        hp_matched = False
        
        print(f"  評価中: {item.get('name', 'Unknown')} (タイプ: {item.get('type', 'Unknown')})")
        
        # HPキーワードと数値条件の組み合わせをチェック
        has_hp_keyword = any("hp" in kw.lower() for kw in keywords)
        has_hp_condition = any(cond in ' '.join(keywords).lower() for cond in ["40以上", "50以上", "100以上", "150以上"])
        
        if has_hp_keyword and has_hp_condition:
            total_conditions += 1
            try:
                hp_value = int(item["hp"]) if "hp" in item and item["hp"] else 0
                # 数値条件を確認
                for kw in keywords:
                    if "40以上" in kw.lower() and hp_value >= 40:
                        score += 2.0
                        hp_matched = True
                        print(f"    HPマッチ: {hp_value} >= 40 -> +2.0")
                        break
                    elif "50以上" in kw.lower() and hp_value >= 50:
                        score += 2.0
                        hp_matched = True
                        print(f"    HPマッチ: {hp_value} >= 50 -> +2.0")
                        break
                    elif "100以上" in kw.lower() and hp_value >= 100:
                        score += 2.0
                        hp_matched = True
                        print(f"    HPマッチ: {hp_value} >= 100 -> +2.0")
                        break
                    elif "150以上" in kw.lower() and hp_value >= 150:
                        score += 2.0
                        hp_matched = True
                        print(f"    HPマッチ: {hp_value} >= 150 -> +2.0")
                        break
            except (ValueError, TypeError):
                pass
        
        # ダメージキーワードと数値条件の組み合わせをチェック  
        has_damage_keyword = any(kw.lower() in ["ダメージ", "技", "攻撃"] for kw in keywords)
        has_damage_condition = any(cond in ' '.join(keywords).lower() for cond in ["30以上", "40以上", "50以上", "60以上"])
        
        if has_damage_keyword and has_damage_condition and not hp_matched:
            total_conditions += 1
            if "attacks" in item and item["attacks"]:
                for attack in item["attacks"]:
                    if isinstance(attack, dict) and "damage" in attack:
                        try:
                            damage_value = int(attack["damage"]) if attack["damage"] else 0
                            # 数値条件を確認
                            for kw in keywords:
                                if "30以上" in kw.lower() and damage_value >= 30:
                                    score += 2.0
                                    damage_matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 30 -> +2.0")
                                    break
                                elif "40以上" in kw.lower() and damage_value >= 40:
                                    score += 2.0
                                    damage_matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 40 -> +2.0")
                                    break
                                elif "50以上" in kw.lower() and damage_value >= 50:
                                    score += 2.0
                                    damage_matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 50 -> +2.0")
                                    break
                                elif "60以上" in kw.lower() and damage_value >= 60:
                                    score += 2.0
                                    damage_matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 60 -> +2.0")
                                    break
                            if damage_matched:
                                break
                        except (ValueError, TypeError):
                            pass
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # タイプ関連の処理
            if keyword_lower in ["炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"]:
                if not type_matched:  # 重複チェックを追加
                    total_conditions += 1
                    if "type" in item and item["type"]:
                        if keyword_lower == item["type"].lower():
                            score += 2.0
                            type_matched = True
                            print(f"    タイプマッチ: {keyword} -> +2.0")
            
            # 一般的なテキストマッチング（低いスコア、HP・ダメージ・タイプ以外）
            elif (keyword_lower not in ["hp", "40以上", "50以上", "100以上", "150以上", "30以上", "60以上", "ダメージ", "技", "攻撃", "タイプ"] and 
                  keyword_lower in searchable_text_lower):
                score += 0.5
                print(f"    テキストマッチ: {keyword} -> +0.5")
            # 部分マッチも考慮
            elif (keyword_lower not in ["hp", "40以上", "50以上", "100以上", "150以上", "30以上", "60以上", "ダメージ", "技", "攻撃", "タイプ"] and
                  any(keyword_lower in word for word in searchable_text_lower.split())):
                score += 0.3
                print(f"    部分マッチ: {keyword} -> +0.3")
        
        # 複合条件の場合、両方の条件を満たした場合にボーナス
        if type_matched and (damage_matched or hp_matched):
            score += 1.0
            print("    複合条件ボーナス: +1.0")
        
        print(f"    最終スコア: {score}")
        
        # スコアを正規化
        return score
    
    def _extract_title(self, item: Dict[str, Any]) -> str:
        """アイテムからタイトルを抽出"""
        for field in ["name", "title", "cardName"]:
            if field in item and item[field]:
                return str(item[field])
        return "不明なアイテム"
    
    def _extract_text(self, item: Dict[str, Any]) -> str:
        """アイテムから検索可能テキストを抽出"""
        text_parts = []
        
        # 主要情報を結合
        if "type" in item:
            text_parts.append(f"タイプ: {item['type']}")
        if "hp" in item:
            text_parts.append(f"HP: {item['hp']}")
        if "species" in item:
            text_parts.append(f"種類: {item['species']}")
        if "stage" in item:
            text_parts.append(f"進化段階: {item['stage']}")
        if "attacks" in item and isinstance(item["attacks"], list):
            attack_names = [attack.get("name", "") for attack in item["attacks"] if isinstance(attack, dict)]
            if attack_names:
                text_parts.append(f"わざ: {', '.join(attack_names)}")
        if "weakness" in item:
            text_parts.append(f"弱点: {item['weakness']}")
        if "resistance" in item:
            text_parts.append(f"抵抗力: {item['resistance']}")
        if "rarity" in item:
            text_parts.append(f"レアリティ: {item['rarity']}")
        
        return " / ".join(text_parts) if text_parts else str(item)
    
    def _get_fallback_results(self) -> List[ContextItem]:
        """フォールバック用のダミーデータ"""
        return [
            ContextItem(
                title="データベース検索 - フィルター結果",
                text="データベースからの検索結果です。具体的な条件に基づいてフィルタリングされています。",
                score=0.8
            )
        ]
