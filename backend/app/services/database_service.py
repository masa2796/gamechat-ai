from typing import List, Dict, Any, Optional
import json
from ..models.rag_models import ContextItem
from ..core.config import settings
from ..core.exceptions import DatabaseException
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger

class DatabaseService:
    """通常のデータベース検索サービス（構造化データのフィルタリング）"""
    
    def __init__(self) -> None:
        # 設定ファイルからデータファイルのパスを取得
        self.data_path = settings.DATA_FILE_PATH
        self.converted_data_path = settings.CONVERTED_DATA_FILE_PATH
        self.cache: Optional[List[Dict[str, Any]]] = None
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """データファイルを読み込む"""
        if self.cache is not None:
            return self.cache
        
        try:
            # data.jsonを優先して使用（構造化データ）
            with open(self.data_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                if not isinstance(loaded_data, list):
                    raise ValueError("Data file must contain a list")
                self.cache = loaded_data
                GameChatLogger.log_success("database_service", f"データファイルを読み込みました: {self.data_path}")
                return self.cache
        except FileNotFoundError:
            try:
                # フォールバックでconvert_data.jsonを使用
                with open(self.converted_data_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if not isinstance(loaded_data, list):
                        raise ValueError("Converted data file must contain a list")
                    self.cache = loaded_data
                    GameChatLogger.log_info("database_service", f"フォールバックファイルを使用: {self.converted_data_path}")
                    return self.cache
            except FileNotFoundError:
                raise DatabaseException(
                    message="データファイルが見つかりません",
                    code="DATA_FILE_NOT_FOUND",
                    details={"data_path": self.data_path, "converted_path": self.converted_data_path}
                )
        except Exception as e:
            raise DatabaseException(
                message="データ読み込みエラー",
                code="DATA_LOAD_ERROR",
                details={"original_error": str(e), "file_path": self.data_path}
            )
    
    @handle_service_exceptions("database", fallback_return=[])
    async def filter_search(self, filter_keywords: List[str], top_k: int = 50) -> List[ContextItem]:
        """
        フィルターキーワードに基づいて構造化検索を実行します。
        
        数値条件（HP、ダメージ）、タイプ、レアリティなどの構造化データに対して
        精密なフィルタリング検索を行い、マッチスコアでランキングされた結果を返します。
        
        Args:
            filter_keywords: フィルタリング用キーワードのリスト
                - 数値条件: ["HP", "100以上"], ["ダメージ", "40以上"]
                - タイプ: ["炎", "タイプ"], ["水", "カード"]
                - レアリティ: ["R", "レア"], ["SR", "スーパーレア"]
            top_k: 返却する最大結果数 (デフォルト: 50)
                
        Returns:
            マッチスコア順にソートされたContextItemのリスト
            各アイテムには title, text, score が含まれます
            
        Raises:
            DatabaseException: データファイルの読み込みに失敗した場合
            ValueError: 不正なキーワード形式が含まれている場合
            
        Examples:
            >>> service = DatabaseService()
            >>> # HP100以上のカードを検索
            >>> results = await service.filter_search(["HP", "100以上"], top_k=10)
            >>> print(f"見つかった件数: {len(results)}")
            >>> print(f"最高スコア: {results[0].score}")
            
            >>> # 複合条件での検索
            >>> results = await service.filter_search(
            ...     ["炎", "タイプ", "ダメージ", "40以上"], top_k=5
            ... )
            >>> # 炎タイプでダメージ40以上の技を持つカードが返される
        """
        data = self._load_data()
        if not data:
            return self._get_fallback_results()
        
        GameChatLogger.log_info("database_service", "データベースフィルター検索を開始", {
            "keywords": filter_keywords,
            "data_count": len(data),
            "top_k": top_k
        })
        
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
        filtered_results.sort(key=lambda x: float(x["score"]) if isinstance(x["score"], (str, int, float)) else 0.0, reverse=True)
        
        GameChatLogger.log_success("database_service", "フィルター検索完了", {
            "results_count": len(filtered_results),
            "returned_count": min(len(filtered_results), top_k)
        })
        
        return [
            ContextItem(
                title=str(result["title"]),
                text=str(result["text"]),
                score=float(result["score"]) if isinstance(result["score"], (str, int, float)) else 0.0
            )
            for result in filtered_results[:top_k]
        ]

    def _calculate_filter_score(
        self, 
        item: Dict[str, Any], 
        keywords: List[str]
    ) -> float:
        """
        アイテムとキーワードのマッチスコアを計算します。
        
        Args:
            item: 評価対象のアイテムデータ
                - name: アイテム名
                - type: タイプ（炎、水など）
                - hp: HP値
                - attacks: 技のリスト
            keywords: 検索キーワードのリスト
                - 数値条件: "40以上", "100以上"など
                - タイプ: "炎", "水"など
                
        Returns:
            0.0-10.0の範囲でのマッチスコア
            - 0.0: マッチなし
            - 2.0: 単一条件マッチ
            - 4.0+: 複合条件マッチ
            
        Raises:
            ValueError: 不正なキーワード形式の場合
            
        Examples:
            >>> service._calculate_filter_score(
            ...     {"name": "リザードン", "type": "炎", "hp": 120},
            ...     ["炎", "タイプ", "HP", "100以上"]
            ... )
            4.0
        """
        if not keywords:
            return 0.0

        print(f"  評価中: {item.get('name', 'Unknown')} (タイプ: {item.get('type', 'Unknown')})")
        
        # 各スコアを計算
        hp_score, hp_matched = self._calculate_hp_score(item, keywords)
        damage_score, damage_matched = self._calculate_damage_score(item, keywords, hp_matched)
        type_score, type_matched = self._calculate_type_score(item, keywords)
        text_score = self._calculate_text_score(item, keywords)
        
        # 複合条件ボーナスを計算
        combo_bonus = self._calculate_combo_bonus(type_matched, damage_matched, hp_matched)
        
        total_score = hp_score + damage_score + type_score + text_score + combo_bonus
        
        print(f"    最終スコア: {total_score}")
        return total_score

    def _calculate_hp_score(self, item: Dict[str, Any], keywords: List[str]) -> tuple[float, bool]:
        """
        HP関連のスコアを計算します。
        
        HPキーワードと数値条件の組み合わせを検出し、
        カードのHP値が条件を満たす場合にスコアを付与します。
        
        Args:
            item: 評価対象のアイテムデータ
                - hp: HP値（整数または文字列）
            keywords: 検索キーワードのリスト
                - HP関連: "hp", "HP", "ヒットポイント"
                - 数値条件: "40以上", "50以上", "100以上", "150以上"
                
        Returns:
            tuple[float, bool]: (スコア, マッチしたかどうか)
            - スコア: 条件を満たす場合は2.0、満たさない場合は0.0
            - マッチフラグ: 他のスコア計算での重複防止用
            
        Examples:
            >>> service = DatabaseService()
            >>> item = {"name": "リザードン", "hp": 120}
            >>> keywords = ["HP", "100以上"]
            >>> score, matched = service._calculate_hp_score(item, keywords)
            >>> print(f"スコア: {score}, マッチ: {matched}")
            スコア: 2.0, マッチ: True
            
            >>> # 条件を満たさない場合
            >>> item = {"name": "ピカチュウ", "hp": 60}
            >>> score, matched = service._calculate_hp_score(item, keywords)
            >>> print(f"スコア: {score}, マッチ: {matched}")
            スコア: 0.0, マッチ: False
            
        Note:
            - HPキーワードと数値条件の両方が必要です
            - HP値が数値変換できない場合は0として扱います
            - 複数の数値条件がある場合、最初にマッチした条件でスコアを決定します
        """
        score = 0.0
        matched = False
        
        # HPキーワードと数値条件の組み合わせをチェック
        has_hp_keyword = any("hp" in kw.lower() for kw in keywords)
        has_hp_condition = any(cond in ' '.join(keywords).lower() for cond in ["40以上", "50以上", "100以上", "150以上"])
        
        if has_hp_keyword and has_hp_condition:
            try:
                hp_value = int(item["hp"]) if "hp" in item and item["hp"] else 0
                # 数値条件を確認
                for kw in keywords:
                    if "40以上" in kw.lower() and hp_value >= 40:
                        score = 2.0
                        matched = True
                        print(f"    HPマッチ: {hp_value} >= 40 -> +2.0")
                        break
                    elif "50以上" in kw.lower() and hp_value >= 50:
                        score = 2.0
                        matched = True
                        print(f"    HPマッチ: {hp_value} >= 50 -> +2.0")
                        break
                    elif "100以上" in kw.lower() and hp_value >= 100:
                        score = 2.0
                        matched = True
                        print(f"    HPマッチ: {hp_value} >= 100 -> +2.0")
                        break
                    elif "150以上" in kw.lower() and hp_value >= 150:
                        score = 2.0
                        matched = True
                        print(f"    HPマッチ: {hp_value} >= 150 -> +2.0")
                        break
            except (ValueError, TypeError):
                pass
        
        return score, matched

    def _calculate_damage_score(self, item: Dict[str, Any], keywords: List[str], hp_matched: bool) -> tuple[float, bool]:
        """ダメージ関連のスコア計算"""
        score = 0.0
        matched = False
        
        # ダメージキーワードと数値条件の組み合わせをチェック  
        has_damage_keyword = any(kw.lower() in ["ダメージ", "技", "攻撃"] for kw in keywords)
        has_damage_condition = any(cond in ' '.join(keywords).lower() for cond in ["30以上", "40以上", "50以上", "60以上"])
        
        if has_damage_keyword and has_damage_condition and not hp_matched:
            if "attacks" in item and item["attacks"]:
                for attack in item["attacks"]:
                    if isinstance(attack, dict) and "damage" in attack:
                        try:
                            damage_value = int(attack["damage"]) if attack["damage"] else 0
                            # 数値条件を確認
                            for kw in keywords:
                                if "30以上" in kw.lower() and damage_value >= 30:
                                    score = 2.0
                                    matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 30 -> +2.0")
                                    break
                                elif "40以上" in kw.lower() and damage_value >= 40:
                                    score = 2.0
                                    matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 40 -> +2.0")
                                    break
                                elif "50以上" in kw.lower() and damage_value >= 50:
                                    score = 2.0
                                    matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 50 -> +2.0")
                                    break
                                elif "60以上" in kw.lower() and damage_value >= 60:
                                    score = 2.0
                                    matched = True
                                    print(f"    ダメージマッチ: {damage_value} >= 60 -> +2.0")
                                    break
                            if matched:
                                break
                        except (ValueError, TypeError):
                            pass
        
        return score, matched

    def _calculate_type_score(self, item: Dict[str, Any], keywords: List[str]) -> tuple[float, bool]:
        """タイプ関連のスコア計算"""
        score = 0.0
        matched = False
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # タイプ関連の処理
            if keyword_lower in ["炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"]:
                if not matched:  # 重複チェック
                    if "type" in item and item["type"]:
                        if keyword_lower == item["type"].lower():
                            score = 2.0
                            matched = True
                            print(f"    タイプマッチ: {keyword} -> +2.0")
                            break
        
        return score, matched

    def _calculate_text_score(self, item: Dict[str, Any], keywords: List[str]) -> float:
        """一般的なテキストマッチングのスコア計算"""
        score = 0.0
        
        # アイテムの全テキストを結合
        searchable_text = self._build_searchable_text(item)
        searchable_text_lower = searchable_text.lower()
        
        excluded_keywords = ["hp", "40以上", "50以上", "100以上", "150以上", "30以上", "60以上", "ダメージ", "技", "攻撃", "タイプ"]
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 除外キーワードをスキップ
            if keyword_lower in excluded_keywords:
                continue
            
            # 完全マッチ
            if keyword_lower in searchable_text_lower:
                score += 0.5
                print(f"    テキストマッチ: {keyword} -> +0.5")
            # 部分マッチ
            elif any(keyword_lower in word for word in searchable_text_lower.split()):
                score += 0.3
                print(f"    部分マッチ: {keyword} -> +0.3")
        
        return score

    def _build_searchable_text(self, item: Dict[str, Any]) -> str:
        """検索可能なテキストを構築"""
        searchable_text = ""
        text_fields = ["name", "title", "type", "category", "rarity", "series", "species", "stage"]
        
        for field in text_fields:
            if field in item and item[field]:
                if isinstance(item[field], str):
                    searchable_text += f" {item[field]}"
                elif isinstance(item[field], list):
                    searchable_text += f" {' '.join(str(x) for x in item[field])}"
                elif isinstance(item[field], dict):
                    searchable_text += f" {' '.join(str(v) for v in item[field].values())}"
        
        return searchable_text

    def _calculate_combo_bonus(self, type_matched: bool, damage_matched: bool, hp_matched: bool) -> float:
        """複合条件ボーナスを計算"""
        if type_matched and (damage_matched or hp_matched):
            print("    複合条件ボーナス: +1.0")
            return 1.0
        return 0.0
    
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
