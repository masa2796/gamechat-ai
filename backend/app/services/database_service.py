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
    
    async def filter_search(self, filter_keywords: List[str], top_k: int = 3) -> List[ContextItem]:
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
        total_keywords = len(keywords)
        
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
        
        # 数値フィールドの特別処理
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # HP関連の処理
            if "hp" in keyword_lower or keyword_lower == "hp":
                try:
                    hp_value = int(item["hp"]) if "hp" in item and item["hp"] else 0
                    # 他のキーワードで数値条件をチェック
                    for other_keyword in keywords:
                        if "100以上" in other_keyword or ("100" in other_keyword and "以上" in keywords):
                            if hp_value >= 100:
                                score += 2.0  # 数値条件マッチは高スコア
                        elif "150以上" in other_keyword:
                            if hp_value >= 150:
                                score += 2.0
                        elif "50以上" in other_keyword:
                            if hp_value >= 50:
                                score += 2.0
                except (ValueError, TypeError):
                    pass
            
            # 数値条件の直接処理
            if "100以上" in keyword_lower:
                try:
                    hp_value = int(item["hp"]) if "hp" in item and item["hp"] else 0
                    if hp_value >= 100:
                        score += 2.0
                except (ValueError, TypeError):
                    pass
            
            # タイプ関連の処理
            if keyword_lower in ["炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"]:
                if "type" in item and item["type"]:
                    if keyword_lower == item["type"].lower():
                        score += 2.0
            
            # 一般的なテキストマッチング
            searchable_text_lower = searchable_text.lower()
            if keyword_lower in searchable_text_lower:
                score += 1.0
            # 部分マッチも考慮
            elif any(keyword_lower in word for word in searchable_text_lower.split()):
                score += 0.5
        
        # 正規化（0.0-1.0の範囲）
        return min(score / total_keywords, 1.0)
    
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
