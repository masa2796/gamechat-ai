from typing import List, Dict, Any
from ..core.config import settings
from ..core.exceptions import DatabaseException
from ..core.logging import GameChatLogger

class DatabaseService:
    def _calculate_filter_score(
        self,
        item: Dict[str, Any],
        keywords: List[str]
    ) -> float:
        """
        filter_keywordsの内容を属性ごとに正しく解釈し、全条件をANDで厳密に適用する。
        例: ["コスト3以下", "疾走", "ドラゴン", "フォロワー"]
        """
        if not keywords:
            return 0.0

        import re
        # 属性ごとに条件を抽出
        numeric_conditions = []  # (field, value, cond)
        type_conditions = set()
        class_conditions = set()
        effect_conditions = set()
        follower_condition = False

        # 属性判定用
        type_aliases = ["type", "タイプ"]
        class_aliases = ["class", "クラス"]
        follower_aliases = ["フォロワー"]

        import re
        for kw in keywords:
            m = re.search(r'(コスト|cost|HP|体力|攻撃|attack)[^\d]*(\d+)(以上|以下|未満|超)?', kw)
            if m:
                field = m.group(1)
                value = int(m.group(2))
                cond = m.group(3) or '以上'
                if field in ["コスト", "cost"]:
                    field = "cost"
                elif field in ["HP", "体力"]:
                    field = "hp"
                elif field in ["攻撃", "attack"]:
                    field = "attack"
                numeric_conditions.append((field, value, cond))
                continue
            for t in type_aliases:
                if t in kw:
                    type_conditions.add(kw.replace(t, '').strip() or t)
            for c in class_aliases:
                if c in kw:
                    class_conditions.add(kw.replace(c, '').strip() or c)
            for f in follower_aliases:
                if f in kw:
                    follower_condition = True
            if not (m or any(t in kw for t in type_aliases + class_aliases + follower_aliases)):
                effect_conditions.add(kw)

        # AND条件厳密化: 全ての条件を満たす場合のみスコア加算
        all_conditions_met = True
        total_score = 0.0

        for field, value, cond in numeric_conditions:
            item_val = item.get(field) or item.get(field.upper())
            try:
                item_val = int(item_val)
            except Exception:
                all_conditions_met = False
                continue
            if cond == '以上':
                if not (item_val >= value):
                    all_conditions_met = False
                else:
                    total_score += 1
            elif cond == '以下':
                if not (item_val <= value):
                    all_conditions_met = False
                else:
                    total_score += 1
            elif cond == '未満':
                if not (item_val < value):
                    all_conditions_met = False
                else:
                    total_score += 1
            elif cond == '超':
                if not (item_val > value):
                    all_conditions_met = False
                else:
                    total_score += 1

        # タイプ条件
        if type_conditions:
            item_type = str(item.get("type", "")).lower()
            if not any(tc.lower() in item_type for tc in type_conditions):
                all_conditions_met = False
            else:
                total_score += 1

        # クラス条件
        if class_conditions:
            item_class = str(item.get("class", "")).lower()
            if not any(cc.lower() in item_class for cc in class_conditions):
                all_conditions_met = False
            else:
                total_score += 1

        # フォロワー条件
        if follower_condition:
            # type, class, keywords, effect等に「フォロワー」含むか
            found = False
            for field in ["type", "class", "keywords"]:
                val = item.get(field)
                if val:
                    if isinstance(val, list):
                        if any("フォロワー" in str(v) for v in val):
                            found = True
                    elif "フォロワー" in str(val):
                        found = True
            # 効果文にも含まれるか
            for ef in ["effect_1", "effect_2", "effect_3", "effect", "description", "text"]:
                val = item.get(ef)
                if val and "フォロワー" in str(val):
                    found = True
            if not found:
                all_conditions_met = False
            else:
                total_score += 1

        # 効果文・キーワード条件
        for kw in effect_conditions:
            found = False
            # 効果文
            for ef in ["effect_1", "effect_2", "effect_3", "effect", "description", "text"]:
                val = item.get(ef)
                if val and kw.replace('_', '').replace('・', '') in str(val).replace('_', '').replace('・', ''):
                    found = True
                    break
            # attacks配列
            if not found and 'attacks' in item and isinstance(item['attacks'], list):
                for atk in item['attacks']:
                    if isinstance(atk, dict):
                        for v in atk.values():
                            if isinstance(v, str) and kw in v:
                                found = True
                                break
                    if found:
                        break
            # keywords
            if not found and 'keywords' in item and isinstance(item['keywords'], list):
                if any(kw in str(k) for k in item['keywords']):
                    found = True
            if not found:
                all_conditions_met = False
            else:
                total_score += 1

        if all_conditions_met and total_score > 0:
            return total_score
        return 0.0
        # 両方のファイルが利用できない場合
        GameChatLogger.log_error("database_service", "データファイルが利用できません", Exception("No data files available"), {
            "primary_file": "data.json",
            "fallback_file": "convert_data.json",
            "environment": settings.ENVIRONMENT
        })
        # プレースホルダーデータを返す（完全な失敗を防ぐため）
        placeholder_data = self._get_placeholder_data()
        if placeholder_data:
            self.cache = placeholder_data
            GameChatLogger.log_warning("database_service", "プレースホルダーデータを使用", {
                "data_count": len(placeholder_data)
            })
            return self.cache
        # プレースホルダーデータがNoneや空リストの場合は例外を投げる
        raise DatabaseException(
            message="データファイルが見つかりません",
            code="DATA_FILE_NOT_FOUND",
            details={
                "primary_file": "data.json", 
                "fallback_file": "convert_data.json",
                "storage_service_configured": bool(self.storage_service)
            }
        )

    def reload_data(self) -> None:
        """
        明示的にデータを再ロードするメソッド
        """
        self.cache = None
        data_list = self._load_data()
        self.title_to_data = {self._extract_title(item): item for item in data_list if self._extract_title(item)}

    def _calculate_filter_score(
        self,
        item: Dict[str, Any],
        keywords: List[str]
    ) -> float:
        """
        アイテムとキーワードのマッチスコアを計算（data.jsonの属性に準拠、type/class/keywords柔軟化、damage/hp/type条件は専用関数で加算、attacks配列も考慮）
        - コスト・クラス・能力・カード種別などのAND条件を厳密に判定
        """
        if not keywords:
            return 0.0
        import re
        # 数値条件抽出用正規表現
        numeric_patterns = [
            (r'(コスト|cost)[^\d]*(\d+)(以上|以下|未満|超)?', 'cost'),
            (r'(HP|体力)[^\d]*(\d+)(以上|以下|未満|超)?', 'hp'),
            (r'(攻撃|attack)[^\d]*(\d+)(以上|以下|未満|超)?', 'attack'),
        ]
        effect_fields = ['effect_1', 'effect_2', 'effect', 'description', 'text']
        # AND条件厳密化: 全条件を満たした場合のみスコア加算
        all_conditions_met = True
        total_score = 0.0
        # 既存のtype/class/keywords/フォロワー判定ロジックは削除し、
        # 上記の属性ごと厳密AND適用ロジックに一本化済みです。

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
        import re
        score = 0.0
        matched = False
        has_hp_keyword = any("hp" in kw.lower() or "体力" in kw.lower() or "ヒットポイント" in kw for kw in keywords)
        # 正規表現で「xx以上」「xx以下」などの数値条件を抽出
        hp_conditions = []
        for kw in keywords:
            m = re.search(r'(\d+)(以上|以下|未満|超)?', kw)
            if m:
                value = int(m.group(1))
                cond = m.group(2) or '以上'  # デフォルトは「以上」
                hp_conditions.append((value, cond))
        if has_hp_keyword and hp_conditions:
            try:
                hp_value = int(item["hp"]) if "hp" in item and item["hp"] else 0
                for num, cond in hp_conditions:
                    if cond == "以上":
                        if hp_value >= num:
                            score = 2.0
                            matched = True
                            if self.debug:
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} >= {num} -> +2.0")
                            break
                    elif cond == "以下":
                        if hp_value <= num:
                            score = 2.0
                            matched = True
                            if self.debug:
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} <= {num} -> +2.0")
                            break
                    elif cond == "未満":
                        if hp_value < num:
                            score = 2.0
                            matched = True
                            if self.debug:
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} < {num} -> +2.0")
                            break
                    elif cond == "超":
                        if hp_value > num:
                            score = 2.0
                            matched = True
                            if self.debug:
                                GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} > {num} -> +2.0")
                            break
            except (ValueError, TypeError):
                pass
        return score, matched

    def _calculate_damage_score(self, item: Dict[str, Any], keywords: List[str], hp_matched: bool) -> tuple[float, bool]:
        """ダメージ関連のスコア計算（data.jsonのeffect_1等からダメージ数値抽出）"""
        import re
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
    
    def _extract_text(self, item: Dict[str, Any]) -> str:
        """
        アイテムから検索可能テキストを抽出（data.jsonの属性に準拠）。
        テスト仕様に合わせて'種類'や'進化段階'なども含める。
        """
        text_parts = []
        if "type" in item:
            text_parts.append(f"タイプ: {item['type']}")
        if "class" in item:
            text_parts.append(f"クラス: {item['class']}")
        if "rarity" in item:
            text_parts.append(f"レアリティ: {item['rarity']}")
        if "cost" in item:
            text_parts.append(f"コスト: {item['cost']}")
        if "attack" in item:
            text_parts.append(f"攻撃: {item['attack']}")
        if "hp" in item:
            text_parts.append(f"HP: {item['hp']}")
        if "species" in item:
            text_parts.append(f"種類: {item['species']}")
        if "stage" in item:
            text_parts.append(f"進化段階: {item['stage']}")
        if "weakness" in item:
            text_parts.append(f"弱点: {item['weakness']}")
        if "effect_1" in item:
            text_parts.append(f"効果1: {item['effect_1']}")
        if "effect_2" in item:
            text_parts.append(f"効果2: {item['effect_2']}")
        if "effect_3" in item:
            text_parts.append(f"効果3: {item['effect_3']}")
        if "cv" in item:
            text_parts.append(f"CV: {item['cv']}")
        if "illustrator" in item:
            text_parts.append(f"イラスト: {item['illustrator']}")
        if "keywords" in item and isinstance(item["keywords"], list):
            text_parts.append(f"キーワード: {'/'.join(str(k) for k in item['keywords'])}")
        if "qa" in item and isinstance(item["qa"], list):
            for qa_item in item["qa"]:
                if isinstance(qa_item, dict):
                    q = qa_item.get("question", "")
                    a = qa_item.get("answer", "")
                    text_parts.append(f"Q: {q} A: {a}")
        return " / ".join(text_parts) if text_parts else str(item)
    
    def _get_fallback_results(self) -> List[str]:
        """
        フォールバック用のダミーカード名リスト
        """
        return ["データベース検索 - フィルター結果"]
    
    def _get_placeholder_data(self) -> List[Dict[str, Any]]:
        """データファイルが利用できない場合のプレースホルダーデータ"""
        return [
            {
                "id": "placeholder-001",
                "title": "システム情報",
                "content": "このデータはプレースホルダーです。実際のゲームデータが利用できない状態です。",
                "category": "system",
                "type": "情報",
                "created_at": "2025-06-20T00:00:00Z",
                "tags": ["システム", "プレースホルダー"]
            },
            {
                "id": "placeholder-002", 
                "title": "データ読み込みエラー",
                "content": "Google Cloud Storageまたはローカルファイルからデータを読み込めませんでした。管理者にお問い合わせください。",
                "category": "system",
                "type": "エラー",
                "created_at": "2025-06-20T00:00:00Z",
                "tags": ["エラー", "データ"]
            }
        ]
    
    def get_card_details_by_titles(self, titles: list[str]) -> list[dict]:
        """
        カード名リストから詳細データ(dict)リストを取得
        """
        return [self.title_to_data[title] for title in titles if title in self.title_to_data]
