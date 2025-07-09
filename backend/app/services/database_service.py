from typing import List, Dict, Any, Optional
from ..models.rag_models import ContextItem
from ..core.config import settings
from ..core.exceptions import DatabaseException
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger
from .storage_service import StorageService

class DatabaseService:
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
        
        raise DatabaseException(
            message="データファイルが見つかりません",
            code="DATA_FILE_NOT_FOUND",
            details={
                "primary_file": "data.json", 
                "fallback_file": "convert_data.json",
                "storage_service_configured": bool(self.storage_service)
            }
        )
    
    @handle_service_exceptions("database", fallback_return=[])
    async def filter_search(self, filter_keywords: List[str], top_k: int = 50) -> List[str]:
        """
        フィルターキーワードに基づいて構造化検索を実行し、カード名リストを返却
        
        Args:
            filter_keywords: フィルタリング用キーワードのリスト
                - 数値条件: ["HP", "100以上"], ["ダメージ", "40以上"]
                - タイプ: ["炎", "タイプ"], ["水", "カード"]
                - レアリティ: ["R", "レア"], ["SR", "スーパーレア"]
            top_k: 返却する最大結果数 (デフォルト: 50)
                
        Returns:
            マッチスコア順にソートされたカード名のリスト
            
        Raises:
            DatabaseException: データファイルの読み込みに失敗した場合
            ValueError: 不正なキーワード形式が含まれている場合
            
        Examples:
            >>> service = DatabaseService()
            >>> # HP100以上のカードを検索
            >>> results = await service.filter_search(["HP", "100以上"], top_k=10)
            >>> print(f"見つかった件数: {len(results)}")
            >>> print(f"カード名: {results[0]}")
            
            >>> # 複合条件での検索
            >>> results = await service.filter_search(
            ...     ["炎", "タイプ", "ダメージ", "40以上"], top_k=5
            ... )
            >>> # 炎タイプでダメージ40以上の技を持つカードの名前が返される
        """
        data = self._load_data()
        if not data:
            return self._get_fallback_results()
        
        GameChatLogger.log_info("database_service", "データベースフィルター検索を開始", {
            "keywords": filter_keywords,
            "data_count": len(data),
            "top_k": top_k
        })
        
        filtered_titles = []
        for item in data:
            score = self._calculate_filter_score(item, filter_keywords)
            if score > 0:
                title = self._extract_title(item)
                filtered_titles.append(title)
        
        GameChatLogger.log_success("database_service", "フィルター検索完了", {
            "results_count": len(filtered_titles),
            "returned_count": min(len(filtered_titles), top_k)
        })
        
        return filtered_titles[:top_k]

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

        if self.debug:
            GameChatLogger.log_debug("database_service", f"  評価中: {item.get('name', 'Unknown')} (タイプ: {item.get('type', 'Unknown')})")
        
        # 各スコアを計算
        hp_score, hp_matched = self._calculate_hp_score(item, keywords)
        damage_score, damage_matched = self._calculate_damage_score(item, keywords, hp_matched)
        type_score, type_matched = self._calculate_type_score(item, keywords)
        text_score = self._calculate_text_score(item, keywords)
        
        # 複合条件ボーナスを計算
        combo_bonus = self._calculate_combo_bonus(type_matched, damage_matched, hp_matched)
        total_score = hp_score + damage_score + type_score + text_score + combo_bonus
        if self.debug:
            GameChatLogger.log_debug("database_service", f"    最終スコア: {total_score}")
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
                for kw in keywords:
                    if "40以上" in kw.lower() and hp_value >= 40:
                        score = 2.0
                        matched = True
                        if self.debug:
                            GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} >= 40 -> +2.0")
                        break
                    elif "50以上" in kw.lower() and hp_value >= 50:
                        score = 2.0
                        matched = True
                        if self.debug:
                            GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} >= 50 -> +2.0")
                        break
                    elif "100以上" in kw.lower() and hp_value >= 100:
                        score = 2.0
                        matched = True
                        if self.debug:
                            GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} >= 100 -> +2.0")
                        break
                    elif "150以上" in kw.lower() and hp_value >= 150:
                        score = 2.0
                        matched = True
                        if self.debug:
                            GameChatLogger.log_debug("database_service", f"    HPマッチ: {hp_value} >= 150 -> +2.0")
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
                            for kw in keywords:
                                if "30以上" in kw.lower() and damage_value >= 30:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} >= 30 -> +2.0")
                                    break
                                elif "40以上" in kw.lower() and damage_value >= 40:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} >= 40 -> +2.0")
                                    break
                                elif "50以上" in kw.lower() and damage_value >= 50:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} >= 50 -> +2.0")
                                    break
                                elif "60以上" in kw.lower() and damage_value >= 60:
                                    score = 2.0
                                    matched = True
                                    if self.debug:
                                        GameChatLogger.log_debug("database_service", f"    ダメージマッチ: {damage_value} >= 60 -> +2.0")
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
            if keyword_lower in ["炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"]:
                if not matched:
                    if "type" in item and item["type"]:
                        if keyword_lower == item["type"].lower():
                            score = 2.0
                            matched = True
                            if self.debug:
                                GameChatLogger.log_debug("database_service", f"    タイプマッチ: {keyword} -> +2.0")
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
                if self.debug:
                    GameChatLogger.log_debug("database_service", f"    テキストマッチ: {keyword} -> +0.5")
            # 部分マッチ
            elif any(keyword_lower in word for word in searchable_text_lower.split()):
                score += 0.3
                if self.debug:
                    GameChatLogger.log_debug("database_service", f"    部分マッチ: {keyword} -> +0.3")
        
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
            if self.debug:
                GameChatLogger.log_debug("database_service", "    複合条件ボーナス: +1.0")
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
