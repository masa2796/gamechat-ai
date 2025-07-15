from typing import List, Dict, Any, Optional
from ..models.rag_models import ContextItem
from ..core.config import settings
from ..core.exceptions import DatabaseException
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger
from .storage_service import StorageService

class DatabaseService:
    async def filter_search(self, filter_keywords: List[str], top_k: int = 50) -> List[str]:
        """
        フィルタキーワードに基づいて構造化検索を実行し、カード名リストを返却（data.json仕様）
        
        Args:
            filter_keywords: フィルタリング用キーワードのリスト
                - 例: ["HP", "100以上"], ["エルフ"], ["ダメージ", "3以上"]
            top_k: 返却する最大件数
        Returns:
            マッチスコア順にソートされたカード名リスト
        """
        data = self._load_data()
        if not data:
            return self._get_fallback_results()
        filtered_titles = []
        scores = {}
        for item in data:
            score = self._calculate_filter_score(item, filter_keywords)
            if score > 0:
                title = self._extract_title(item)
                filtered_titles.append(title)
                scores[title] = score
        self.last_scores = scores
        # スコア順にソート
        filtered_titles = sorted(filtered_titles, key=lambda t: scores[t], reverse=True)
        return filtered_titles[:top_k]

    def _extract_title(self, item: dict) -> str:
        """
        カードのタイトル（nameまたはtitle）を抽出。なければ'不明なアイテム'。
        """
        if "name" in item and item["name"]:
            return item["name"]
        if "title" in item and item["title"]:
            return item["title"]
        return "不明なアイテム"
    # 検索ごとにカード名→スコアの辞書を保持
    last_scores: dict = {}
    _instance = None
    def __new__(cls, *args: object, **kwargs: object) -> "DatabaseService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    """通常のデータベース検索サービス（構造化データのフィルタリング）"""
    
    def __init__(self) -> None:
        
        # 設定ファイルからデータファイルのパスを取得（後方互換性のため保持）
        self.data_path = settings.DATA_FILE_PATH
        self.converted_data_path = settings.CONVERTED_DATA_FILE_PATH
        self.cache: Optional[List[Dict[str, Any]]] = None
        self.title_to_data: dict[str, dict] = {}
        
        # StorageServiceを初期化
        self.storage_service = StorageService()
        print(f"[DEBUG] settings: {settings}")
        print(f"[DEBUG] settings type: {type(settings)}")
        print(f"[DEBUG] hasattr(settings, 'ENVIRONMENT'): {hasattr(settings, 'ENVIRONMENT')}")
        print(f"[DEBUG] settings.ENVIRONMENT: {getattr(settings, 'ENVIRONMENT', '属性なし')}")

        
        # 初期化時にパス情報をログ出力
        GameChatLogger.log_info("database_service", "DatabaseService初期化", {
            "data_path": self.data_path,
            "converted_path": self.converted_data_path,
            "project_root": str(settings.PROJECT_ROOT if hasattr(settings, 'PROJECT_ROOT') else 'N/A'),
            "environment": settings.ENVIRONMENT,
            "storage_service_initialized": True
        })
        
        self.debug = getattr(settings, "DEBUG", False)  # デバッグ用フラグ
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """データファイルを読み込む"""
        if self.cache is not None:
            return self.cache
        GameChatLogger.log_info("database_service", "データファイル読み込み開始", {
            "environment": settings.ENVIRONMENT,
            "using_storage_service": True
        })
        # まずmain data fileを試行
        data = self.storage_service.load_json_data("data")
        if data:
            self.cache = data
            # title_to_dataを構築
            self.title_to_data = {self._extract_title(item): item for item in data if self._extract_title(item)}
            GameChatLogger.log_success("database_service", "データファイルを読み込みました", {
                "source": "data.json",
                "data_count": len(data)
            })
            return self.cache
        # フォールバックとしてconvert_dataを試行
        GameChatLogger.log_info("database_service", "フォールバックファイルを試行")
        data = self.storage_service.load_json_data("convert_data")
        if data:
            self.cache = data
            # title_to_dataを構築
            self.title_to_data = {self._extract_title(item): item for item in data if self._extract_title(item)}
            GameChatLogger.log_info("database_service", "フォールバックファイルを使用", {
                "source": "convert_data.json",
                "data_count": len(data)
            })
            return self.cache
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
        """
        if not keywords:
            return 0.0
        score = 0.0
        # HP条件
        hp_score, hp_matched = self._calculate_hp_score(item, keywords)
        score += hp_score
        # ダメージ条件（attacks配列も考慮）
        damage_score, damage_matched = self._calculate_damage_score(item, keywords, hp_matched)
        score += damage_score
        # attacks配列のdamageもキーワード条件で加点
        for kw in keywords:
            if "attacks" in item and isinstance(item["attacks"], list):
                for attack in item["attacks"]:
                    if isinstance(attack, dict) and "damage" in attack:
                        try:
                            dmg = int(attack["damage"])
                            if kw.endswith("以上") and kw[:-2].isdigit():
                                if dmg >= int(kw[:-2]):
                                    score += 1.0
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    attacks配列ダメージマッチ: {kw} -> +1.0")
                        except Exception:
                            pass
        # タイプ条件
        type_score, type_matched = self._calculate_type_score(item, keywords)
        score += type_score
        # その他属性
        for kw in keywords:
            kw_l = kw.lower()
            # クラス/type/keywords
            if ("class" in item and item["class"] and kw in str(item["class"])) or \
               ("type" in item and item["type"] and kw in str(item["type"])) or \
               ("keywords" in item and any(kw in str(k) for k in item["keywords"])):
                score += 2.0
                if self.debug:
                    GameChatLogger.log_debug("database_service", f"    クラス/タイプ/キーワードマッチ: {kw} -> +2.0")
            # レアリティ
            if "rarity" in item and item["rarity"] and kw in str(item["rarity"]):
                score += 1.0
                if self.debug:
                    GameChatLogger.log_debug("database_service", f"    レアリティマッチ: {kw} -> +1.0")
            # コスト
            if "cost" in item:
                try:
                    cost_val = int(item["cost"])
                    if kw_l.isdigit() and int(kw_l) == cost_val:
                        score += 2.0
                        if self.debug:
                            GameChatLogger.log_debug("database_service", f"    コストマッチ: {kw} == {cost_val} -> +2.0")
                except Exception:
                    pass
            # 攻撃
            if "attack" in item:
                try:
                    attack_val = int(item["attack"])
                    if kw_l.isdigit() and int(kw_l) == attack_val:
                        score += 1.0
                        if self.debug:
                            GameChatLogger.log_debug("database_service", f"    攻撃マッチ: {kw} == {attack_val} -> +1.0")
                except Exception:
                    pass
            # 効果文
            for ef in ["effect_1", "effect_2", "effect_3"]:
                if ef in item and item[ef] and kw in str(item[ef]):
                    score += 0.5
                    if self.debug:
                        GameChatLogger.log_debug("database_service", f"    効果マッチ: {kw} -> +0.5")
            # QA
            if "qa" in item and isinstance(item["qa"], list):
                for qa_item in item["qa"]:
                    if isinstance(qa_item, dict):
                        if kw in qa_item.get("question", "") or kw in qa_item.get("answer", ""):
                            score += 0.3
                            if self.debug:
                                GameChatLogger.log_debug("database_service", f"    QAマッチ: {kw} -> +0.3")
        # テキスト全体で部分一致
        searchable_text = self._build_searchable_text(item)
        for kw in keywords:
            if kw in searchable_text:
                score += 0.2
                if self.debug:
                    GameChatLogger.log_debug("database_service", f"    テキスト部分一致: {kw} -> +0.2")
        return score

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
        
        has_hp_keyword = any("hp" in kw.lower() or "体力" in kw.lower() for kw in keywords)
        hp_conditions = [c for c in ["40以上", "50以上", "100以上", "150以上"] if any(c in kw for kw in keywords)]
        if has_hp_keyword and hp_conditions:
            try:
                hp_value = int(item["hp"]) if "hp" in item and item["hp"] else 0
                for cond in hp_conditions:
                    num = int(cond.replace("以上", ""))
                    if hp_value >= num:
                        score = 2.0
                        matched = True
                        if self.debug:
                            GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} >= {num} -> +2.0")
                        break
            except (ValueError, TypeError):
                pass
        return score, matched
        return score, matched

    def _calculate_damage_score(self, item: Dict[str, Any], keywords: List[str], hp_matched: bool) -> tuple[float, bool]:
        """ダメージ関連のスコア計算（data.jsonのeffect_1等からダメージ数値抽出）"""
        score = 0.0
        matched = False
        has_damage_keyword = any(kw.lower() in ["ダメージ", "技", "攻撃"] for kw in keywords)
        damage_conditions = [c for c in ["30以上", "40以上", "50以上", "60以上"] if any(c in kw for kw in keywords)]
        if has_damage_keyword and damage_conditions and not hp_matched:
            for ef in ["effect_1", "effect_2", "effect_3"]:
                if ef in item and item[ef]:
                    import re
                    m = re.search(r"(\d+)ダメージ", str(item[ef]))
                    if m:
                        damage_value = int(m.group(1))
                        for cond in damage_conditions:
                            num = int(cond.replace("以上", ""))
                            if damage_value >= num:
                                score = 2.0
                                matched = True
                                if self.debug:
                                    GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} >= {num} -> +2.0")
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
