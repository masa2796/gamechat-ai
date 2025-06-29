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
            api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.getenv("BACKEND_OPENAI_API_KEY")
            
            # APIキーの検証
            if not api_key or api_key in ["your_openai_api_key", "your_actual_openai_api_key_here", "sk-test_openai_key"]:
                raise ClassificationException(
                    "OpenAI APIキーが設定されていません。.envファイルでBACKEND_OPENAI_API_KEYを設定してください。"
                )
            
            self.client = openai.OpenAI(api_key=api_key)
            self.is_mocked = False
        self.system_prompt = """あなたはゲーム攻略データベースのクエリ分類システムです。
ユーザーの質問を分析し、最適な検索戦略を決定してください。

分類タイプ:
1. "greeting" - 挨拶・雑談（検索不要）
   例：「こんにちは」「おはよう」「ありがとう」「よろしく」「お疲れ様」
   例：「元気？」「調子はどう？」「今日は暑いね」
2. "filterable" - 具体的な条件での絞り込み検索
   例：「HPが100以上のカード」「炎タイプのカード」「レアリティがRRのカード」
   例：「ダメージが40以上の技を持つカード」「水タイプのカード」
   例：「ダメージが40以上の技を持つ、水タイプカード」（複合条件）
3. "semantic" - 意味的な検索
   例：「強いカードを教えて」「おすすめの戦略」「初心者向けのデッキ」
4. "hybrid" - 両方の組み合わせ
   例：「炎タイプで強いカード」「HPが高くて使いやすいカード」

重要: 挨拶や一般的な会話は「greeting」として分類し、検索キーワードは空にしてください。

フィルターキーワードの例:
- 数値条件: "HP", "100以上", "50以上", "200以下", "ダメージ", "40以上", "30以下"
- タイプ: "炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"
- レアリティ: "C", "UC", "R", "RR", "SR", "SAR"
- 種類: "たね", "1進化", "2進化", "ex", "V", "VMAX"
- 技関連: "技", "攻撃", "ダメージ", "威力"

検索キーワードの例:
- 抽象的概念: "強い", "弱い", "おすすめ", "人気", "使いやすい"
- 戦略: "攻撃的", "守備的", "サポート", "コンボ"

重要: 複合条件の場合は、すべての条件をfilter_keywordsに含めてください。
例：「ダメージが40以上の技を持つ、水タイプカード」
→ filter_keywords: ["ダメージ", "40以上", "技", "水", "タイプ"]

**必ず以下のJSON形式のみで回答してください。他の文章は含めず、JSONのみを出力してください:**
{
    "query_type": "greeting",
    "summary": "要約されたクエリ",
    "confidence": 0.8,
    "filter_keywords": ["フィルター用キーワード"],
    "search_keywords": ["検索用キーワード"],
    "reasoning": "分類理由"
}"""

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
            
            # フィルター判定
            filter_keywords_found = []
            if any(word in query_lower for word in ["hp", "ダメージ", "以上", "以下", "タイプ", "レア"]):
                filter_keywords_found = ["hp", "ダメージ"] if "hp" in query_lower or "ダメージ" in query_lower else ["タイプ"]
                return ClassificationResult(
                    query_type=QueryType.FILTERABLE,
                    summary=f"フィルター検索: {request.query}",
                    confidence=0.8,
                    filter_keywords=filter_keywords_found,
                    search_keywords=[],
                    reasoning="具体的な条件が検出されました"
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
        
        user_prompt = f"質問: {request.query}"
        
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
        
        try:
            result_data = json.loads(result_text)
            classification = ClassificationResult(**result_data)
            
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
            GameChatLogger.log_error("classification_service", "予期しないエラー", e)
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
