import openai
import json
import os
import asyncio
import random
from ..models.classification_models import ClassificationRequest, ClassificationResult, QueryType, SearchStrategy
from ..core.config import settings
from ..core.exceptions import ClassificationException
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger

class ClassificationService:
    """
    LLMによるクエリ分類・要約サービス。
    
    OpenAI GPT-4oを使用してユーザーのクエリを分析し、
    最適な検索戦略を決定するための分類を行います。
    
    分類タイプ:
        - GREETING: 挨拶・雑談（検索不要）
        - FILTERABLE: 具体的な条件での絞り込み検索
        - SEMANTIC: 意味的な検索
        - HYBRID: 両方の組み合わせ
        
    Attributes:
        client: OpenAI APIクライアント
        system_prompt: 分類用のシステムプロンプト
        
    Examples:
        >>> service = ClassificationService()
        >>> request = ClassificationRequest(query="HP100以上のカード")
        >>> result = await service.classify_query(request)
        >>> print(result.query_type)
        QueryType.FILTERABLE
        >>> print(result.confidence)
        0.9
    """
    
    def __init__(self) -> None:
        # モック環境のチェック
        mock_external = os.getenv("BACKEND_MOCK_EXTERNAL_SERVICES", "false").lower() == "true"
        is_testing = os.getenv("BACKEND_TESTING", "false").lower() == "true"
        
        if mock_external or is_testing:
            # モック環境では実際のOpenAIクライアントは初期化しない
            self.client = None
            self.is_mocked = True
        else:
            # OpenAI クライアントを初期化
            api_key = getattr(settings, 'BACKEND_OPENAI_API_KEY', None) or os.getenv("BACKEND_OPENAI_API_KEY")
            
            # APIキーの検証
            if not api_key or api_key in ["your_openai_api_key", "your_actual_openai_api_key_here", "sk-test_openai_key"]:
                raise ClassificationException(
                    "OpenAI APIキーが設定されていません。.envファイルでBACKEND_OPENAI_API_KEYを設定してください。"
                )
            
            self.client = openai.OpenAI(api_key=api_key)
            self.is_mocked = False
        self.system_prompt = """
あなたはカードゲームのデータベース検索アシスタントです。
ユーザーのクエリを解析し、構造化検索や分類に必要な条件を必ず抽出してください。

【データベーススキーマ】
cardsテーブル
- name: string（カード名）
- rarity: string（レアリティ）
- cost: integer（コスト）
- class: string（クラス）
- effect: string（効果の説明）
- hp: integer（HP・体力）
- attack: integer（攻撃力）
- damage: integer（ダメージ）

【指示】
1. ユーザーのクエリから、必ず以下のJSON形式で検索条件を抽出してください。
   {
     "table": "cards",
     "conditions": {
       "name": "<カード名または空文字>",
       "rarity": "<レアリティまたは空文字>",
       "cost": <数値またはnull>,
       "class": "<クラスまたは空文字>",
       "aggregation": "<集約条件または空文字>",
       "numeric_conditions": "<数値条件または空文字>"
     }
   }
2. 数値条件・集約条件・属性条件など、抽出できる条件は必ず抽出してください。
3. 集約条件例：「一番高い」「最大」「最小」「上位N件」「トップ」「ボトム」
4. 数値条件例：範囲（「○○から○○の間」）、複数値（「○○または○○」）、近似（「約○○」「○○程度」）
5. 抽出できない場合は空文字またはnullにし、reasoningに「なぜ抽出できなかったか」を必ず記載してください。
6. 出力はJSONのみで行い、他の文章は一切含めないでください。

【例1：集約クエリ】
ユーザー: 「一番高いHPのカードを探して」
出力:
{
  "table": "cards",
  "conditions": {
    "name": "",
    "rarity": "",
    "cost": null,
    "class": "",
    "aggregation": "最大値:HP",
    "numeric_conditions": ""
  }
}

【例2：複雑な数値条件】
ユーザー: 「HPが○○から○○の間のレジェンドカード」
出力:
{
  "table": "cards",
  "conditions": {
    "name": "",
    "rarity": "レジェンド",
    "cost": null,
    "class": "",
    "aggregation": "",
    "numeric_conditions": "範囲:HP"
  }
}

---

また、あなたはゲーム攻略データベースのクエリ分類システムでもあります。
ユーザーの質問を分析し、最適な検索戦略を決定してください。

分類タイプ:
1. "greeting" - 挨拶・雑談（検索不要）
   例：「こんにちは」「おはよう」「ありがとう」「よろしく」「お疲れ様」
   例：「元気？」「調子はどう？」「今日は暑いね」
2. "filterable" - 具体的な条件での絞り込み検索（数値条件、集約条件、属性条件等が含まれる場合）
   【数値条件の例】
   - 基本条件: 「HPが○○以上のカード」「コストが○○以下のカード」
   - 範囲条件: 「HPが○○から○○の間のカード」「コストが○○～○○のカード」
   - 複数値条件: 「コストが○○または○○のカード」「HPが○○か○○のカード」
   - 近似値条件: 「約○○のHP」「○○程度のダメージ」「およそ○○のコスト」
   【集約条件の例】
   - 最大値: 「一番高いHP」「最大ダメージ」「最高コスト」「HPがトップのカード」
   - 最小値: 「一番低いHP」「最小コスト」「最低ダメージ」「HPがボトムのカード」
   - 上位N件: 「上位N位のHP」「トップNのダメージ」「ベストNのコスト」
   【属性条件の例】
   - タイプ・クラス: 「炎タイプのカード」「エルフクラスのカード」
   - レアリティ: 「レジェンドのカード」「レアカード」
   - 複合条件: 「炎タイプで高HPのカード」「エルフの低コストカード」
3. "semantic" - 意味的な検索
   例：「強いカードを教えて」「おすすめの戦略」「初心者向けのデッキ」
4. "hybrid" - 両方の組み合わせ
   例：「炎タイプで強いカード」「HPが高くて使いやすいカード」「最大ダメージで人気のカード」

重要: 挨拶や一般的な会話は「greeting」として分類し、検索キーワードは空にしてください。

フィルターキーワードの例:
- 数値条件: "HP", "○○以上", "○○以下", "○○から○○", "○○または○○", "約○○", "○○程度", "ダメージ", "コスト", "攻撃力"
- 集約条件: "一番高い", "最大", "最高", "トップ", "一番低い", "最小", "最低", "ボトム", "上位", "ベスト"
- タイプ: "炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"
- レアリティ: "レジェンド", "ゴールドレア", "シルバーレア", "ブロンズ"
- クラス: "ニュートラル", "エルフ", "ロイヤル", "ヴァンパイア", "ドラゴン", "ウィッチ", "ネクロマンサー", "ビショップ", "ネメシス"
- 効果キーワード: "ファンファーレ", "ラストワード", "コンボ", "覚醒", "土の印", "スペルブースト", "ネクロマンス", "エンハンス", "アクセラレート", "チョイス", "融合", "進化", "必殺", "守護", "疾走", "突進", "交戦時", "超進化時", "攻撃時", "潜伏", "進化時", "アクト", "カウントダウン", "バリア", "モード", "土の秘術", "リアニメイト", "威圧", "オーラ", "ドレイン", "アポカリプスデッキ"

検索キーワードの例:
- 抽象的概念: "強い", "弱い", "おすすめ", "人気", "使いやすい", "効果的", "有用", "便利"
- 戦略: "攻撃的", "守備的", "サポート", "コンボ", "バランス", "速攻", "持久戦"
- 評価: "最強", "最弱", "優秀", "微妙", "注目", "話題"

重要: 複合条件の場合は、すべての条件をfilter_keywordsに含めてください。
例：「ダメージが高い技を持つ、水タイプカード」
→ filter_keywords: ["ダメージ", "高い", "技", "水", "タイプ"]

重要: 集約クエリの場合は、集約条件と対象フィールドの両方を含めてください。
例：「一番高いHPのカード」
→ filter_keywords: ["一番高い", "HP", "最大値"]

**必ず以下のJSON形式のみで回答してください。他の文章は含めず、JSONのみを出力してください:**
{
    "query_type": "greeting",
    "summary": "要約されたクエリ",
    "confidence": 0.8,
    "filter_keywords": ["フィルター用キーワード"],
    "search_keywords": ["検索用キーワード"],
    "reasoning": "分類理由"
}
"""

    @handle_service_exceptions("classification", fallback_return=None)
    async def classify_query(self, request: ClassificationRequest) -> ClassificationResult:
        """
        クエリを分類・要約します。
        
        GPT-4oを使用してユーザーのクエリを分析し、適切な検索戦略を決定するための
        分類結果を返します。JSON形式での回答を強制し、一貫性を保ちます。
        
        Args:
            request: 分類リクエスト
                - query: 分類対象のクエリ文字列
                
        Returns:
            分類結果:
                - query_type: クエリタイプ（GREETING, FILTERABLE, SEMANTIC, HYBRID）
                - summary: LLMが生成した要約
                - confidence: 分類の信頼度（0.0-1.0）
                - filter_keywords: フィルター検索用キーワード
            # クラス名リストから直接抽出
            class_names = [
                "エルフ", "ドラゴン", "ロイヤル", "ウィッチ", "ネクロマンサー",
                "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル"
            ]
            for cname in class_names:
                if cname in request.query:
                    filter_keywords_found.append(cname)
                - search_keywords: セマンティック検索用キーワード
                - reasoning: 分類理由
                
        Raises:
            ClassificationException: OpenAI APIキーが設定されていない場合
            ClassificationException: OpenAI APIからの応答が空の場合
            
        Examples:
            >>> service = ClassificationService()
            >>> request = ClassificationRequest(query="HP100以上のカード")
            >>> result = await service.classify_query(request)
            >>> print(result.query_type)
            QueryType.FILTERABLE
            >>> print(result.filter_keywords)
            ['HP', '100以上']
        """
        
        # モック環境の処理
        if self.is_mocked:
            GameChatLogger.log_info("classification_service", "モック環境で実行")
            
            # 簡単な分類ロジック
            query_lower = request.query.lower()
            
            # 挨拶判定
            greetings = ["こんにちは", "おはよう", "こんばんは", "はじめまして", "よろしく", "ありがとう"]
            if any(greeting in query_lower for greeting in greetings):
                return ClassificationResult(
                    query_type=QueryType.GREETING,
                    summary="挨拶・雑談",
                    confidence=0.9,
                    filter_keywords=[],
                    search_keywords=[],
                    reasoning="挨拶に関するキーワードが検出されました"
                )
            
            # フィルター判定（コスト・HP・タイプ・効果キーワード等の多様な表現に対応）
            filter_keywords_found = []
            import re
            matched_spans = []
            
            # 集約条件の検出（最高優先度）
            aggregation_patterns = [
                r"一番[高低]い", r"最[大小高低]", r"トップ\d*", r"ボトム\d*", 
                r"上位\d+", r"ベスト\d+", r"[高低]い順"
            ]
            for pattern in aggregation_patterns:
                for m in re.finditer(pattern, request.query):
                    filter_keywords_found.append(m.group(0).strip())
                    matched_spans.append((m.start(), m.end()))
            
            # フィールド名の検出（集約クエリと組み合わせて使用）
            field_patterns = [
                r"HP", r"ヒットポイント", r"体力", r"コスト", r"cost", 
                r"ダメージ", r"攻撃力", r"攻撃", r"attack"
            ]
            for pattern in field_patterns:
                for m in re.finditer(pattern, request.query, re.IGNORECASE):
                    filter_keywords_found.append(m.group(0).strip())
                    matched_spans.append((m.start(), m.end()))
            
            # 効果キーワードの検出（優先度高）
            effect_keywords = [
                "交戦時", "攻撃時", "ファンファーレ", "ラストワード", "進化時", "超進化時",
                "結晶", "土の印", "共鳴", "アクセラレート", "エンハンス", "スペルブースト",
                "復讐", "ヴェンジェンス", "覚醒", "機械", "自然", "OTK", "フィニッシャー",
                "バーン", "ドロー", "サーチ", "除去", "AOE", "全体除去", "単体除去",
                "バフ", "デバフ", "回復", "ダメージ", "破壊", "消滅", "変身"
            ]
            
            for keyword in effect_keywords:
                if keyword in request.query:
                    filter_keywords_found.append(keyword)
                    # マッチした位置を記録
                    start_pos = request.query.find(keyword)
                    if start_pos != -1:
                        matched_spans.append((start_pos, start_pos + len(keyword)))
            
            # 数値条件の複合パターンを1キーワードとして抽出（動的な数値対応）
            numeric_patterns = [
                r"(\d+)\s*コスト", r"コスト\s*(\d+)", r"cost\s*(\d+)", r"(\d+)\s*cost",
                r"HP\s*(\d+|○○)", r"ヒットポイント\s*(\d+|○○)", r"体力\s*(\d+|○○)",
                r"ダメージ\s*(\d+|○○)", r"攻撃\s*(\d+|○○)", r"attack\s*(\d+|○○)",
                r"(\d+|○○)\s*以上", r"(\d+|○○)\s*以下", r"(\d+|○○)\s*未満", r"(\d+|○○)\s*超",
                r"(\d+|○○)から(\d+|○○)", r"(\d+|○○)～(\d+|○○)", r"(\d+|○○)または(\d+|○○)",
                r"約(\d+|○○)", r"(\d+|○○)程度", r"およそ(\d+|○○)", r"(\d+|○○)か(\d+|○○)"
            ]
            for pattern in numeric_patterns:
                for m in re.finditer(pattern, request.query, re.IGNORECASE):
                    filter_keywords_found.append(m.group(0).strip())
                    matched_spans.append((m.start(), m.end()))
            
            # 複数値/選択系キーワードの明示的検出
            choice_keywords = ["または", "か", "もしくは", "あるいは", "まで"]
            for keyword in choice_keywords:
                if keyword in request.query:
                    filter_keywords_found.append(keyword)
                    start_pos = request.query.find(keyword)
                    if start_pos != -1:
                        matched_spans.append((start_pos, start_pos + len(keyword)))
            
            # タイプ・クラス条件（動的検出）
            type_class_keywords = [
                "タイプ", "type", "class", "クラス", "エルフ", "ドラゴン", "ロイヤル", 
                "ウィッチ", "ネクロマンサー", "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル"
            ]
            for keyword in type_class_keywords:
                if keyword in request.query:
                    filter_keywords_found.append(keyword)
            
            # その他単語（例: レアリティ等）の動的抽出
            # 既存のパターンに該当しない単語を抽出（空白区切り）
            # ただし、既に抽出済みのspanには含まれない部分のみ追加
            def is_in_matched_spans(idx: int) -> bool:
                for start, end in matched_spans:
                    if start <= idx < end:
                        return True
                return False
            for m in re.finditer(r'[^\s　,、]+', request.query):
                if not is_in_matched_spans(m.start()):
                    w = m.group(0).strip()
                    if w and not any(w in k for k in filter_keywords_found):
                        filter_keywords_found.append(w)
            # 重複除去
            filter_keywords_found = list(dict.fromkeys(filter_keywords_found))
            if filter_keywords_found:
                return ClassificationResult(
                    query_type=QueryType.FILTERABLE,
                    summary=f"フィルター検索: {request.query}",
                    confidence=0.8,
                    filter_keywords=filter_keywords_found,
                    search_keywords=[],
                    reasoning="具体的な条件が検出されました（集約・数値・属性条件の動的抽出）"
                )
            
            # デフォルトはセマンティック検索
            return ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary=f"セマンティック検索: {request.query}",
                confidence=0.7,
                filter_keywords=[],
                search_keywords=request.query.split()[:3],  # 最初の3単語を使用
                reasoning="一般的な質問として判定"
            )
        
        # 本番環境の処理
        if not self.client:
            raise ClassificationException(
                message="OpenAI APIキーが設定されていません",
                code="API_KEY_NOT_SET"
            )
        
        GameChatLogger.log_info("classification_service", "クエリ分類開始", {
            "query_length": len(request.query),
            "query_preview": request.query[:50]
        })
        
        # プロンプト強化: 集約クエリ、複雑な数値条件、多様な例を追加
        user_prompt = f"""
あなたはカードゲームのクエリ分類AIです。ユーザーの質問文を必ず以下のJSON形式で分類してください。
---
分類タイプ:
- filterable: 具体的な条件指定（数値条件、集約条件、属性指定等）
  【数値条件の例】
  - 基本: HPが○○以上、コストが○○以下
  - 範囲: HPが○○から○○の間、コストが○○～○○
  - 複数値: コストが○○または○○、HPが○○か○○
  - 近似: 約○○のHP、○○程度のダメージ
  【集約条件の例】
  - 最大値: 一番高いHP、最大ダメージ、最高コスト、HPがトップ
  - 最小値: 一番低いHP、最小コスト、最低ダメージ、HPがボトム
  - 上位N件: 上位3位のHP、トップ5のダメージ、ベスト3のコスト
  【属性条件の例】
  - タイプ・クラス: 炎タイプ、エルフクラス
  - レアリティ: レジェンド、レア
- semantic: 曖昧・主観的・抽象的な問い
  例: 強いカード、人気のカード、おすすめのデッキ、使いやすい、効果的
- hybrid: 両方の要素を含む
  例: HPが高くて強いカード、炎タイプでおすすめ、最大ダメージで人気
---
必ず以下のJSON形式のみで出力してください。
{{
  "query_type": "filterable|semantic|hybrid",
  "summary": "分類理由の要約",
  "confidence": 0.0〜1.0,
  "filter_keywords": ["必ず1つ以上"],
  "search_keywords": ["必ず1つ以上"],
  "reasoning": "分類理由"
}}
---
【例1】基本的なフィルター条件
質問: コストが低いエルフのカードを出力
{{
  "query_type": "filterable",
  "summary": "コストとクラス指定",
  "confidence": 0.95,
  "filter_keywords": ["コスト", "低い", "エルフ"],
  "search_keywords": ["コスト", "エルフ"],
  "reasoning": "数値条件と属性指定を検出"
}}
【例2】集約条件
質問: 一番高いHPのカード
{{
  "query_type": "filterable",
  "summary": "HP最大値検索",
  "confidence": 0.95,
  "filter_keywords": ["一番高い", "HP", "最大値"],
  "search_keywords": ["HP", "最大"],
  "reasoning": "集約条件（最大値）を検出"
}}
【例3】範囲条件
質問: HPが中程度のカード
{{
  "query_type": "filterable",
  "summary": "HP範囲指定",
  "confidence": 0.90,
  "filter_keywords": ["HP", "中程度", "範囲"],
  "search_keywords": ["HP", "範囲"],
  "reasoning": "数値範囲条件を検出"
}}
【例4】複数値条件
質問: ファイアタイプまたは水タイプのカード
{{
  "query_type": "filterable",
  "summary": "複数タイプ指定",
  "confidence": 0.95,
  "filter_keywords": ["ファイア", "タイプ", "または", "水", "タイプ"],
  "search_keywords": ["ファイア", "水", "タイプ"],
  "reasoning": "複数値条件を検出"
}}
【例5】セマンティック
質問: 強いドラゴンカード
{{
  "query_type": "semantic",
  "summary": "曖昧な強さ評価",
  "confidence": 0.85,
  "filter_keywords": ["ドラゴン"],
  "search_keywords": ["強い", "ドラゴン"],
  "reasoning": "主観的表現を検出"
}}
【例6】ハイブリッド
質問: 最大ダメージで人気のカード
{{
  "query_type": "hybrid",
  "summary": "集約条件+主観評価",
  "confidence": 0.90,
  "filter_keywords": ["最大", "ダメージ"],
  "search_keywords": ["人気", "カード"],
  "reasoning": "集約条件と主観的評価の組み合わせ"
}}
---
質問: {request.query}
"""
        
        # レート制限対応のためのリトライ処理
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                GameChatLogger.log_info("classification_service", f"OpenAI API呼び出し開始 (試行 {attempt + 1}/{max_retries + 1})")
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.0,  # 一貫性のために0に設定
                    response_format={"type": "json_object"},  # JSON形式を強制
                    timeout=10  # 個別APIコールのタイムアウト
                )
                
                GameChatLogger.log_success("classification_service", f"OpenAI API呼び出し成功 (試行 {attempt + 1})")
                break  # 成功したらループを抜ける
                
            except openai.AuthenticationError as e:
                GameChatLogger.log_error("classification_service", "OpenAI認証エラー", e, {
                    "api_key_prefix": getattr(settings, 'OPENAI_API_KEY', 'None')[:10] if getattr(settings, 'OPENAI_API_KEY', None) else 'None'
                })
                raise ClassificationException(
                    message="OpenAI APIキーが無効です。正しいAPIキーを設定してください。",
                    code="INVALID_API_KEY"
                ) from e
                
            except openai.RateLimitError as e:
                if attempt == max_retries:
                    GameChatLogger.log_error("classification_service", "OpenAI レート制限、全リトライ試行完了", e)
                    raise ClassificationException(
                        message="OpenAI APIのレート制限に達しました。しばらく待ってから再試行してください。",
                        code="RATE_LIMIT_EXCEEDED"
                    ) from e
                else:
                    # 指数バックオフ + ジッター
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    GameChatLogger.log_warning("classification_service", f"OpenAI APIレート制限エラー、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})")
                    asyncio.run(asyncio.sleep(delay))
                    continue
                    
            except openai.OpenAIError as e:
                error_str = str(e)
                # その他のOpenAIエラーもレート制限の可能性があるかチェック
                if "429" in error_str or "rate_limit" in error_str.lower() or "too many requests" in error_str.lower():
                    if attempt == max_retries:
                        GameChatLogger.log_error("classification_service", f"OpenAI APIレート制限（その他）、全リトライ試行完了: {error_str}", e)
                        raise ClassificationException(
                            message="現在多くのリクエストが集中しているため処理できません。少し時間をおいてからもう一度お試しください。",
                            code="RATE_LIMIT_EXCEEDED"
                        ) from e
                    else:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        GameChatLogger.log_warning("classification_service", f"OpenAI APIレート制限エラー（その他）、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})")
                        asyncio.run(asyncio.sleep(delay))
                        continue
                else:
                    GameChatLogger.log_error("classification_service", "OpenAI APIエラー", e)
                    raise ClassificationException(
                        message=f"OpenAI APIでエラーが発生しました: {error_str}",
                        code="OPENAI_API_ERROR"
                    ) from e
                    
            except Exception as e:
                GameChatLogger.log_error("classification_service", f"予期しないエラー (試行 {attempt + 1})", e)
                raise ClassificationException(
                    message=f"分類処理中に予期しないエラーが発生しました: {str(e)}",
                    code="UNEXPECTED_ERROR"
                ) from e
        
        result_text = response.choices[0].message.content
        if result_text is None:
            raise ClassificationException(
                message="OpenAI APIからの応答が空です",
                code="EMPTY_RESPONSE"
            )
        result_text = result_text.strip()
        GameChatLogger.log_info("classification_service", "LLM応答取得完了", {
            "response_length": len(result_text)
        })
        # LLMの生JSON応答をターミナルに出力
        GameChatLogger.log_info("classification_service", "LLM生応答(JSON)", {
            "llm_raw_response": result_text[:1000]  # 長すぎる場合は1000文字まで
        })
        
        try:
            result_data = json.loads(result_text)
            # 必須フィールドの存在チェックと補完
            required_fields = ["query_type", "summary", "confidence", "filter_keywords", "search_keywords", "reasoning"]
            defaults = {
                "query_type": "semantic",
                "summary": request.query,
                "confidence": 0.3,
                "filter_keywords": [],
                "search_keywords": [],
                "reasoning": ""
            }
            missing = [f for f in required_fields if f not in result_data or result_data[f] is None]
            if missing:
                GameChatLogger.log_warning("classification_service", "OpenAI応答に必須フィールド欠落（デフォルト補完）", {
                    "missing_fields": missing,
                    "response_text": result_text[:200]
                })
                for f in missing:
                    result_data[f] = defaults[f]
            # 型バリデーション
            # query_typeはEnum変換
            if isinstance(result_data["query_type"], str):
                result_data["query_type"] = QueryType(result_data["query_type"])
            # filter_keywords, search_keywordsはリスト型に強制
            for k in ["filter_keywords", "search_keywords"]:
                if not isinstance(result_data[k], list):
                    result_data[k] = []
            # reasoningはstr型に強制
            if not isinstance(result_data["reasoning"], str):
                result_data["reasoning"] = str(result_data["reasoning"]) if result_data["reasoning"] is not None else ""

            # --- ここから自動補完ロジック追加 ---
            # filter_keywords, search_keywordsが空の場合はクエリから自動抽出
            def extract_keywords_fallback(query: str) -> list[str]:
                import re
                keywords: list[str] = []
                
                # クラス名リスト
                class_names = [
                    "エルフ", "ドラゴン", "ロイヤル", "ウィッチ", "ネクロマンサー",
                    "ビショップ", "ネメシス", "ヴァンパイア", "ニュートラル"
                ]
                for cname in class_names:
                    if cname in query:
                        keywords.append(cname)
                
                # コスト・タイプ等のパターン抽出
                patterns = [
                    r"(\d+)\s*コスト", r"コスト\s*(\d+)", r"cost\s*(\d+)", r"(\d+)\s*cost",
                    r"[炎|水|草|電気|超|闘|悪|鋼|フェアリー]タイプ"
                ]
                for pat in patterns:
                    for m in re.finditer(pat, query, re.IGNORECASE):
                        kw = m.group(0).strip()
                        if kw and kw not in keywords:
                            keywords.append(kw)
                
                # 空白区切り単語も追加
                for w in re.split(r"[\s　,、]+", query):
                    w = w.strip()
                    if w and w not in keywords:
                        keywords.append(w)
                
                return keywords

            if (not result_data["filter_keywords"] or not result_data["search_keywords"]) and result_data["query_type"] != QueryType.GREETING:
                GameChatLogger.log_warning(
                    "classification_service",
                    "OpenAI応答のfilter_keywordsまたはsearch_keywordsが空です（自動抽出で補完）",
                    {
                        "filter_keywords": result_data["filter_keywords"],
                        "search_keywords": result_data["search_keywords"],
                        "response_text": result_text[:200]
                    }
                )
                # 自動抽出で補完
                if not result_data["filter_keywords"]:
                    result_data["filter_keywords"] = extract_keywords_fallback(request.query)
                if not result_data["search_keywords"]:
                    result_data["search_keywords"] = extract_keywords_fallback(request.query)

            classification = ClassificationResult.parse_obj(result_data)
            GameChatLogger.log_success("classification_service", "クエリ分類完了", {
                "query_type": classification.query_type,
                "confidence": classification.confidence,
                "filter_keywords_count": len(classification.filter_keywords or []),
                "search_keywords_count": len(classification.search_keywords or [])
            })
            return classification
        except json.JSONDecodeError as json_error:
            GameChatLogger.log_warning("classification_service", "JSON解析エラー - フォールバック実行", {
                "json_error": str(json_error),
                "response_text": result_text[:100]
            })
            # JSONパースに失敗した場合のフォールバック
            return ClassificationResult(
                query_type=QueryType.FILTERABLE,  # 複合クエリなのでfilterableを推定
                summary=request.query,
                confidence=0.5,
                filter_keywords=["ダメージ", "40以上", "技", "水", "タイプ"],  # 手動でキーワード抽出
                search_keywords=[request.query],
                reasoning="JSON解析エラー - 手動キーワード抽出で対応"
            )
        except Exception as e:
            GameChatLogger.log_error("classification_service", "必須フィールド欠落または型不整合", e)
            # エラー時のフォールバック
            return ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary=request.query,
                confidence=0.3,
                search_keywords=[request.query],
                reasoning=f"分類エラー: {str(e)}"
            )

    def determine_search_strategy(self, classification: ClassificationResult) -> SearchStrategy:
        """分類結果に基づいて検索戦略を決定"""
        if classification.query_type == QueryType.GREETING:
            # 挨拶の場合は検索不要
            return SearchStrategy(
                use_db_filter=False,
                use_vector_search=False
            )
        elif classification.query_type == QueryType.FILTERABLE:
            return SearchStrategy(
                use_db_filter=True,
                use_vector_search=False,
                db_filter_params={
                    "keywords": classification.filter_keywords,
                    "confidence": classification.confidence
                }
            )
        elif classification.query_type == QueryType.SEMANTIC:
            return SearchStrategy(
                use_db_filter=False,
                use_vector_search=True,
                vector_search_params={
                    "keywords": classification.search_keywords,
                    "confidence": classification.confidence
                }
            )
        else:  # HYBRID
            return SearchStrategy(
                use_db_filter=True,
                use_vector_search=True,
                db_filter_params={
                    "keywords": classification.filter_keywords,
                    "confidence": classification.confidence
                },
                vector_search_params={
                    "keywords": classification.search_keywords,
                    "confidence": classification.confidence
                }
            )
