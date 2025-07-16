
import re
from typing import List, Dict, Any
from ..core.logging import GameChatLogger
from .storage_service import StorageService

class DatabaseService:
    def _normalize_keyword(self, keyword: str) -> str:
        """
        検索キーワードの正規化処理
        - 全角→半角
        - ひらがな→カタカナ
        - 英字小文字化
        - 前後空白除去
        - 属性名の揺れを統一
        """
        import unicodedata
        # 全角→半角
        keyword = unicodedata.normalize('NFKC', keyword)
        # ひらがな→カタカナ
        keyword = ''.join([
            chr(ord(ch) + 0x60) if 'ぁ' <= ch <= 'ゖ' else ch for ch in keyword
        ])
        # 英字小文字化
        keyword = keyword.lower()
        # 前後空白除去
        keyword = keyword.strip()
        # 属性名の揺れを統一
        keyword = keyword.replace('職業', 'クラス').replace('class', 'クラス')
        return keyword

    def _split_keywords(self, keywords: list[str]) -> list[str]:
        """
        複合条件の分割（空白・全角空白・カンマ区切り等）
        """
        result = []
        for kw in keywords:
            # 全角空白・半角空白・カンマで分割
            for part in re.split(r'[\s　,、]+', kw):
                if part:
                    result.append(part)
        return result

    def search_cards(self, keywords: list[str], query_type: str = "filterable") -> list[dict[str, Any]]:
        """
        クエリタイプに応じて最適な検索を実行する
        filterable: 明確な属性・数値条件のみ → 条件一致カードをそのまま返す
        semantic/hybrid: スコア計算で重み付け
        Args:
            keywords (list[str]): 検索キーワード
            query_type (str): クエリタイプ（filterable/semantic/hybrid）
        Returns:
            list[dict]: 検索結果リスト
        """
        if query_type == "filterable":
            # キーワード正規化・分割
            normalized = [self._normalize_keyword(kw) for kw in keywords]
            expanded = self._split_keywords(normalized)
            # AND条件で全キーワードに一致するカードのみ返す
            results = []
            for item in self.data_cache:
                if all(self._match_filterable(item, kw) for kw in expanded):
                    results.append(item)
            return results
        else:
            # スコア計算による重み付け検索
            results = []
            for item in self.data_cache:
                hp_score, hp_matched = self._calculate_hp_score(item, keywords)
                damage_score, damage_matched = self._calculate_damage_score(item, keywords, hp_matched)
                type_score, type_matched = self._calculate_type_score(item, keywords)
                text_score = self._calculate_text_score(item, keywords)
                combo_bonus = 0.0
                if type_matched and (damage_matched or hp_matched):
                    combo_bonus = 1.0
                total_score = hp_score + damage_score + type_score + text_score + combo_bonus
                if total_score > 0:
                    results.append({
                        **item,
                        "_score": total_score
                    })
            results.sort(key=lambda x: x["_score"], reverse=True)
            return results

    def _match_filterable(self, item: dict, keyword: str) -> bool:
        """
        単純な属性・数値条件キーワードに対する一致判定（例: クラス名、コストN以下等）
        - コスト条件: コストN, コストN以下, コストN未満, コストN以上, コストN超, cost N, cost <=N, cost >=N, cost <N, cost >N, Nコスト, N cost
        - 等価条件や英語表現にも対応
        - 型安全な比較
        """
        import re
        # コスト条件（日本語・英語・等価・比較）
        cost_patterns = [
            r"コスト(\d+)(以下|未満|以上|超)?",           # コスト1以下, コスト1
            r"(\d+)コスト(以下|未満|以上|超)?",           # 1コスト以下, 1コスト
            r"cost\s*(=|<=|>=|<|>)?\s*(\d+)",           # cost<=1, cost=1
            r"(\d+)\s*cost(以下|未満|以上|超)?",         # 1 cost以下, 1 cost
        ]
        for pat in cost_patterns:
            m = re.match(pat, keyword, re.IGNORECASE)
            if m and "cost" in item:
                try:
                    if pat.startswith("cost"):
                        op = m.group(1) or "="
                        value = int(m.group(2))
                    elif pat.startswith("コスト") or pat.startswith("("):
                        value = int(m.group(1))
                        cond = m.group(2) or "="
                        op = {
                            "以下": "<=", "未満": "<", "以上": ">=", "超": ">", None: "="
                        }[cond]
                    else:
                        value = int(m.group(1))
                        cond = m.group(2) or "="
                        op = {
                            "以下": "<=", "未満": "<", "以上": ">=", "超": ">", None: "="
                        }[cond]
                    cost = item.get("cost")
                    if cost is None:
                        return False
                    try:
                        cost = int(cost)
                    except Exception:
                        return False
                    if op == "<":
                        return cost < value
                    elif op == "<=":
                        return cost <= value
                    elif op == ">":
                        return cost > value
                    elif op == ">=":
                        return cost >= value
                    elif op == "=":
                        return cost == value
                except Exception:
                    return False
        if keyword.isdigit() and "cost" in item:
            try:
                return int(item["cost"]) == int(keyword)
            except Exception:
                return False
        for key in ["class", "type", "category"]:
            if key in item and keyword in str(item[key]):
                return True
        return False
    def __init__(self) -> None:
        # data.jsonのカード名→詳細dictのキャッシュ
        self.title_to_data: dict[str, dict] = {}
        self.data_cache: list[dict] = []
        self.storage_service = StorageService()
        self.debug = False
        # data_path属性を追加
        # StorageServiceの論理キー（'data'）を使う
        self.data_path = "data"
        self.reload_data()

    def reload_data(self) -> None:
        """
        data.jsonを再ロードし、title_to_dataキャッシュを再構築する
        """
        data = self._load_data()
        self.data_cache = data
        self.title_to_data = {}
        for item in data:
            # nameフィールドがキー
            name = item.get("name")
            if name:
                self.title_to_data[name] = item

    def _load_data(self) -> list[dict[Any, Any]]:
        """
        StorageService経由でデータファイルをロードする（テスト用モックも考慮）
        """
        try:
            data = self.storage_service.load_json_data(self.data_path)
            if not isinstance(data, list):
                return []
            # 各要素がdictであることを保証
            return [d for d in data if isinstance(d, dict)]
        except Exception:
            return []
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
                - 数値条件: "40以上", "50以上", "100以上", "150以上" など任意
        Returns:
            tuple[float, bool]: (スコア, マッチしたかどうか)
        Note:
            - HPキーワードと数値条件の両方が必要です
            - HP値が数値変換できない場合は0として扱います
            - 複数の数値条件がある場合、最初にマッチした条件でスコアを決定します
        """
        score = 0.0
        matched = False
        has_hp_keyword = any("hp" in kw.lower() or "体力" in kw.lower() or "ヒットポイント" in kw for kw in keywords)
        hp_conditions = []
        for kw in keywords:
            m = re.search(r'(\d+)(以上|以下|未満|超)?', kw)
            if m:
                value = int(m.group(1))
                cond = m.group(2) or '以上'
                hp_conditions.append((value, cond))
        if has_hp_keyword and hp_conditions:
            try:
                hp_value = int(item["hp"]) if "hp" in item and item["hp"] else 0
                for num, cond in hp_conditions:
                    if cond == "以上":
                        if hp_value >= num:
                            score = 2.0
                            matched = True
                            if getattr(self, 'debug', False):
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} >= {num} -> +2.0")
                            break
                    elif cond == "以下":
                        if hp_value <= num:
                            score = 2.0
                            matched = True
                            if getattr(self, 'debug', False):
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} <= {num} -> +2.0")
                            break
                    elif cond == "未満":
                        if hp_value < num:
                            score = 2.0
                            matched = True
                            if getattr(self, 'debug', False):
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} < {num} -> +2.0")
                            break
                    elif cond == "超":
                        if hp_value > num:
                            score = 2.0
                            matched = True
                            if getattr(self, 'debug', False):
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} > {num} -> +2.0")
                            break
            except (ValueError, TypeError):
                pass
        return score, matched

    def _calculate_damage_score(self, item: Dict[str, Any], keywords: List[str], hp_matched: bool) -> tuple[float, bool]:
        """ダメージ関連のスコア計算（data.jsonのeffect_1等からダメージ数値抽出）"""
        score = 0.0
        matched = False
        has_damage_keyword = any(kw.lower() in ["ダメージ", "技", "攻撃"] for kw in keywords)
        # 正規表現で「xx以上」「xx以下」などの数値条件を抽出
        damage_conditions = []
        for kw in keywords:
            m = re.search(r'(\d+)(以上|以下|未満|超)?', kw)
            if m:
                value = int(m.group(1))
                cond = m.group(2) or '以上'  # デフォルトは「以上」
                damage_conditions.append((value, cond))
        if has_damage_keyword and damage_conditions and not hp_matched:
            for ef in ["effect_1", "effect_2", "effect_3"]:
                if ef in item and item[ef]:
                    m = re.search(r"(\d+)ダメージ", str(item[ef]))
                    if m:
                        damage_value = int(m.group(1))
                        for num, cond in damage_conditions:
                            if cond == "以上":
                                if damage_value >= num:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} >= {num} -> +2.0")
                                    break
                            elif cond == "以下":
                                if damage_value <= num:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} <= {num} -> +2.0")
                                    break
                            elif cond == "未満":
                                if damage_value < num:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} < {num} -> +2.0")
                                    break
                            elif cond == "超":
                                if damage_value > num:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} > {num} -> +2.0")
                                    break
                        if matched:
                            break
        return score, matched

    def _calculate_type_score(self, item: Dict[str, Any], keywords: List[str]) -> tuple[float, bool]:
        """タイプ関連のスコア計算（type/class/keywords柔軟化）"""
        score = 0.0
        matched = False
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # type, class, keywords いずれかに一致
            if ("type" in item and item["type"] and keyword_lower in str(item["type"]).lower()) or \
               ("class" in item and item["class"] and keyword_lower in str(item["class"]).lower()) or \
               ("keywords" in item and any(keyword_lower in str(k).lower() for k in item["keywords"])):
                score = 2.0
                matched = True
                if self.debug:
                    GameChatLogger.log_debug("database_service", f"    タイプ/クラス/キーワードマッチ: {keyword} -> +2.0")
                break
        return score, matched

    def _calculate_text_score(self, item: Dict[str, Any], keywords: List[str]) -> float:
        """一般的なテキストマッチングのスコア計算（data.jsonの全属性を対象）"""
        score = 0.0
        searchable_text = self._build_searchable_text(item).lower()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in searchable_text:
                score += 0.5
                if self.debug:
                    GameChatLogger.log_debug("database_service", f"    テキストマッチ: {keyword} -> +0.5")
        return score

    def _build_searchable_text(self, item: Dict[str, Any]) -> str:
        """検索可能なテキストを構築（data.jsonの全属性を対象）"""
        fields = [
            "id", "name", "class", "rarity", "cost", "attack", "hp", "effect_1", "effect_2", "effect_3", "cv", "illustrator", "crest"
        ]
        text = []
        for field in fields:
            if field in item and item[field]:
                text.append(str(item[field]))
        # keywords, qaも追加
        if "keywords" in item and isinstance(item["keywords"], list):
            text.extend([str(k) for k in item["keywords"]])
        if "qa" in item and isinstance(item["qa"], list):
            for qa_item in item["qa"]:
                if isinstance(qa_item, dict):
                    text.append(qa_item.get("question", ""))
                    text.append(qa_item.get("answer", ""))
        return " ".join(text)

    def _calculate_combo_bonus(self, type_matched: bool, damage_matched: bool, hp_matched: bool) -> float:
        """複合条件ボーナスを計算"""
        if type_matched and (damage_matched or hp_matched):
            if self.debug:
                GameChatLogger.log_debug("database_service", "    複合条件ボーナス: +1.0")
            return 1.0
        return 0.0

    async def filter_search(self, keywords: list[str], top_k: int = 10) -> list[str]:
        """
        AND条件で全キーワードに一致するカード名リストを返す（非同期）
        """
        # 空キーワードまたはデータが空なら即空リスト返却
        if not keywords or not self.data_cache:
            return []
        normalized = [self._normalize_keyword(kw) for kw in keywords]
        expanded = self._split_keywords(normalized)
        if not expanded:
            return []
        results = []
        for item in self.data_cache:
            if all(self._match_filterable(item, kw) for kw in expanded):
                name = item.get("name")
                if name:
                    results.append(name)
            if len(results) >= top_k:
                break
        return results
    
    def get_card_details_by_titles(self, titles: list[str]) -> list[dict[Any, Any]]:
        """
        カード名リストから詳細データ(dict)リストを取得
        """
        # title_to_dataが未構築ならリロード
        if not hasattr(self, "title_to_data") or not self.title_to_data:
            self.reload_data()
        return [self.title_to_data[title] for title in titles if title in self.title_to_data and self.title_to_data[title] is not None]
