import re
from typing import List, Dict, Any, Optional
from ..core.logging import GameChatLogger

class DatabaseService:
    def __init__(self, data_path: Optional[str] = None):
        import os
        # data_pathが指定されていればそれを、なければプロジェクトルート基準の絶対パス
        if data_path:
            self.data_path = data_path
        else:
            # このファイル（database_service.py）から見てプロジェクトルートを計算
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
            self.data_path = os.path.join(base_dir, 'data/data.json')
        self.debug = True  # デバッグフラグ追加
                # 実データをロードするストレージサービス
        class JsonFileStorageService:
            def __init__(self, file_path: str) -> None:
                self.file_path = file_path
            def load_data(self) -> list[dict[str, Any]]:
                import json
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data if isinstance(data, list) else []
                except Exception as e:
                    print(f"[ERROR] データファイルの読み込みに失敗: {e}")
                    return []
            def load_json_data(self) -> list[dict[str, Any]]:
                return self.load_data()

        self.storage_service = JsonFileStorageService(self.data_path)
        self.reload_data()

    def _load_data(self) -> list[dict[str, Any]]:
        # テスト用: StorageServiceのload_json_dataを呼ぶ
        if hasattr(self.storage_service, "load_json_data"):
            return self.storage_service.load_json_data()
        elif hasattr(self.storage_service, "load_data"):
            return self.storage_service.load_data()
        return []
    async def filter_search_async(self, keywords: list[str], top_k: int = 10) -> list[str]:
        print(f"[SEARCH] filter_search_async called: keywords={keywords}, top_k={top_k}")
        result = await self.filter_search_titles_async(keywords, top_k)
        print(f"[SEARCH] filter_search_async result: {result}")
        return result

    def filter_search(self, keywords: list[str], top_k: int = 10) -> list[str]:
        print(f"[SEARCH] filter_search called: keywords={keywords}, top_k={top_k}")
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(self.filter_search_async(keywords, top_k))
        print(f"[SEARCH] filter_search result: {result}")
        return result

    def reload_data(self) -> None:
        """
        データを再読み込みし、キャッシュとtitle_to_dataを構築
        """
        data = self._load_data()
        self.data_cache = data
        print(f"[DEBUG] data_cache loaded: {len(self.data_cache)} 件")  # デバッグ出力追加
        self.title_to_data = {}
        for item in data:
            # nameフィールドがキー（正規化処理を強化）
            name = item.get("name")
            if name:
                norm_name = self._normalize_title(str(name))
                self.title_to_data[norm_name] = item
        print(f"[DEBUG] title_to_data keys: {list(self.title_to_data.keys())[:10]} ... (total {len(self.title_to_data)})")
    def _search_filterable(self, keywords: list[str], top_k: int = 10) -> list[dict[str, Any]]:
        print(f"[SEARCH] _search_filterable called: keywords={keywords}, top_k={top_k}")
        print(f"[SEARCH] data_cache count: {len(self.data_cache)}")
        results = []
        for item in self.data_cache:
            match_flags = [self._match_filterable(item, kw) for kw in keywords]
            print(f"[SEARCH] Checking item: {item.get('name', '')}, match_flags={match_flags}")
            if all(match_flags):
                results.append(item)
                print(f"[SEARCH] Matched: {item.get('name', '')}")
                if len(results) >= top_k:
                    break
        print(f"[SEARCH] _search_filterable found {len(results)} results")
        for i, r in enumerate(results):
            print(f"[SEARCH] _search_filterable result[{i}]: {r.get('name', '')}")
        return results

    def _match_filterable(self, item: dict[str, Any], keyword: str) -> bool:
        if self.debug:
            print(f"[DEBUG] _match_filterable: item={item.get('name', '')}, keyword={keyword}")
        
        import re
        
        # コスト条件判定: "コストN" または "Nコスト" → item["cost"] == N
        m1 = re.match(r"コスト(\d+)", keyword)  # "コストN" 形式
        m2 = re.match(r"(\d+)コスト", keyword)  # "Nコスト" 形式
        if m1 or m2:
            try:
                if m1:
                    cost_val = int(m1.group(1))
                    pattern = "コストN"
                elif m2:
                    cost_val = int(m2.group(1))
                    pattern = "Nコスト"
                else:
                    return False
                item_cost = int(item.get("cost", -1))
                result = (item_cost == cost_val)
                if self.debug:
                    print(f"[DEBUG] コスト判定({pattern}): item_cost={item_cost}, 条件={cost_val}, result={result}")
                return result
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] コスト判定エラー: {e}")
                return False
        
        # クラス条件判定: classフィールドとの完全一致
        class_names = [
            "エルフ", "ドラゴン", "ロイヤル", "ウィッチ", "ネクロマンサー",
            "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル", "ナイトメア"
        ]
        if keyword in class_names:
            item_class = str(item.get("class", ""))
            result = (item_class == keyword)
            if self.debug:
                print(f"[DEBUG] クラス判定: item_class='{item_class}', 条件='{keyword}', result={result}")
            return result
        
        # レアリティ条件判定
        rarity_names = [
            "レジェンド", "ゴールドレア", "シルバーレア", "ブロンズ", "レア"
        ]
        if keyword in rarity_names:
            item_rarity = str(item.get("rarity", ""))
            result = (item_rarity == keyword)
            if self.debug:
                print(f"[DEBUG] レアリティ判定: item_rarity='{item_rarity}', 条件='{keyword}', result={result}")
            return result
        
        # HP条件判定: "HP数値以上/以下/未満/超"
        hp_match = re.match(r"HP(\d+)(以上|以下|未満|超)?", keyword)
        if hp_match:
            try:
                hp_val = int(hp_match.group(1))
                condition = hp_match.group(2) or "以上"
                item_hp = int(item.get("hp", 0))
                
                if condition == "以上":
                    result = (item_hp >= hp_val)
                elif condition == "以下":
                    result = (item_hp <= hp_val)
                elif condition == "未満":
                    result = (item_hp < hp_val)
                elif condition == "超":
                    result = (item_hp > hp_val)
                else:
                    result = False
                    
                if self.debug:
                    print(f"[DEBUG] HP判定: item_hp={item_hp}, 条件={keyword}, result={result}")
                return result
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] HP判定エラー: {e}")
                return False
        
        # デフォルト: 名前部分一致
        name = str(item.get("name", ""))
        if keyword in name:
            if self.debug:
                print(f"[DEBUG] 名前部分一致: {keyword} in {name}")
            return True
        
        if self.debug:
            print(f"[DEBUG] マッチしなかった: {keyword}")
        return False

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
        
        # デバッグ: 渡された引数の詳細情報
        print(f"[DEBUG] get_card_details_by_titles called with {len(titles)} titles")
        print(f"[DEBUG] titles type: {type(titles)}")
        if titles:
            print(f"[DEBUG] first title type: {type(titles[0])}")
            print(f"[DEBUG] first title value: {repr(titles[0])}")
        
        details = []
        for title in titles:
            # 明示的な型確認
            actual_title_str = str(title)
            norm_title = self._normalize_title(actual_title_str)
            item = self.title_to_data.get(norm_title)
            if item:
                details.append(item)
            else:
                print(f"[DEBUG] get_card_details_by_titles: not found for title '{title}' (normalized: '{norm_title}')")
        print(f"[DEBUG] get_card_details_by_titles: found {len(details)} / {len(titles)}")
        return details

    def _normalize_title(self, title: str) -> str:
        """
        カード名の正規化（空白・全角スペース・改行・記号除去など）
        """
        import re
        normalized = title.strip()
        normalized = re.sub(r"[\s\u3000]+", "", normalized)  # 空白・全角スペース除去
        normalized = re.sub(r"[\r\n]+", "", normalized)      # 改行除去
        normalized = re.sub(r"[（）()・・]+", "", normalized)   # 一部記号除去
        normalized = normalized.replace("　", "")
        return normalized
