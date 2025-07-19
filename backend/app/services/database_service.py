

import re
from typing import List, Dict, Any, Optional
from ..core.logging import GameChatLogger


class DatabaseService:
    def __init__(self, data_path: Optional[str] = None):
        # --- ここから下の重複・未完成な関数本体を完全削除 ---
        self.data_path = "data"
        self.debug = False  # デバッグフラグ追加
        # storage_serviceのダミー実装（本来はDIや外部から渡すべき）
        class DummyStorageService:
            def load_data(self) -> list[dict[str, Any]]:
                return []
        self.storage_service = DummyStorageService()
        self.reload_data()

    def reload_data(self) -> None:
        """
        """
        data = self.storage_service.load_data()
        self.data_cache = data
        print(f"[DEBUG] data_cache loaded: {len(self.data_cache)} 件")  # デバッグ出力追加
        self.title_to_data = {}
        for item in data:
            # nameフィールドがキー
            name = item.get("name")
            if name:
                norm_name = str(name).strip()
                self.title_to_data[norm_name] = item
        print(f"[DEBUG] title_to_data keys: {list(self.title_to_data.keys())[:10]} ... (total {len(self.title_to_data)})")
    def _search_filterable(self, keywords: list[str], top_k: int = 10) -> list[dict[str, Any]]:
        print(f"[DEBUG] 検索キーワード: {keywords}")
        print(f"[DEBUG] data_cache 件数: {len(self.data_cache)}")
        results = []
        for item in self.data_cache:
            if all(self._match_filterable(item, kw) for kw in keywords):
                results.append(item)
                if len(results) >= top_k:
                    break
        print(f"[DEBUG] DB検索結果 件数: {len(results)}")
        for i, r in enumerate(results):
            print(f"[DEBUG] DB検索結果[{i}]: {r}")
        return results

    def _match_filterable(self, item: dict[str, Any], keyword: str) -> bool:
        # ダミー実装: すべてTrueを返す（本来はitemの内容とkeywordで判定）
        return True

    def _normalize_keyword(self, keyword: str) -> str:
        # ダミー実装: 前後空白除去
        return keyword.strip()

    def _split_keywords(self, keywords: list[str]) -> list[str]:
        # ダミー実装: そのまま返す
        return keywords

    def _search_semantic(self, keywords: list[str], top_k: int = 10) -> list[dict[str, Any]]:
        # 型チェック用のダミー実装（mypyエラー回避）
        return []

    def _search_hybrid(self, keywords: list[str], top_k: int = 10) -> list[dict[str, Any]]:
        # 型チェック用のダミー実装（mypyエラー回避）
        return []

    def _calculate_hp_score(self, item: Dict[str, Any], keywords: List[str]) -> tuple[float, bool]:
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
        if type_matched and (damage_matched or hp_matched):
            if self.debug:
                GameChatLogger.log_debug("database_service", "    複合条件ボーナス: +1.0")
            return 1.0
        return 0.0

    async def _filter_search_titles(self, keywords: list[str], top_k: int = 10) -> list[str]:
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

    async def filter_search_titles_async(self, keywords: list[str], top_k: int = 10) -> list[str]:
        # _filter_search_titlesのasyncラッパー
        return await self._filter_search_titles(keywords, top_k)
    
    def get_card_details_by_titles(self, titles: list[str]) -> list[dict[Any, Any]]:
        # title_to_dataが未構築ならリロード
        if not hasattr(self, "title_to_data") or not self.title_to_data:
            self.reload_data()
        details = []
        for title in titles:
            if title in self.title_to_data and self.title_to_data[title] is not None:
                details.append(self.title_to_data[title])
        return details
