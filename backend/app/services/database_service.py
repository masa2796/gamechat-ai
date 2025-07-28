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
    def __init__(self, data_path: Optional[str] = None):
        import os
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
- hp: integer（HP・体力）
- attack: integer（攻撃力）
- effect: string（効果の説明）
- type: string（タイプ・属性）

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
    "effect": "<効果キーワードまたは空文字>"
  },
  "reasoning": "抽出理由"
}

【抽出ルール】
1. コスト・HP・攻撃力：「5コスト」「HP100以上」「体力50以下」「攻撃40以上」「ダメージ30以上」などから数値と条件を抽出
2. クラス：「エルフ」「ドラゴン」「ロイヤル」「ウィッチ」「ネクロマンサー」「ビショップ」「ネメシス」「ヴァンパイア」「ニュートラル」
3. レアリティ：「レジェンド」「ゴールドレア」「シルバーレア」「ブロンズ」「レア」
4. タイプ・属性：「炎」「水」「草」「電気」「超」「闘」「悪」「鋼」「フェアリー」「タイプ」など
5. 効果：「進化」「必殺」「守護」「疾走」「突進」「回復」「ドロー」「サーチ」などの効果キーワード
6. 「ダメージ」「攻撃」は attack フィールドとして扱う
7. 抽出できない場合は空文字またはnullを設定

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
    "effect": ""
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
    "effect": ""
  },
  "reasoning": "ダメージ40以上の条件と水タイプを抽出"
}

必ずJSONのみで回答してください。他の文章は含めないでください。
"""

    def _load_data(self) -> list[dict[str, Any]]:
        # テスト用: StorageServiceのload_json_dataを呼ぶ
        if hasattr(self.storage_service, "load_json_data"):
            return self.storage_service.load_json_data()
        elif hasattr(self.storage_service, "load_data"):
            return self.storage_service.load_data()
        return []

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
            
            content = response.choices[0].message.content.strip()
            if self.debug:
                print(f"[DEBUG] LLM Response: {content}")
            
            # JSONをパース
            analysis_result = json.loads(content)
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
            "effect": ""
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
        classes = ["エルフ", "ドラゴン", "ロイヤル", "ウィッチ", "ネクロマンサー", "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル"]
        for cls in classes:
            if cls in query:
                conditions["class"] = cls
                break
        
        # レアリティ検出
        rarities = ["レジェンド", "ゴールドレア", "シルバーレア", "ブロンズ", "レア"]
        for rarity in rarities:
            if rarity in query:
                conditions["rarity"] = rarity
                break
        
        # タイプ検出
        types = ["炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"]
        for card_type in types:
            if card_type in query:
                conditions["type"] = card_type
                break
        
        # 効果キーワード検出
        effects = ["進化", "必殺", "守護", "疾走", "突進", "回復", "ドロー", "サーチ", "召喚", "破壊"]
        for effect in effects:
            if effect in query:
                conditions["effect"] = effect
                break
        
        return {
            "conditions": conditions,
            "reasoning": f"モック環境でのクエリ解析: {query}"
        }
    async def filter_search_async(self, keywords: list[str], top_k: int = 10) -> list[str]:
        result = await self.filter_search_titles_async(keywords, top_k)
        return result

    async def filter_search_llm_async(self, query: str, top_k: int = 10) -> list[str]:
        """LLMベースのフィルタ検索（カード名リストを返す）"""
        
        # LLMベースの検索を実行
        results = await self._search_filterable_llm(query, top_k)
        
        # カード名リストに変換
        card_names = [item.get("name", "") for item in results if item.get("name")]
        
        return card_names

    def filter_search(self, keywords: list[str], top_k: int = 10) -> list[str]:
        result = asyncio.get_event_loop().run_until_complete(self.filter_search_async(keywords, top_k))
        return result

    def _filter_search_sync(self, keywords: list[str], top_k: int = 10) -> list[str]:
        """同期版フィルタ検索（高速フォールバックのみ）"""
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
            return await self.filter_search_llm_async(query_input, top_k)
        else:
            # 従来のキーワード検索を使用（クエリを簡単にキーワードに分割）
            keywords = self._split_query_to_keywords(query_input)
            return await self.filter_search_async(keywords, top_k)
    
    def _split_query_to_keywords(self, query: str) -> list[str]:
        """クエリを検索可能なキーワードに分割（改善版）"""
        import re
        keywords = []
        
        # 1. クラス名を抽出
        classes = ["エルフ", "ドラゴン", "ロイヤル", "ウィッチ", "ネクロマンサー", "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル"]
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
        rarities = ["レジェンド", "ゴールドレア", "シルバーレア", "ブロンズ", "レア"]
        for rarity in rarities:
            if rarity in query:
                keywords.append(rarity)
        
        # 空文字列や重複を除去
        return list(set(kw for kw in keywords if kw.strip()))

    def reload_data(self) -> None:
        """
        データを再読み込みし、キャッシュとtitle_to_dataを構築
        """
        data = self._load_data()
        self.data_cache = data
        self.title_to_data = {}
        for item in data:
            # nameフィールドがキー（正規化処理を強化）
            name = item.get("name")
            if name:
                norm_name = self._normalize_title(str(name))
                self.title_to_data[norm_name] = item
    async def _search_filterable(self, keywords: list[str], top_k: int = 10) -> list[dict[str, Any]]:
        """最適化されたフィルタ検索（LLM解析を最小化）"""
        
        # 各キーワードに対してLLM解析を1回だけ実行
        keyword_analyses = {}
        for kw in keywords:
            try:
                keyword_analyses[kw] = await self._analyze_query_with_llm(kw)
                if self.debug:
                    print(f"[DEBUG] キーワード解析完了: {kw}")
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] キーワード解析エラー: {kw}, {e}")
                keyword_analyses[kw] = None
        
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
        """LLMを使用したフィルタ検索（新実装）"""
        
        # LLMでクエリを解析
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

    async def _match_filterable_llm(self, item: Dict[str, Any], query_analysis: Dict[str, Any]) -> bool:
        """LLM解析結果を使用してアイテムがフィルター条件に一致するかを判定（拡張版）"""
        if self.debug:
            print(f"[DEBUG] _match_filterable_llm: item={item.get('name', '')}")
        
        try:
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
                item_effect = str(item.get("effect", ""))
                if effect_condition not in item_effect:
                    if self.debug:
                        print(f"[DEBUG] 効果条件不一致: {effect_condition} not in {item_effect}")
                    return False
            
            # コスト条件チェック
            cost_condition = conditions.get("cost", {})
            if cost_condition.get("value") is not None:
                item_cost = int(item.get("cost", 0))
                cost_value = cost_condition["value"]
                cost_operator = cost_condition.get("operator", "等しい")
                
                if cost_operator == "等しい" and item_cost != cost_value:
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
                
                if hp_operator == "等しい" and item_hp != hp_value:
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
                
                if attack_operator == "等しい" and item_attack != attack_value:
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
            
            if self.debug:
                print(f"[DEBUG] 全条件一致: {item.get('name', '')}")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] _match_filterable_llm エラー: {e}")
            return False

    async def _match_filterable(self, item: dict[str, Any], keyword: str) -> bool:
        """効率化されたフィルタリング判定メソッド（LLM解析は外部で1回のみ実行）"""
        if self.debug:
            print(f"[DEBUG] _match_filterable (FALLBACK): item={item.get('name', '')}, keyword={keyword}")
        
        # LLM解析は外部で1回のみ実行されるように変更
        # ここでは従来の正規表現ベースの高速フォールバック処理のみ実行
        return self._match_filterable_fallback(item, keyword)
    
    def _match_filterable_fallback(self, item: dict[str, Any], keyword: str) -> bool:
        """従来の正規表現ベースのフィルタリング（フォールバック用・拡張版）"""
        if self.debug:
            print(f"[DEBUG] _match_filterable_fallback: item={item.get('name', '')}, keyword={keyword}")
        
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
        
        # 効果キーワード判定
        effect_keywords = [
            "進化", "必殺", "守護", "疾走", "突進", "回復", "ドロー", "サーチ", 
            "召喚", "破壊", "バフ", "デバフ", "スペル", "アミュレット"
        ]
        for effect_keyword in effect_keywords:
            if effect_keyword in keyword:
                item_effect = str(item.get("effect", ""))
                result = (effect_keyword in item_effect)
                if self.debug:
                    print(f"[DEBUG] 効果判定: '{effect_keyword}' in '{item_effect}', result={result}")
                return result
        
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
        """最適化されたフィルタ検索（カード名のリストを返す）"""
        # 空キーワードまたはデータが空なら即空リスト返却
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
        
        # パフォーマンス最適化：LLM解析を使わずに高速なフォールバック処理のみ使用
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
