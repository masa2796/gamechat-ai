import re
import os
import json
import asyncio
import openai
from typing import List, Dict, Any, Optional
from ..core.logging import GameChatLogger
from ..core.config import settings
from ..core.exceptions import DatabaseServiceException

class DatabaseService:
    # 集約クエリパターン定数
    AGGREGATION_PATTERNS = {
        'max': r'(一番高い|最大|最高|トップ)\s*(HP|ダメージ|攻撃力|コスト)',
        'min': r'(一番低い|最小|最低|ボトム)\s*(HP|ダメージ|攻撃力|コスト)',
        'top_n': r'(上位|トップ)(\d+)位?\s*(の)?\s*(HP|ダメージ|攻撃力|コスト)'
    }
    
    # 複雑な数値パターン定数
    COMPLEX_NUMERIC_PATTERNS = {
        'range': r'(\d+)から(\d+)の間|(\d+)～(\d+)|(\d+)-(\d+)',
        'multiple': r'(\d+)または(\d+)|(\d+)か(\d+)',
        'approximate': r'約(\d+)|(\d+)程度|およそ(\d+)|(\d+)くらい'
    }
    
    # フィールドマッピング辞書（多様な表現に対応）
    FIELD_MAPPINGS = {
        'cost': ['コスト', 'cost', 'マナコスト', 'マナ', 'mana'],
        'hp': ['HP', 'hp', '体力', 'ヒットポイント', 'hitpoint', 'health'],
        'attack': ['攻撃力', '攻撃', 'ダメージ', 'attack', 'damage', 'アタック'],
        'name': ['名前', 'カード名', 'name', '名称'],
        'class': ['クラス', 'class', '職業', 'クラス名'],
        'rarity': ['レアリティ', 'rarity', '希少度'],
        'type': ['タイプ', 'type', '種族', '属性']
    }
    def __init__(self, data_path: Optional[str] = None):
        import os
        
        # テスト環境の判定
        is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        # data_pathが指定されていればそれを、なければプロジェクトルート基準の絶対パス
        if data_path:
            self.data_path = data_path
        else:
            # このファイル（database_service.py）から見てプロジェクトルートを計算
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
            self.data_path = os.path.join(base_dir, 'data/data.json')
        self.debug = False  # デバッグフラグ（パフォーマンス向上のため無効化）
        
        # LLM初期化
        self._init_llm()
        
        # テストモードの場合はファイル読み込みをスキップ
        if is_test_mode:
            # テスト用の空データで初期化
            self.storage_service = None
            self.data_cache: List[Dict[str, Any]] = []
            self.title_to_data: Dict[str, Dict[str, Any]] = {}
            # dataプロパティも空で初期化（テストで上書きされる）
            self.data = []
        else:
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

    def _init_llm(self) -> None:
        """LLMクライアントを初期化"""
        # モック環境のチェック
        mock_external = os.getenv("BACKEND_MOCK_EXTERNAL_SERVICES", "false").lower() == "true"
        is_testing = os.getenv("BACKEND_TESTING", "false").lower() == "true"
        
        if mock_external or is_testing:
            # モック環境では実際のOpenAIクライアントは初期化しない
            self.llm_client = None
            self.is_mocked = True
        else:
            # OpenAI クライアントを初期化
            import openai
            api_key = getattr(settings, 'BACKEND_OPENAI_API_KEY', None) or os.getenv("BACKEND_OPENAI_API_KEY")
            
            # APIキーの検証
            if not api_key or api_key in ["your_openai_api_key", "your_actual_openai_api_key_here", "sk-test_openai_key"]:
                print("[WARNING] OpenAI APIキーが設定されていません。LLMクエリ解析は無効になります。")
                self.llm_client = None
                self.is_mocked = True
            else:
                self.llm_client = openai.OpenAI(api_key=api_key)
                self.is_mocked = False
        
        # LLMクエリ解析用システムプロンプト
        self.query_analysis_prompt = """
あなたはカードゲームのデータベース検索クエリ解析アシスタントです。
ユーザーのクエリを解析し、構造化検索に必要な条件を抽出してください。

【データベーススキーマ】
cardsテーブル
- name: string（カード名）
- rarity: string（レアリティ）
- cost: integer（コスト）
- class: string（クラス）
- hp: integer（HP・体力 - スペルの場合は存在しない）
- attack: integer（攻撃力 - スペルの場合は存在しない）
- effect_1: string（メイン効果）
- effect_2: string（サブ効果・進化時効果等 - 存在する場合のみ）
- effect_3: string（追加効果 - 存在する場合のみ）
- type: string（タイプ・属性）
- keywords: array（効果キーワードのリスト：ファンファーレ、ラストワード、コンボ等）
- cv: string（声優名）
- illustrator: string（イラストレーター名）
- qa: array（Q&A情報）

【指示】
ユーザーのクエリから、以下のJSON形式で検索条件を抽出してください。
{
  "conditions": {
    "name": "<カード名または空文字>",
    "rarity": "<レアリティまたは空文字>", 
    "cost": {
      "value": <数値またはnull>,
      "operator": "<以上|以下|等しい|null>"
    },
    "class": "<クラスまたは空文字>",
    "hp": {
      "value": <数値またはnull>,
      "operator": "<以上|以下|等しい|null>"
    },
    "attack": {
      "value": <数値またはnull>,
      "operator": "<以上|以下|等しい|null>"
    },
    "type": "<タイプまたは空文字>",
    "effect": "<効果キーワードまたは空文字>",
    "keywords": ["<keywordsフィールドで検索するキーワードのリスト>"],
    "cv": "<声優名または空文字>",
    "illustrator": "<イラストレーター名または空文字>",
    "qa_search": "<Q&A内容での検索キーワードまたは空文字>"
  },
  "reasoning": "抽出理由"
}

【抽出ルール】
1. コスト・HP・攻撃力：「5コスト」「HP100以上」「体力50以下」「攻撃40以上」「ダメージ30以上」などから数値と条件を抽出
   - 範囲指定：「50から100の間」「50～100」「50-100」→ 範囲条件として抽出
   - 複数値：「50または60」「50か60」→ 複数値条件として抽出  
   - 近似値：「約50」「50程度」「およそ50」「50くらい」→ 近似値条件として抽出
2. クラス：「エルフ」「ドラゴン」「ロイヤル」「ウィッチ」「ネクロマンサー」「ビショップ」「ネメシス」「ヴァンパイア」「ニュートラル」「ナイトメア」
3. レアリティ：「レジェンド」「ゴールドレア」「シルバーレア」「ブロンズレア」
4. タイプ・属性：「ルミナス」「土の印」「マナリア」「レヴィオン」「アナテマ」など
5. 効果：「進化」「必殺」「守護」「疾走」「突進」「回復」「ドロー」「サーチ」などの効果キーワード
6. keywords：「ファンファーレ」「ラストワード」「コンボ」「覚醒」「土の印」「スペルブースト」「ネクロマンス」「エンハンス」「アクセラレート」「チョイス」「融合」「交戦時」「超進化時」「攻撃時」「疾走」「守護」「突進」「必殺」「潜伏」「進化時」「アクト」「カウントダウン」「バリア」「モード」「土の秘術」「リアニメイト」「威圧」「オーラ」「ドレイン」「アポカリプスデッキ」など
7. 「ダメージ」「攻撃」は attack フィールドとして扱う
8. 声優：「門脇舞以」「日笠陽子」など cv フィールドで検索
9. イラストレーター：「ツネくん」「やまもも」など illustrator フィールドで検索
10. Q&A検索：「使い方」「効果の詳細」「ルール」などはqa_searchフィールドで検索
11. 抽出できない場合は空文字またはnullまたは空配列を設定

【例1】
ユーザー: 「5コストのレジェンドカードを探して」
出力:
{
  "conditions": {
    "name": "",
    "rarity": "レジェンド",
    "cost": {
      "value": 5,
      "operator": "等しい"
    },
    "class": "",
    "hp": {
      "value": null,
      "operator": null
    },
    "attack": {
      "value": null,
      "operator": null
    },
    "type": "",
    "effect": "",
    "keywords": [],
    "cv": "",
    "illustrator": "",
    "qa_search": ""
  },
  "reasoning": "5コストの条件とレジェンドレアリティを抽出"
}

【例2】
ユーザー: 「ダメージが40以上の技を持つ、水タイプカード」
出力:
{
  "conditions": {
    "name": "",
    "rarity": "",
    "cost": {
      "value": null,
      "operator": null
    },
    "class": "",
    "hp": {
      "value": null,
      "operator": null
    },
    "attack": {
      "value": 40,
      "operator": "以上"
    },
    "type": "水",
    "effect": "",
    "keywords": [],
    "cv": "",
    "illustrator": "",
    "qa_search": ""
  },
  "reasoning": "ダメージ40以上の条件と水タイプを抽出"
}

【例3】
ユーザー: 「ファンファーレ効果を持つエルフカード」
出力:
{
  "conditions": {
    "name": "",
    "rarity": "",
    "cost": {
      "value": null,
      "operator": null
    },
    "class": "エルフ",
    "hp": {
      "value": null,
      "operator": null
    },
    "attack": {
      "value": null,
      "operator": null
    },
    "type": "",
    "effect": "",
    "keywords": ["ファンファーレ"],
    "cv": "",
    "illustrator": "",
    "qa_search": ""
  },
  "reasoning": "エルフクラスとファンファーレキーワードを抽出"
}

【例4】
ユーザー: 「門脇舞以が声優のカードの使い方を教えて」
出力:
{
  "conditions": {
    "name": "",
    "rarity": "",
    "cost": {
      "value": null,
      "operator": null
    },
    "class": "",
    "hp": {
      "value": null,
      "operator": null
    },
    "attack": {
      "value": null,
      "operator": null
    },
    "type": "",
    "effect": "",
    "keywords": [],
    "cv": "門脇舞以",
    "illustrator": "",
    "qa_search": "使い方"
  },
  "reasoning": "声優条件とQ&A検索条件を抽出"
}

【例5】
ユーザー: 「交戦時に能力を発動するカード」
出力:
{
  "conditions": {
    "name": "",
    "rarity": "",
    "cost": {
      "value": null,
      "operator": null
    },
    "class": "",
    "hp": {
      "value": null,
      "operator": null
    },
    "attack": {
      "value": null,
      "operator": null
    },
    "type": "",
    "effect": "",
    "keywords": ["交戦時"],
    "cv": "",
    "illustrator": "",
    "qa_search": ""
  },
  "reasoning": "交戦時のキーワード効果を抽出"
}

必ずJSONのみで回答してください。他の文章は含めないでください。
"""

    def _load_data(self) -> list[dict[str, Any]]:
        # テスト用: StorageServiceのload_json_dataを呼ぶ
        if self.storage_service is not None and hasattr(self.storage_service, "load_json_data"):
            return self.storage_service.load_json_data()
        elif self.storage_service is not None and hasattr(self.storage_service, "load_data"):
            return self.storage_service.load_data()
        return []

    @property
    def data(self) -> List[Dict[str, Any]]:
        """テスト用のdataプロパティ - data_cacheへのアクセサ"""
        return getattr(self, 'data_cache', [])
    
    @data.setter
    def data(self, value: List[Dict[str, Any]]) -> None:
        """テスト用のdataプロパティセッター"""
        self.data_cache = value
        # title_to_dataマッピングも更新
        self.title_to_data = {}
        if value:
            for item in value:
                title = item.get("title") or item.get("name")
                if title:
                    self.title_to_data[title] = item

    def _detect_aggregation_query(self, query: str) -> Dict[str, Any]:
        """集約クエリの検出"""
        aggregation_info: Dict[str, Any] = {
            "is_aggregation": False,
            "aggregation_type": None,  # Optional[str] - 'max', 'min', 'top_n'
            "field": None,  # Optional[str] - 'hp', 'attack', 'cost'
            "count": None  # Optional[int] - top_nの場合の件数
        }
        
        # 各パターンをチェック
        for agg_type, pattern in self.AGGREGATION_PATTERNS.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                aggregation_info["is_aggregation"] = True
                aggregation_info["aggregation_type"] = agg_type  # str を代入
                
                # フィールド名の正規化
                if agg_type == "top_n":
                    # top_nパターンの場合: グループ4がフィールド名
                    field_text = match.group(4) if len(match.groups()) >= 4 else ""
                else:
                    # max/minパターンの場合: グループ2がフィールド名
                    field_text = match.group(2) if len(match.groups()) >= 2 else ""
                    
                field_mapping = {
                    "HP": "hp",
                    "ダメージ": "attack", 
                    "攻撃力": "attack",
                    "コスト": "cost"
                }
                aggregation_info["field"] = field_mapping.get(field_text, field_text.lower())  # str を代入
                
                # top_nの場合は件数を抽出
                if agg_type == "top_n" and len(match.groups()) >= 2:
                    try:
                        aggregation_info["count"] = int(match.group(2))  # int を代入
                    except (ValueError, TypeError):
                        aggregation_info["count"] = 5  # デフォルト値 int を代入
                break
                
        return aggregation_info

    def _parse_aggregation_condition(self, query: str) -> Dict[str, Any]:
        """集約クエリ条件のパース"""
        aggregation_info = self._detect_aggregation_query(query)
        
        if not aggregation_info["is_aggregation"]:
            return {}
            
        return {
            "aggregation": aggregation_info,
            "reasoning": f"集約クエリを検出: {aggregation_info['aggregation_type']} {aggregation_info['field']}"
        }

    def _extract_numeric_field(self, item: Dict[str, Any], field: str) -> Optional[float]:
        """アイテムから数値フィールドを抽出"""
        try:
            value = item.get(field)
            if value is None:
                return None
            return float(value)
        except (ValueError, TypeError):
            return None

    def _sort_by_field(self, items: List[Dict[str, Any]], field: str, reverse: bool = False) -> List[Dict[str, Any]]:
        """指定フィールドでソート"""
        def sort_key(item: Dict[str, Any]) -> float:
            value = self._extract_numeric_field(item, field)
            return value if value is not None else -1.0
        
        return sorted(items, key=sort_key, reverse=reverse)

    def _get_max_value_items(self, items: List[Dict[str, Any]], field: str) -> List[Dict[str, Any]]:
        """最大値を持つアイテムを取得"""
        if not items:
            return []
        
        # 有効な数値を持つアイテムのみを対象
        valid_items = [item for item in items if self._extract_numeric_field(item, field) is not None]
        if not valid_items:
            return []
        
        # 最大値を取得
        valid_numeric_values = [self._extract_numeric_field(item, field) for item in valid_items]
        filtered_values = [v for v in valid_numeric_values if v is not None]
        if not filtered_values:
            return []
        max_value = max(filtered_values)
        
        # 最大値を持つ全てのアイテムを返す
        return [item for item in valid_items if self._extract_numeric_field(item, field) == max_value]

    def _get_min_value_items(self, items: List[Dict[str, Any]], field: str) -> List[Dict[str, Any]]:
        """最小値を持つアイテムを取得"""
        if not items:
            return []
        
        # 有効な数値を持つアイテムのみを対象
        valid_items = [item for item in items if self._extract_numeric_field(item, field) is not None]
        if not valid_items:
            return []
        
        # 最小値を取得
        valid_numeric_values = [self._extract_numeric_field(item, field) for item in valid_items]
        filtered_values = [v for v in valid_numeric_values if v is not None]
        if not filtered_values:
            return []
        min_value = min(filtered_values)
        
        # 最小値を持つ全てのアイテムを返す
        return [item for item in valid_items if self._extract_numeric_field(item, field) == min_value]

    def _get_top_n_items(self, items: List[Dict[str, Any]], field: str, count: int) -> List[Dict[str, Any]]:
        """上位N件のアイテムを取得"""
        if not items or count <= 0:
            return []
        
        # 有効な数値を持つアイテムのみを対象
        valid_items = [item for item in items if self._extract_numeric_field(item, field) is not None]
        if not valid_items:
            return []
        
        # フィールド値で降順ソート（高い値から順に）
        sorted_items = self._sort_by_field(valid_items, field, reverse=True)
        
        # 上位N件を返す
        return sorted_items[:count]

    def _parse_complex_numeric_conditions(self, query: str) -> Dict[str, Any]:
        """複雑な数値条件のパース（範囲指定、複数値、近似値）"""
        complex_conditions: Dict[str, List[Dict[str, Any]]] = {
            "range_conditions": [],
            "multiple_conditions": [],
            "approximate_conditions": []
        }
        
        import re
        
        # 範囲指定パターンの検出
        range_pattern = self.COMPLEX_NUMERIC_PATTERNS['range']
        for match in re.finditer(range_pattern, query):
            # パターンに応じて数値を抽出
            if match.group(1) and match.group(2):  # "NからMの間"
                min_val, max_val = int(match.group(1)), int(match.group(2))
            elif match.group(3) and match.group(4):  # "N～M"
                min_val, max_val = int(match.group(3)), int(match.group(4))
            elif match.group(5) and match.group(6):  # "N-M"
                min_val, max_val = int(match.group(5)), int(match.group(6))
            else:
                continue
                
            # 最小値と最大値の順序を正す
            if min_val > max_val:
                min_val, max_val = max_val, min_val
                
            # フィールドを特定
            field = self._identify_field_in_context(query, match.start(), match.end())
            complex_conditions["range_conditions"].append({
                "field": field,
                "min_value": min_val,
                "max_value": max_val,
                "original_text": match.group(0)
            })
        
        # 複数値パターンの検出
        multiple_pattern = self.COMPLEX_NUMERIC_PATTERNS['multiple']
        for match in re.finditer(multiple_pattern, query):
            if match.group(1) and match.group(2):  # "NまたはM"
                val1, val2 = int(match.group(1)), int(match.group(2))
            elif match.group(3) and match.group(4):  # "NかM"
                val1, val2 = int(match.group(3)), int(match.group(4))
            else:
                continue
                
            field = self._identify_field_in_context(query, match.start(), match.end())
            complex_conditions["multiple_conditions"].append({
                "field": field,
                "values": [val1, val2],
                "original_text": match.group(0)
            })
        
        # 近似値パターンの検出
        approximate_pattern = self.COMPLEX_NUMERIC_PATTERNS['approximate']
        for match in re.finditer(approximate_pattern, query):
            if match.group(1):  # "約N"
                value = int(match.group(1))
            elif match.group(2):  # "N程度"
                value = int(match.group(2))
            elif match.group(3):  # "およそN"
                value = int(match.group(3))
            elif match.group(4):  # "Nくらい"
                value = int(match.group(4))
            else:
                continue
                
            field = self._identify_field_in_context(query, match.start(), match.end())
            complex_conditions["approximate_conditions"].append({
                "field": field,
                "value": value,
                "tolerance": max(5, value * 0.1),  # 10%の許容範囲（最小5）
                "original_text": match.group(0)
            })
        
        return complex_conditions

    def _identify_field_in_context(self, query: str, start_pos: int, end_pos: int) -> str:
        """クエリ内の位置からフィールド名を特定"""
        # 数値パターンの前後20文字を解析対象とする
        context_start = max(0, start_pos - 20)
        context_end = min(len(query), end_pos + 20)
        context = query[context_start:context_end].lower()
        
        # フィールドマッピングを使用して最適なフィールドを特定
        for field, aliases in self.FIELD_MAPPINGS.items():
            for alias in aliases:
                if alias.lower() in context:
                    return field
        
        # デフォルトは'unknown'
        return 'unknown'

    def _normalize_field_name(self, field_input: str) -> str:
        """多様なフィールド名表現を正規化"""
        field_lower = field_input.lower()
        
        for standard_field, aliases in self.FIELD_MAPPINGS.items():
            for alias in aliases:
                if alias.lower() == field_lower or alias.lower() in field_lower:
                    return standard_field
        
        return field_input  # 正規化できない場合はそのまま返す

    def _match_complex_numeric_condition(self, item: Dict[str, Any], condition: Dict[str, Any], condition_type: str) -> bool:
        """複雑な数値条件のマッチング"""
        field = condition.get("field", "unknown")
        if field == "unknown":
            return False
            
        # アイテムから対象フィールドの値を取得
        item_value = self._extract_numeric_field(item, field)
        if item_value is None:
            return False
        
        try:
            if condition_type == "range":
                # 範囲条件のチェック
                min_val = float(condition["min_value"])
                max_val = float(condition["max_value"])
                return bool(min_val <= item_value <= max_val)
                
            elif condition_type == "multiple":
                # 複数値条件のチェック
                values = condition["values"]
                return bool(item_value in values)
                
            elif condition_type == "approximate":
                # 近似値条件のチェック
                target_value = float(condition["value"])
                tolerance = float(condition["tolerance"])
                return bool(abs(item_value - target_value) <= tolerance)
                
        except (ValueError, TypeError):
            return False
        
        return False

    async def _analyze_query_with_llm(self, query: str) -> Dict[str, Any]:
        """LLMを使用してクエリを解析し、構造化された検索条件を抽出"""
        if self.is_mocked or self.llm_client is None:
            # モック環境の場合はダミーデータを返す
            return self._get_mock_query_analysis(query)
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.query_analysis_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            if content is None:
                return {}
            
            content = content.strip()
            if self.debug:
                print(f"[DEBUG] LLM Response: {content}")
            
            # JSONをパース
            analysis_result: dict[str, Any] = json.loads(content)
            return analysis_result
            
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] LLMクエリ解析エラー: {e}")
            # エラー時はフォールバックとしてダミーデータを返す
            return self._get_mock_query_analysis(query)
    
    def _get_mock_query_analysis(self, query: str) -> Dict[str, Any]:
        """テスト・モック環境用のクエリ解析（拡張版）"""
        # 簡単なパターンマッチングでモック解析
        conditions = {
            "name": "",
            "rarity": "",
            "cost": {"value": None, "operator": None},
            "class": "",
            "hp": {"value": None, "operator": None},
            "attack": {"value": None, "operator": None},
            "type": "",
            "effect": "",
            "keywords": [],
            "cv": "",
            "illustrator": "",
            "qa_search": ""
        }
        
        import re
        
        # コスト検出
        cost_match = re.search(r'(\d+)コスト|コスト(\d+)', query)
        if cost_match:
            cost_val = int(cost_match.group(1) or cost_match.group(2))
            conditions["cost"] = {"value": cost_val, "operator": "等しい"}
        
        # HP検出
        hp_match = re.search(r'HP(\d+)(以上|以下)|体力(\d+)(以上|以下)', query)
        if hp_match:
            hp_val = int(hp_match.group(1) or hp_match.group(3))
            operator = hp_match.group(2) or hp_match.group(4)
            conditions["hp"] = {"value": hp_val, "operator": operator}
        
        # 攻撃力・ダメージ検出
        attack_match = re.search(r'攻撃(\d+)(以上|以下)|ダメージ(\d+)(以上|以上)', query)
        if attack_match:
            attack_val = int(attack_match.group(1) or attack_match.group(3))
            operator = attack_match.group(2) or attack_match.group(4) or "以上"
            conditions["attack"] = {"value": attack_val, "operator": operator}
        
        # クラス検出
        classes = ["エルフ", "ドラゴン", "ロイヤル", "ウィッチ", "ネクロマンサー", "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル", "ナイトメア"]
        for cls in classes:
            if cls in query:
                conditions["class"] = cls
                break
        
        # レアリティ検出
        rarities = ["レジェンド", "ゴールドレア", "シルバーレア", "ブロンズレア"]
        for rarity in rarities:
            if rarity in query:
                conditions["rarity"] = rarity
                break
        
        # タイプ検出
        types = ["ルミナス", "土の印", "マナリア", "レヴィオン", "アナテマ"]
        for card_type in types:
            if card_type in query:
                conditions["type"] = card_type
                break
        
        # keywordsフィールド用のキーワード検出（疾走・守護などを含む）
        keyword_effects = [
            "ファンファーレ", "ラストワード", "コンボ", "覚醒", "土の印", "スペルブースト", 
            "ネクロマンス", "エンハンス", "アクセラレート", "チョイス", "融合",
            "疾走", "守護", "突進", "必殺", "潜伏", "進化時", "超進化時", "アクト",
            "カウントダウン", "バリア", "モード", "土の秘術", "リアニメイト", "攻撃時",
            "威圧", "オーラ", "ドレイン", "交戦時", "アポカリプスデッキ"
        ]
        detected_keywords = []
        for keyword in keyword_effects:
            if keyword in query:
                detected_keywords.append(keyword)
        if detected_keywords:
            conditions["keywords"] = detected_keywords
        
        # 効果キーワード検出（keywordsフィールドにないもの）
        effects = ["進化", "回復", "ドロー", "サーチ", "召喚", "破壊"]
        for effect in effects:
            if effect in query and effect not in detected_keywords:
                conditions["effect"] = effect
                break
        
        # 声優検出
        cv_names = ["門脇舞以", "日笠陽子", "内田雄馬", "辻あゆみ", "潘めぐみ"]
        for cv in cv_names:
            if cv in query:
                conditions["cv"] = cv
                break
        
        # イラストレーター検出
        illustrator_names = ["ツネくん", "やまもも", "伊吹つくば", "misekiss", "言犬", "林", "りょうへい", "あかかがち"]
        for illustrator in illustrator_names:
            if illustrator in query:
                conditions["illustrator"] = illustrator
                break
        
        # Q&A検索検出
        qa_keywords = ["使い方", "効果", "ルール", "働く", "できる", "プレイ", "場合", "とき"]
        for qa_keyword in qa_keywords:
            if qa_keyword in query:
                conditions["qa_search"] = qa_keyword
                break
        
        # Phase 2: 複雑な数値パターンの検出（モック環境用）
        # 範囲指定パターンの検出
        range_patterns = [
            r'HP(\d+)から(\d+)の間',
            r'攻撃力(\d+)～(\d+)',
            r'コスト(\d+)-(\d+)',
            r'ダメージ(\d+)から(\d+)の間'
        ]
        for pattern in range_patterns:
            match = re.search(pattern, query)
            if match:
                min_val, max_val = int(match.group(1)), int(match.group(2))
                if 'HP' in pattern:
                    conditions["hp"] = {"value": min_val, "operator": "範囲", "max_value": max_val}
                elif '攻撃力' in pattern or 'ダメージ' in pattern:
                    conditions["attack"] = {"value": min_val, "operator": "範囲", "max_value": max_val}
                elif 'コスト' in pattern:
                    conditions["cost"] = {"value": min_val, "operator": "範囲", "max_value": max_val}
                break
        
        # 複数値パターンの検出
        multiple_patterns = [
            r'攻撃力(\d+)または(\d+)',
            r'攻撃力(\d+)か(\d+)',
            r'HP(\d+)または(\d+)',
            r'HP(\d+)か(\d+)',
            r'コスト(\d+)または(\d+)',
            r'コスト(\d+)か(\d+)'
        ]
        for pattern in multiple_patterns:
            match = re.search(pattern, query)
            if match:
                val1, val2 = int(match.group(1)), int(match.group(2))
                if '攻撃力' in pattern:
                    conditions["attack"] = {"value": val1, "operator": "複数値", "additional_values": [val2]}
                elif 'HP' in pattern:
                    conditions["hp"] = {"value": val1, "operator": "複数値", "additional_values": [val2]}
                elif 'コスト' in pattern:
                    conditions["cost"] = {"value": val1, "operator": "複数値", "additional_values": [val2]}
                break
        
        # 近似値パターンの検出
        approximate_patterns = [
            r'約HP(\d+)|HP(\d+)程度',
            r'約攻撃力(\d+)|攻撃力(\d+)程度',
            r'約コスト(\d+)|コスト(\d+)程度'
        ]
        for pattern in approximate_patterns:
            match = re.search(pattern, query)
            if match:
                value = int(match.group(1) or match.group(2))
                if 'HP' in pattern:
                    conditions["hp"] = {"value": value, "operator": "近似"}
                elif '攻撃力' in pattern:
                    conditions["attack"] = {"value": value, "operator": "近似"}
                elif 'コスト' in pattern:
                    conditions["cost"] = {"value": value, "operator": "近似"}
                break
        
        return {
            "conditions": conditions,
            "reasoning": f"モック環境でのクエリ解析: {query}"
        }
    async def filter_search_async(self, keywords: list[str], top_k: int = 10) -> list[str]:
        # 空キーワードまたはデータが空なら即空リスト返却
        if not keywords or not self.data_cache:
            return []
            
        # キーワードを自然言語クエリとして結合してLLMベース検索を優先
        query = " ".join(keywords)
        
        # LLMベース検索を実行
        try:
            result = await self.filter_search_llm_async(query, top_k)
            if result:  # LLMで結果が得られた場合
                return result
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] LLM検索エラー、フォールバックに切り替え: {e}")
        
        # フォールバック: 従来の正規表現ベース検索
        result = await self.filter_search_titles_async(keywords, top_k)
        return result

    async def filter_search_llm_async(self, query: str, top_k: int = 10) -> list[str]:
        """LLMベースのフィルタ検索（カード名リストを返す）"""
        
        # データが空なら即空リスト返却
        if not self.data_cache:
            return []
        
        # LLMベースの検索を実行
        results = await self._search_filterable_llm(query, top_k)
        
        # カード名リストに変換
        card_names = [item.get("name", "") for item in results if item.get("name")]
        
        return card_names

    def filter_search(self, keywords: list[str], top_k: int = 10) -> list[str]:
        result = asyncio.get_event_loop().run_until_complete(self.filter_search_async(keywords, top_k))
        return result

    def _filter_search_sync(self, keywords: list[str], top_k: int = 10) -> list[str]:
        """同期版フィルタ検索（LLMベースを優先、フォールバックのみ同期）"""
        if not keywords or not self.data_cache:
            return []
        
        # 複雑なクエリがある場合は事前に分割
        processed_keywords = []
        for kw in keywords:
            if len(kw) > 15 and any(word in kw for word in ["クラス", "コスト", "攻撃", "HP", "かつ", "で"]):
                # 自然言語クエリと判断して分割
                split_kws = self._split_query_to_keywords(kw)
                processed_keywords.extend(split_kws)
            else:
                # 通常のキーワードとして処理
                processed_keywords.append(kw)
        
        normalized = [self._normalize_keyword(kw) for kw in processed_keywords]
        expanded = self._split_keywords(normalized)
        if not expanded:
            return []
        
        # 同期版では正規表現ベースのフォールバック処理のみ使用
        results = []
        for item in self.data_cache:
            # 全てのキーワードに対してフォールバック処理でマッチング判定
            match_flags = []
            for kw in expanded:
                # 高速なフォールバック処理を使用（LLM解析をスキップ）
                match_result = self._match_filterable_fallback(item, kw)
                match_flags.append(match_result)
            
            if all(match_flags):
                name = item.get("name")
                if name:
                    results.append(name)
            if len(results) >= top_k:
                break
        return results

    def filter_search_llm(self, query: str, top_k: int = 10) -> list[str]:
        """LLMベースのフィルタ検索（同期版）"""
        result = asyncio.get_event_loop().run_until_complete(self.filter_search_llm_async(query, top_k))
        return result

    async def smart_search_llm(self, query: str, top_k: int = 10) -> list[str]:
        """LLMベースの統合スマート検索（自然言語クエリから直接カード名リストを返す）"""
        
        # LLMでクエリ全体を解析
        query_analysis = await self._analyze_query_with_llm(query)
        if self.debug:
            print(f"[DEBUG] スマート検索クエリ解析結果: {query_analysis}")
        
        results = []
        for item in self.data_cache:
            if await self._match_filterable_llm(item, query_analysis):
                name = item.get("name")
                if name:
                    results.append(name)
                if len(results) >= top_k:
                    break
        
        return results

    async def smart_filter_search_async(self, query_input: str, top_k: int = 10, use_llm: bool = True) -> list[str]:
        """統合検索メソッド（LLMの有効/無効を切り替え可能）"""
        
        if use_llm:
            # LLM解析ベース検索を使用
            try:
                result = await self.filter_search_llm_async(query_input, top_k)
                if result:  # LLMで結果が得られた場合
                    return result
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] LLM検索エラー、正規表現ベースにフォールバック: {e}")
        
        # フォールバック: 従来のキーワード検索を使用（クエリを簡単にキーワードに分割）
        keywords = self._split_query_to_keywords(query_input)
        return await self.filter_search_titles_async(keywords, top_k)
    
    def _split_query_to_keywords(self, query: str) -> list[str]:
        """クエリを検索可能なキーワードに分割（改善版）"""
        import re
        keywords = []
        
        # 1. クラス名を抽出
        classes = ["エルフ", "ドラゴン", "ロイヤル", "ウィッチ", "ネクロマンサー", "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル", "ナイトメア"]
        for cls in classes:
            if cls in query:
                keywords.append(cls)
        
        # 2. コスト条件を抽出
        cost_patterns = [
            r'コスト(\d+)',
            r'(\d+)コスト',
            r'コストが(\d+)'
        ]
        for pattern in cost_patterns:
            match = re.search(pattern, query)
            if match:
                cost_val = match.group(1)
                keywords.append(f'コスト{cost_val}')
                break
        
        # 3. 攻撃力条件を抽出
        attack_patterns = [
            r'攻撃力が(\d+)',
            r'攻撃力(\d+)',
            r'攻撃(\d+)',
            r'ダメージ(\d+)'
        ]
        for pattern in attack_patterns:
            match = re.search(pattern, query)
            if match:
                attack_val = match.group(1)
                keywords.append(f'攻撃{attack_val}')
                break
        
        # 4. HP条件を抽出
        hp_patterns = [
            r'HPが(\d+)',
            r'HP(\d+)',
            r'体力が(\d+)',
            r'体力(\d+)'
        ]
        for pattern in hp_patterns:
            match = re.search(pattern, query)
            if match:
                hp_val = match.group(1)
                keywords.append(f'HP{hp_val}')
                break
        
        # 5. レアリティを抽出
        rarities = ["レジェンド", "ゴールドレア", "シルバーレア", "ブロンズレア"]
        for rarity in rarities:
            if rarity in query:
                keywords.append(rarity)
        
        # 6. タイプを抽出
        types = ["ルミナス", "土の印", "マナリア", "レヴィオン", "アナテマ"]
        for card_type in types:
            if card_type in query:
                keywords.append(card_type)
        
        # 空文字列や重複を除去
        return list(set(kw for kw in keywords if kw.strip()))

    def reload_data(self) -> None:
        """
        データを再読み込みし、キャッシュとtitle_to_dataを構築
        """
        try:
            data = self._load_data()
            self.data_cache = data
            self.title_to_data = {}
            
            # インデックス構築
            for item in data:
                # nameフィールドがキー（正規化処理を強化）
                name = item.get("name")
                if name:
                    norm_name = self._normalize_title(str(name))
                    self.title_to_data[norm_name] = item
                    
            if self.debug:
                print(f"[DEBUG] データリロード完了: {len(data)}件のカード, {len(self.title_to_data)}件のインデックス")
                
        except Exception as e:
            print(f"[ERROR] データリロード失敗: {e}")
            self.data_cache = []
            self.title_to_data = {}
            raise DatabaseServiceException(f"データベースの初期化に失敗しました: {e}")

    def validate_data_integrity(self) -> dict[str, Any]:
        """データ整合性チェック"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
            
        issues: dict[str, list[str]] = {
            "missing_fields": [],
            "invalid_values": [],
            "duplicate_ids": [],
            "duplicate_names": []
        }
        
        seen_ids = set()
        seen_names = set()
        required_fields = ["id", "name", "class", "rarity", "cost"]
        
        for i, item in enumerate(self.data_cache):
            # 必須フィールドチェック
            for field in required_fields:
                if field not in item or item[field] is None or str(item[field]).strip() == "":
                    issues["missing_fields"].append(f"項目{i}: {field}フィールドが不正")
            
            # 数値フィールドチェック
            for field in ["cost", "hp", "attack"]:
                if field in item and item[field] is not None:
                    try:
                        int(item[field])
                    except (ValueError, TypeError):
                        issues["invalid_values"].append(f"項目{i}: {field}={item[field]}は数値ではない")
            
            # ID重複チェック
            card_id = str(item.get("id", ""))
            if card_id in seen_ids:
                issues["duplicate_ids"].append(f"項目{i}: ID {card_id} が重複")
            seen_ids.add(card_id)
            
            # 名前重複チェック
            name = str(item.get("name", ""))
            if name in seen_names:
                issues["duplicate_names"].append(f"項目{i}: 名前 {name} が重複")
            seen_names.add(name)
        
        return {
            "total_cards": len(self.data_cache),
            "issues_found": sum(len(v) for v in issues.values()),
            "details": issues
        }

    def get_cache_info(self) -> dict[str, Any]:
        """キャッシュ情報取得"""
        return {
            "data_cache_loaded": hasattr(self, "data_cache") and self.data_cache is not None,
            "data_cache_size": len(self.data_cache) if hasattr(self, "data_cache") and self.data_cache else 0,
            "title_to_data_loaded": hasattr(self, "title_to_data") and self.title_to_data is not None,
            "title_to_data_size": len(self.title_to_data) if hasattr(self, "title_to_data") and self.title_to_data else 0,
            "data_path": self.data_path,
            "debug_mode": self.debug,
            "llm_mocked": self.is_mocked
        }
    async def _search_filterable(self, keywords: list[str], top_k: int = 10) -> list[dict[str, Any]]:
        """最適化されたフィルタ検索（LLMベースを優先）"""
        
        # キーワードを自然言語クエリとして結合
        query = " ".join(keywords)
        
        # まずLLMベース検索を試行
        try:
            llm_results = await self._search_filterable_llm(query, top_k)
            if llm_results:  # LLMで結果が得られた場合
                return llm_results
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] LLMベース検索エラー、キーワード別解析にフォールバック: {e}")
        
        # フォールバック: 各キーワードに対してLLM解析を1回だけ実行
        keyword_analyses = {}
        for kw in keywords:
            try:
                keyword_analyses[kw] = await self._analyze_query_with_llm(kw)
                if self.debug:
                    print(f"[DEBUG] キーワード解析完了: {kw}")
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] キーワード解析エラー: {kw}, {e}")
                keyword_analyses[kw] = {}
        
        results = []
        for item in self.data_cache:
            # 全てのキーワードに対してマッチング判定（AND条件）
            match_flags = []
            for kw in keywords:
                if keyword_analyses[kw] is not None:
                    # LLM解析結果を使用
                    match_result = await self._match_filterable_llm(item, keyword_analyses[kw])
                else:
                    # フォールバック処理を使用
                    match_result = self._match_filterable_fallback(item, kw)
                match_flags.append(match_result)
            
            if all(match_flags):
                results.append(item)
                if len(results) >= top_k:
                    break
        
        return results

    async def _search_filterable_llm(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """LLMを使用したフィルタ検索（集約クエリ対応版）"""
        
        # 集約クエリかどうかをチェック
        aggregation_result = self._parse_aggregation_condition(query)
        
        if aggregation_result and aggregation_result.get("aggregation", {}).get("is_aggregation"):
            # 集約クエリの場合
            return await self._handle_aggregation_query(query, aggregation_result, top_k)
        
        # 通常のフィルタクエリの場合
        query_analysis = await self._analyze_query_with_llm(query)
        if self.debug:
            print(f"[DEBUG] クエリ解析結果: {query_analysis}")
        
        results = []
        for item in self.data_cache:
            if await self._match_filterable_llm(item, query_analysis):
                results.append(item)
                if len(results) >= top_k:
                    break
        
        return results

    async def _handle_aggregation_query(self, query: str, aggregation_result: Dict[str, Any], top_k: int = 10) -> list[dict[str, Any]]:
        """集約クエリの処理"""
        try:
            aggregation_info = aggregation_result.get("aggregation", {})
            agg_type = aggregation_info.get("aggregation_type")
            field = aggregation_info.get("field")
            count = aggregation_info.get("count", top_k)
            
            if not field:
                if self.debug:
                    print(f"[DEBUG] 集約クエリでフィールドが指定されていません: {aggregation_info}")
                return []
            
            # フィールドマッピングの検証
            valid_fields = ["hp", "attack", "cost"]
            if field not in valid_fields:
                if self.debug:
                    print(f"[DEBUG] 無効なフィールドです: {field}. 有効なフィールド: {valid_fields}")
                return []
            
            # 該当フィールドが存在するアイテムのみを対象とする
            valid_items = [item for item in self.data_cache if self._extract_numeric_field(item, field) is not None]
            
            if not valid_items:
                if self.debug:
                    print(f"[DEBUG] フィールド '{field}' を持つアイテムが見つかりません")
                return []
            
            if agg_type == "max":
                result = self._get_max_value_items(valid_items, field)
            elif agg_type == "min":
                result = self._get_min_value_items(valid_items, field)
            elif agg_type == "top_n":
                if count <= 0:
                    count = top_k
                result = self._get_top_n_items(valid_items, field, count)
            else:
                if self.debug:
                    print(f"[DEBUG] 未対応の集約タイプ: {agg_type}")
                return []
            
            if self.debug:
                print(f"[DEBUG] 集約クエリ結果: {len(result)}件 (タイプ: {agg_type}, フィールド: {field})")
            
            return result
            
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 集約クエリ処理エラー: {e}")
            return []

    async def _match_filterable_llm(self, item: Dict[str, Any], query_analysis: Dict[str, Any]) -> bool:
        """LLM解析結果を使用してアイテムがフィルター条件に一致するかを判定（拡張版）"""
        if self.debug:
            print(f"[DEBUG] _match_filterable_llm: item={item.get('name', '')}")
        
        try:
            # 集約クエリの場合はスキップ（別途 _handle_aggregation_query で処理）
            if query_analysis.get("aggregation", {}).get("is_aggregation"):
                return True
            
            conditions = query_analysis.get("conditions", {})
            
            # 名前条件チェック
            name_condition = conditions.get("name", "")
            if name_condition and name_condition not in str(item.get("name", "")):
                if self.debug:
                    print(f"[DEBUG] 名前条件不一致: {name_condition} not in {item.get('name', '')}")
                return False
            
            # レアリティ条件チェック
            rarity_condition = conditions.get("rarity", "")
            if rarity_condition and str(item.get("rarity", "")) != rarity_condition:
                if self.debug:
                    print(f"[DEBUG] レアリティ条件不一致: {item.get('rarity', '')} != {rarity_condition}")
                return False
            
            # クラス条件チェック
            class_condition = conditions.get("class", "")
            if class_condition and str(item.get("class", "")) != class_condition:
                if self.debug:
                    print(f"[DEBUG] クラス条件不一致: {item.get('class', '')} != {class_condition}")
                return False
            
            # タイプ条件チェック
            type_condition = conditions.get("type", "")
            if type_condition:
                item_type = str(item.get("type", ""))
                if type_condition not in item_type:
                    if self.debug:
                        print(f"[DEBUG] タイプ条件不一致: {type_condition} not in {item_type}")
                    return False
            
            # 効果条件チェック
            effect_condition = conditions.get("effect", "")
            if effect_condition:
                # effect_1, effect_2, effect_3すべてで検索
                effect_found = False
                for effect_field in ["effect_1", "effect_2", "effect_3"]:
                    item_effect = str(item.get(effect_field, ""))
                    if effect_condition in item_effect:
                        effect_found = True
                        break
                if not effect_found:
                    if self.debug:
                        print(f"[DEBUG] 効果条件不一致: {effect_condition} not found in effects")
                    return False
            
            # 声優条件チェック
            cv_condition = conditions.get("cv", "")
            if cv_condition and str(item.get("cv", "")) != cv_condition:
                if self.debug:
                    print(f"[DEBUG] 声優条件不一致: {item.get('cv', '')} != {cv_condition}")
                return False
            
            # イラストレーター条件チェック
            illustrator_condition = conditions.get("illustrator", "")
            if illustrator_condition and str(item.get("illustrator", "")) != illustrator_condition:
                if self.debug:
                    print(f"[DEBUG] イラストレーター条件不一致: {item.get('illustrator', '')} != {illustrator_condition}")
                return False
            
            # keywords条件チェック（新機能）
            keywords_conditions = conditions.get("keywords", [])
            if keywords_conditions and isinstance(keywords_conditions, list):
                item_keywords = item.get("keywords", [])
                if isinstance(item_keywords, list):
                    # すべてのkeyword条件がマッチするかチェック
                    for keyword_condition in keywords_conditions:
                        keyword_found = False
                        for item_keyword in item_keywords:
                            if keyword_condition.lower() in item_keyword.lower() or item_keyword.lower() in keyword_condition.lower():
                                keyword_found = True
                                break
                        if not keyword_found:
                            if self.debug:
                                print(f"[DEBUG] keywords条件不一致: '{keyword_condition}' not found in {item_keywords}")
                            return False
                    if self.debug:
                        print(f"[DEBUG] keywords条件一致: {keywords_conditions} found in {item_keywords}")
                else:
                    # keywordsフィールドがない場合は条件不一致
                    if self.debug:
                        print("[DEBUG] keywords条件不一致: keywordsフィールドがない")
                    return False
            
            # コスト条件チェック
            cost_condition = conditions.get("cost", {})
            if cost_condition.get("value") is not None:
                item_cost = int(item.get("cost", 0))
                cost_value = cost_condition["value"]
                cost_operator = cost_condition.get("operator", "等しい")
                
                # Phase 2: 複雑な数値条件のチェック
                if cost_operator == "範囲":
                    max_value = cost_condition.get("max_value", cost_value)
                    if not (cost_value <= item_cost <= max_value):
                        if self.debug:
                            print(f"[DEBUG] コスト範囲条件不一致: {item_cost} not in range [{cost_value}, {max_value}]")
                        return False
                elif cost_operator == "複数値":
                    additional_values = cost_condition.get("additional_values", [])
                    allowed_values = [cost_value] + additional_values
                    if item_cost not in allowed_values:
                        if self.debug:
                            print(f"[DEBUG] コスト複数値条件不一致: {item_cost} not in {allowed_values}")
                        return False
                elif cost_operator == "近似":
                    tolerance = max(1, cost_value * 0.2)  # コストは20%の許容範囲（最小1）
                    if abs(item_cost - cost_value) > tolerance:
                        if self.debug:
                            print(f"[DEBUG] コスト近似条件不一致: {item_cost} not within {tolerance} of {cost_value}")
                        return False
                elif cost_operator == "等しい" and item_cost != cost_value:
                    if self.debug:
                        print(f"[DEBUG] コスト条件不一致: {item_cost} != {cost_value}")
                    return False
                elif cost_operator == "以上" and item_cost < cost_value:
                    if self.debug:
                        print(f"[DEBUG] コスト条件不一致: {item_cost} < {cost_value}")
                    return False
                elif cost_operator == "以下" and item_cost > cost_value:
                    if self.debug:
                        print(f"[DEBUG] コスト条件不一致: {item_cost} > {cost_value}")
                    return False
            
            # HP条件チェック
            hp_condition = conditions.get("hp", {})
            if hp_condition.get("value") is not None:
                item_hp = int(item.get("hp", 0))
                hp_value = hp_condition["value"]
                hp_operator = hp_condition.get("operator", "以上")
                
                # Phase 2: 複雑な数値条件のチェック
                if hp_operator == "範囲":
                    max_value = hp_condition.get("max_value", hp_value)
                    if not (hp_value <= item_hp <= max_value):
                        if self.debug:
                            print(f"[DEBUG] HP範囲条件不一致: {item_hp} not in range [{hp_value}, {max_value}]")
                        return False
                elif hp_operator == "複数値":
                    additional_values = hp_condition.get("additional_values", [])
                    allowed_values = [hp_value] + additional_values
                    if item_hp not in allowed_values:
                        if self.debug:
                            print(f"[DEBUG] HP複数値条件不一致: {item_hp} not in {allowed_values}")
                        return False
                elif hp_operator == "近似":
                    tolerance = max(5, hp_value * 0.1)  # 10%の許容範囲（最小5）
                    if abs(item_hp - hp_value) > tolerance:
                        if self.debug:
                            print(f"[DEBUG] HP近似条件不一致: {item_hp} not within {tolerance} of {hp_value}")
                        return False
                elif hp_operator == "等しい" and item_hp != hp_value:
                    if self.debug:
                        print(f"[DEBUG] HP条件不一致: {item_hp} != {hp_value}")
                    return False
                elif hp_operator == "以上" and item_hp < hp_value:
                    if self.debug:
                        print(f"[DEBUG] HP条件不一致: {item_hp} < {hp_value}")
                    return False
                elif hp_operator == "以下" and item_hp > hp_value:
                    if self.debug:
                        print(f"[DEBUG] HP条件不一致: {item_hp} > {hp_value}")
                    return False
            
            # 攻撃力条件チェック
            attack_condition = conditions.get("attack", {})
            if attack_condition.get("value") is not None:
                item_attack = int(item.get("attack", 0))
                attack_value = attack_condition["value"]
                attack_operator = attack_condition.get("operator", "以上")
                
                # Phase 2: 複雑な数値条件のチェック
                if attack_operator == "範囲":
                    max_value = attack_condition.get("max_value", attack_value)
                    if not (attack_value <= item_attack <= max_value):
                        if self.debug:
                            print(f"[DEBUG] 攻撃力範囲条件不一致: {item_attack} not in range [{attack_value}, {max_value}]")
                        return False
                elif attack_operator == "複数値":
                    additional_values = attack_condition.get("additional_values", [])
                    allowed_values = [attack_value] + additional_values
                    if item_attack not in allowed_values:
                        if self.debug:
                            print(f"[DEBUG] 攻撃力複数値条件不一致: {item_attack} not in {allowed_values}")
                        return False
                elif attack_operator == "近似":
                    tolerance = max(5, attack_value * 0.1)  # 10%の許容範囲（最小5）
                    if abs(item_attack - attack_value) > tolerance:
                        if self.debug:
                            print(f"[DEBUG] 攻撃力近似条件不一致: {item_attack} not within {tolerance} of {attack_value}")
                        return False
                elif attack_operator == "等しい" and item_attack != attack_value:
                    if self.debug:
                        print(f"[DEBUG] 攻撃力条件不一致: {item_attack} != {attack_value}")
                    return False
                elif attack_operator == "以上" and item_attack < attack_value:
                    if self.debug:
                        print(f"[DEBUG] 攻撃力条件不一致: {item_attack} < {attack_value}")
                    return False
                elif attack_operator == "以下" and item_attack > attack_value:
                    if self.debug:
                        print(f"[DEBUG] 攻撃力条件不一致: {item_attack} > {attack_value}")
                    return False
            
            # Q&A検索条件チェック
            qa_search_condition = conditions.get("qa_search", "")
            if qa_search_condition:
                qa_data = item.get("qa", [])
                qa_found = False
                if isinstance(qa_data, list):
                    for qa in qa_data:
                        if isinstance(qa, dict):
                            question = str(qa.get("question", ""))
                            answer = str(qa.get("answer", ""))
                            if qa_search_condition in question or qa_search_condition in answer:
                                qa_found = True
                                break
                if not qa_found:
                    if self.debug:
                        print(f"[DEBUG] Q&A条件不一致: '{qa_search_condition}' not found in Q&A data")
                    return False
            
            if self.debug:
                print(f"[DEBUG] 全条件一致: {item.get('name', '')}")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] _match_filterable_llm エラー: {e}")
            return False

    async def _match_filterable(self, item: dict[str, Any], keyword: str) -> bool:
        """効率化されたフィルタリング判定メソッド（LLMベースを優先）"""
        if self.debug:
            print(f"[DEBUG] _match_filterable: item={item.get('name', '')}, keyword={keyword}")
        
        # まずLLM解析を試行
        try:
            query_analysis = await self._analyze_query_with_llm(keyword)
            if query_analysis:
                return await self._match_filterable_llm(item, query_analysis)
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] LLM解析エラー、フォールバックに切り替え: {e}")
        
        # フォールバック: 従来の正規表現ベースの高速処理
        return self._match_filterable_fallback(item, keyword)
    
    def _match_filterable_fallback(self, item: dict[str, Any], keyword: str) -> bool:
        """従来の正規表現ベースのフィルタリング（フォールバック用・拡張版）"""
        if self.debug:
            print(f"[DEBUG] _match_filterable_fallback: item={item.get('name', '')}, keyword={keyword}")
        
        # Phase 2: 複雑な数値パターンのチェック
        complex_conditions = self._parse_complex_numeric_conditions(keyword)
        
        # 範囲条件のチェック
        for range_condition in complex_conditions["range_conditions"]:
            if self._match_complex_numeric_condition(item, range_condition, "range"):
                if self.debug:
                    print(f"[DEBUG] 範囲条件一致: {range_condition}")
                return True
        
        # 複数値条件のチェック
        for multiple_condition in complex_conditions["multiple_conditions"]:
            if self._match_complex_numeric_condition(item, multiple_condition, "multiple"):
                if self.debug:
                    print(f"[DEBUG] 複数値条件一致: {multiple_condition}")
                return True
        
        # 近似値条件のチェック
        for approximate_condition in complex_conditions["approximate_conditions"]:
            if self._match_complex_numeric_condition(item, approximate_condition, "approximate"):
                if self.debug:
                    print(f"[DEBUG] 近似値条件一致: {approximate_condition}")
                return True
        
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
            "レジェンド", "ゴールドレア", "シルバーレア", "ブロンズレア"
        ]
        if keyword in rarity_names:
            item_rarity = str(item.get("rarity", ""))
            result = (item_rarity == keyword)
            if self.debug:
                print(f"[DEBUG] レアリティ判定: item_rarity='{item_rarity}', 条件='{keyword}', result={result}")
            return result
        
        # タイプ条件判定
        type_names = [
            "炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"
        ]
        for type_name in type_names:
            if type_name in keyword:
                item_type = str(item.get("type", ""))
                result = (type_name in item_type)
                if self.debug:
                    print(f"[DEBUG] タイプ判定: '{type_name}' in '{item_type}', result={result}")
                return result
        
        # HP条件判定: "HP数値", "HP数値以上/以下/未満/超", "体力数値", "HPが数値"
        hp_match = re.match(r"(HP|体力)(が)?(\d+)(以上|以下|未満|超|等しい)?", keyword)
        if hp_match:
            try:
                hp_val = int(hp_match.group(3))
                condition = hp_match.group(4) or "等しい"  # デフォルトを等しいに変更
                item_hp = int(item.get("hp", 0))
                
                if condition == "等しい":
                    result = (item_hp == hp_val)
                elif condition == "以上":
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
        
        # 攻撃力・ダメージ条件判定: "攻撃数値以上/以下" "ダメージ数値以上/以下"
        attack_match = re.match(r"(攻撃|ダメージ)(\d+)(以上|以下|未満|超)?", keyword)
        if attack_match:
            try:
                attack_val = int(attack_match.group(2))
                condition = attack_match.group(3) or "以上"
                item_attack = int(item.get("attack", 0))
                
                if condition == "以上":
                    result = (item_attack >= attack_val)
                elif condition == "以下":
                    result = (item_attack <= attack_val)
                elif condition == "未満":
                    result = (item_attack < attack_val)
                elif condition == "超":
                    result = (item_attack > attack_val)
                else:
                    result = False
                    
                if self.debug:
                    print(f"[DEBUG] 攻撃力判定: item_attack={item_attack}, 条件={keyword}, result={result}")
                return result
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] 攻撃力判定エラー: {e}")
                return False
        
        # keywordsフィールドでの検索（カードの効果キーワード）
        item_keywords = item.get("keywords", [])
        if isinstance(item_keywords, list):
            # keywordsフィールドに直接一致するキーワードがある場合
            for item_keyword in item_keywords:
                if keyword.lower() in item_keyword.lower() or item_keyword.lower() in keyword.lower():
                    if self.debug:
                        print(f"[DEBUG] keywordsフィールド一致: '{keyword}' <-> '{item_keyword}'")
                    return True
            
            # 部分一致も検索（例：「ファンファーレ」で検索して「ファンファーレ」キーワードを持つカードを見つける）
            keyword_lower = keyword.lower()
            for item_keyword in item_keywords:
                if keyword_lower == item_keyword.lower():
                    if self.debug:
                        print(f"[DEBUG] keywords完全一致: '{keyword}' == '{item_keyword}'")
                    return True
        
        # 効果キーワード判定（effect_1, effect_2, effect_3フィールドでの検索）
        effect_keywords = [
            "進化", "必殺", "守護", "疾走", "突進", "回復", "ドロー", "サーチ", 
            "召喚", "破壊", "バフ", "デバフ", "スペル", "アミュレット",
            "ファンファーレ", "ラストワード", "コンボ", "覚醒", "土の印", "スペルブースト",
            "ネクロマンス", "エンハンス", "アクセラレート", "チョイス", "融合"
        ]
        for effect_keyword in effect_keywords:
            if effect_keyword in keyword:
                # effect_1, effect_2, effect_3フィールドでの検索
                for effect_field in ["effect_1", "effect_2", "effect_3"]:
                    item_effect = str(item.get(effect_field, ""))
                    if effect_keyword in item_effect:
                        if self.debug:
                            print(f"[DEBUG] {effect_field}判定: '{effect_keyword}' in '{item_effect}'")
                        return True
                # keywordsフィールドでの検索
                if isinstance(item_keywords, list) and effect_keyword in item_keywords:
                    if self.debug:
                        print(f"[DEBUG] keywords効果判定: '{effect_keyword}' in {item_keywords}")
                    return True
        
        # 声優名判定
        cv_names = ["門脇舞以", "日笠陽子", "内田雄馬", "辻あゆみ", "潘めぐみ"]
        for cv_name in cv_names:
            if cv_name in keyword:
                item_cv = str(item.get("cv", ""))
                if cv_name in item_cv:
                    if self.debug:
                        print(f"[DEBUG] 声優判定: '{cv_name}' in '{item_cv}'")
                    return True
        
        # イラストレーター名判定
        illustrator_names = ["ツネくん", "やまもも", "伊吹つくば", "misekiss", "言犬", "林", "りょうへい", "あかかがち"]
        for illustrator_name in illustrator_names:
            if illustrator_name in keyword:
                item_illustrator = str(item.get("illustrator", ""))
                if illustrator_name in item_illustrator:
                    if self.debug:
                        print(f"[DEBUG] イラストレーター判定: '{illustrator_name}' in '{item_illustrator}'")
                    return True
        
        # デフォルト: 名前部分一致
        name = str(item.get("name", ""))
        if keyword in name:
            if self.debug:
                print(f"[DEBUG] 名前部分一致: {keyword} in {name}")
            return True
        
        # Q&Aデータでの検索（自然言語クエリに有効）
        qa_data = item.get("qa", [])
        if isinstance(qa_data, list):
            for qa in qa_data:
                if isinstance(qa, dict):
                    question = str(qa.get("question", ""))
                    answer = str(qa.get("answer", ""))
                    if keyword in question or keyword in answer:
                        if self.debug:
                            print(f"[DEBUG] Q&A一致: '{keyword}' found in Q&A")
                        return True
        
        if self.debug:
            print(f"[DEBUG] マッチしなかった: {keyword}")
        return False

    def _normalize_keyword(self, keyword: str) -> str:
        """キーワードの正規化（前後空白除去など）"""
        return keyword.strip()

    def _split_keywords(self, keywords: list[str]) -> list[str]:
        """キーワードを詳細な検索条件に分割"""
        expanded = []
        for keyword in keywords:
            # "HPが1のエルフのカード" → ["HPが1", "エルフ", "カード"]のように分割
            parts = []
            
            # HP条件の抽出
            hp_pattern = r'(HP|体力)(が)?(\d+)(のエルフ|のドラゴン|の\w+)?'
            hp_match = re.search(hp_pattern, keyword)
            if hp_match:
                hp_part = hp_match.group(1) + (hp_match.group(2) or "") + hp_match.group(3)
                parts.append(hp_part)
                # 残りの部分（クラス名など）を抽出
                remaining = keyword.replace(hp_match.group(0), "")
                remaining = remaining.replace("の", "").replace("カード", "").strip()
                if remaining:
                    parts.append(remaining)
            else:
                # その他のパターン（そのまま使用）
                parts.append(keyword)
            
            expanded.extend(parts)
        
        # 空文字列や重複を除去
        result = list(set(p for p in expanded if p.strip()))
        return result

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
            for ef in ["effect_1", "effect_2", "effect_3", "effect_4", "effect_5"]:
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
            "id", "name", "class", "rarity", "cost", "attack", "hp", "type", 
            "effect_1", "effect_2", "effect_3", "effect_4", "effect_5", 
            "cv", "illustrator", "crest"
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
        """最適化されたフィルタ検索（カード名のリストを返す）- LLMベースを優先"""
        # 空キーワードまたはデータが空なら即空リスト返却
        if not keywords or not self.data_cache:
            return []
        
        # キーワードを自然言語クエリとして結合してLLMベース検索を優先
        query = " ".join(keywords)
        
        # LLMベース検索を試行
        try:
            llm_results = await self._search_filterable_llm(query, top_k)
            if llm_results:
                # カード名リストに変換
                card_names = [item.get("name", "") for item in llm_results if item.get("name")]
                if card_names:
                    return card_names
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] LLMベース検索エラー、正規表現ベースにフォールバック: {e}")
        
        # フォールバック: 従来の正規表現ベース検索
        # 複雑なクエリがある場合は事前に分割
        processed_keywords = []
        for kw in keywords:
            if len(kw) > 15 and any(word in kw for word in ["クラス", "コスト", "攻撃", "HP", "かつ", "で"]):
                # 自然言語クエリと判断して分割
                split_kws = self._split_query_to_keywords(kw)
                processed_keywords.extend(split_kws)
            else:
                # 通常のキーワードとして処理
                processed_keywords.append(kw)
        
        # 攻撃力キーワードの正規化
        final_keywords = []
        for kw in processed_keywords:
            if '攻撃力' in kw:
                # 「攻撃力1」を「攻撃1」に変換
                normalized_kw = kw.replace('攻撃力', '攻撃')
                final_keywords.append(normalized_kw)
                if self.debug:
                    print(f"[DEBUG] 攻撃力キーワード正規化: {kw} -> {normalized_kw}")
            else:
                final_keywords.append(kw)
        
        normalized = [self._normalize_keyword(kw) for kw in final_keywords]
        expanded = self._split_keywords(normalized)
        if not expanded:
            return []

        if self.debug:
            print(f"[DEBUG] _filter_search_titles 最終キーワード: {expanded}")
        
        # 正規表現ベースのフォールバック処理
        results = []
        for item in self.data_cache:
            # 全てのキーワードに対してフォールバック処理でマッチング判定
            match_flags = []
            for kw in expanded:
                # 高速なフォールバック処理を使用（LLM解析をスキップ）
                match_result = self._match_filterable_fallback(item, kw)
                match_flags.append(match_result)
            
            if all(match_flags):
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
            # 明示的な型確認
            actual_title_str = str(title)
            norm_title = self._normalize_title(actual_title_str)
            item = self.title_to_data.get(norm_title)
            if item:
                details.append(item)
        return details

    def get_card_by_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """IDによるカード詳細取得"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
        
        for item in self.data_cache:
            if str(item.get("id", "")) == str(card_id):
                return item
        return None

    def get_all_cards(self, limit: Optional[int] = None, offset: int = 0) -> list[dict[str, Any]]:
        """全カード取得（ページネーション対応）"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
        
        if limit is None:
            return self.data_cache[offset:]
        return self.data_cache[offset:offset + limit]

    def get_total_card_count(self) -> int:
        """総カード数取得"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
        return len(self.data_cache)

    def search_by_filters(self, 
                         class_filter: Optional[str] = None,
                         rarity_filter: Optional[str] = None,
                         cost_min: Optional[int] = None,
                         cost_max: Optional[int] = None,
                         hp_min: Optional[int] = None,
                         hp_max: Optional[int] = None,
                         attack_min: Optional[int] = None,
                         attack_max: Optional[int] = None,
                         type_filter: Optional[str] = None,
                         keywords_filter: Optional[list[str]] = None,
                         limit: Optional[int] = None,
                         offset: int = 0) -> list[dict[str, Any]]:
        """高度なフィルタ検索"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
        
        results = []
        for item in self.data_cache:
            # クラスフィルタ
            if class_filter and str(item.get("class", "")) != class_filter:
                continue
                
            # レアリティフィルタ
            if rarity_filter and str(item.get("rarity", "")) != rarity_filter:
                continue
                
            # コストフィルタ
            if cost_min is not None or cost_max is not None:
                try:
                    cost = int(item.get("cost", 0))
                    if cost_min is not None and cost < cost_min:
                        continue
                    if cost_max is not None and cost > cost_max:
                        continue
                except (ValueError, TypeError):
                    continue
                    
            # HPフィルタ
            if hp_min is not None or hp_max is not None:
                try:
                    hp = int(item.get("hp", 0))
                    if hp_min is not None and hp < hp_min:
                        continue
                    if hp_max is not None and hp > hp_max:
                        continue
                except (ValueError, TypeError):
                    continue
                    
            # 攻撃力フィルタ
            if attack_min is not None or attack_max is not None:
                try:
                    attack = int(item.get("attack", 0))
                    if attack_min is not None and attack < attack_min:
                        continue
                    if attack_max is not None and attack > attack_max:
                        continue
                except (ValueError, TypeError):
                    continue
                    
            # タイプフィルタ
            if type_filter:
                item_type = str(item.get("type", ""))
                if type_filter not in item_type:
                    continue
                    
            # キーワードフィルタ
            if keywords_filter:
                item_keywords = item.get("keywords", [])
                if not isinstance(item_keywords, list):
                    continue
                for keyword in keywords_filter:
                    if not any(keyword.lower() in str(k).lower() for k in item_keywords):
                        continue
                        
            results.append(item)
            
        # ページネーション適用
        if limit is None:
            return results[offset:]
        return results[offset:offset + limit]

    def get_random_cards(self, count: int = 5) -> list[dict[str, Any]]:
        """ランダムカード取得"""
        import random
        
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
            
        if count >= len(self.data_cache):
            return self.data_cache.copy()
            
        return random.sample(self.data_cache, count)

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

    def bulk_get_card_details(self, identifiers: list[str], by_field: str = "id") -> list[dict[str, Any]]:
        """複数カードの一括取得（IDまたは名前で検索）"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
            
        results = []
        for identifier in identifiers:
            found = False
            for item in self.data_cache:
                if by_field == "id" and str(item.get("id", "")) == str(identifier):
                    results.append(item)
                    found = True
                    break
                elif by_field == "name":
                    norm_identifier = self._normalize_title(str(identifier))
                    norm_item_name = self._normalize_title(str(item.get("name", "")))
                    if norm_identifier == norm_item_name:
                        results.append(item)
                        found = True
                        break
            if not found and self.debug:
                print(f"[DEBUG] カードが見つかりません: {identifier} (by_{by_field})")
        return results

    def get_cards_by_class(self, class_name: str, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """クラス別カード取得"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
            
        results = []
        for item in self.data_cache:
            if str(item.get("class", "")) == class_name:
                results.append(item)
                if limit and len(results) >= limit:
                    break
        return results

    def get_cards_by_rarity(self, rarity: str, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """レアリティ別カード取得"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
            
        results = []
        for item in self.data_cache:
            if str(item.get("rarity", "")) == rarity:
                results.append(item)
                if limit and len(results) >= limit:
                    break
        return results

    def get_statistics(self) -> dict[str, Any]:
        """データベース統計情報取得"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
            
        stats: dict[str, Any] = {
            "total_cards": len(self.data_cache),
            "classes": {},
            "rarities": {},
            "cost_distribution": {},
            "hp_range": {"min": float("inf"), "max": 0},
            "attack_range": {"min": float("inf"), "max": 0}
        }
        
        for item in self.data_cache:
            # クラス統計
            class_name = str(item.get("class", "不明"))
            classes_dict = stats["classes"]
            assert isinstance(classes_dict, dict)
            classes_dict[class_name] = classes_dict.get(class_name, 0) + 1
            
            # レアリティ統計
            rarity = str(item.get("rarity", "不明"))
            rarities_dict = stats["rarities"]
            assert isinstance(rarities_dict, dict)
            rarities_dict[rarity] = rarities_dict.get(rarity, 0) + 1
            
            # コスト統計
            try:
                cost = int(item.get("cost", 0))
                cost_dist_dict = stats["cost_distribution"]
                assert isinstance(cost_dist_dict, dict)
                cost_dist_dict[cost] = cost_dist_dict.get(cost, 0) + 1
            except (ValueError, TypeError):
                pass
                
            # HP範囲
            try:
                hp = int(item.get("hp", 0))
                if hp > 0:
                    hp_range_dict = stats["hp_range"]
                    assert isinstance(hp_range_dict, dict)
                    hp_range_dict["min"] = min(hp_range_dict["min"], hp)
                    hp_range_dict["max"] = max(hp_range_dict["max"], hp)
            except (ValueError, TypeError):
                pass
                
            # 攻撃力範囲
            try:
                attack = int(item.get("attack", 0))
                if attack > 0:
                    attack_range_dict = stats["attack_range"]
                    assert isinstance(attack_range_dict, dict)
                    attack_range_dict["min"] = min(attack_range_dict["min"], attack)
                    attack_range_dict["max"] = max(attack_range_dict["max"], attack)
            except (ValueError, TypeError):
                pass
        
        # 無限大値の修正
        hp_range_dict = stats["hp_range"]
        assert isinstance(hp_range_dict, dict)
        if hp_range_dict["min"] == float("inf"):
            hp_range_dict["min"] = 0
        
        attack_range_dict = stats["attack_range"]
        assert isinstance(attack_range_dict, dict)
        if attack_range_dict["min"] == float("inf"):
            attack_range_dict["min"] = 0
            
        return stats

    def search_cards_with_pagination(self, 
                                   query: str = "", 
                                   page: int = 1, 
                                   page_size: int = 20,
                                   sort_by: str = "name",
                                   sort_order: str = "asc") -> dict[str, Any]:
        """ページネーション付き検索"""
        if not hasattr(self, "data_cache") or not self.data_cache:
            self.reload_data()
            
        # 検索実行
        if query:
            # 簡単な文字列検索
            filtered_cards = []
            query_lower = query.lower()
            for item in self.data_cache:
                if (query_lower in str(item.get("name", "")).lower() or
                    query_lower in str(item.get("effect_1", "")).lower() or
                    query_lower in str(item.get("effect_2", "")).lower() or
                    query_lower in str(item.get("class", "")).lower() or
                    query_lower in str(item.get("type", "")).lower()):
                    filtered_cards.append(item)
        else:
            filtered_cards = self.data_cache.copy()
        
        # ソート
        if sort_by in ["name", "cost", "hp", "attack", "class", "rarity"]:
            reverse = (sort_order == "desc")
            try:
                if sort_by in ["cost", "hp", "attack"]:
                    filtered_cards.sort(key=lambda x: int(x.get(sort_by, 0)), reverse=reverse)
                else:
                    filtered_cards.sort(key=lambda x: str(x.get(sort_by, "")), reverse=reverse)
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] ソートエラー: {e}")
        
        # ページネーション計算
        total_count = len(filtered_cards)
        total_pages = (total_count + page_size - 1) // page_size
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        page_cards = filtered_cards[start_index:end_index]
        
        return {
            "cards": page_cards,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
