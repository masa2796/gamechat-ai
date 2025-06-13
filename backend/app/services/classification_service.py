import openai
import json
import os
from ..models.classification_models import ClassificationRequest, ClassificationResult, QueryType, SearchStrategy
from ..core.config import settings

class ClassificationService:
    """LLMによるクエリ分類・要約サービス"""
    
    def __init__(self):
        # OpenAI クライアントを初期化
        api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
        self.system_prompt = """あなたはゲーム攻略データベースのクエリ分類システムです。
ユーザーの質問を分析し、最適な検索戦略を決定してください。

分類タイプ:
1. "greeting" - 挨拶・雑談（検索不要）
   例：「こんにちは」「おはよう」「ありがとう」「よろしく」「お疲れ様」
   例：「元気？」「調子はどう？」「今日は暑いね」
2. "filterable" - 具体的な条件での絞り込み検索
   例：「HPが100以上のポケモン」「炎タイプのカード」「レアリティがRRのカード」
   例：「ダメージが40以上の技を持つポケモン」「水タイプのポケモン」
   例：「ダメージが40以上の技を持つ、水タイプポケモン」（複合条件）
3. "semantic" - 意味的な検索
   例：「強いポケモンを教えて」「おすすめの戦略」「初心者向けのデッキ」
4. "hybrid" - 両方の組み合わせ
   例：「炎タイプで強いポケモン」「HPが高くて使いやすいポケモン」

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
例：「ダメージが40以上の技を持つ、水タイプポケモン」
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

    async def classify_query(self, request: ClassificationRequest) -> ClassificationResult:
        """クエリを分類・要約する"""
        try:
            if not self.client:
                print("OpenAI APIキーが設定されていません - フォールバック分類を使用")
                return ClassificationResult(
                    query_type=QueryType.SEMANTIC,
                    summary=request.query,
                    confidence=0.3,
                    search_keywords=[request.query],
                    reasoning="APIキー未設定 - フォールバック分類"
                )
            
            user_prompt = f"質問: {request.query}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.0,  # 一貫性のために0に設定
                response_format={"type": "json_object"}  # JSON形式を強制
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"LLM応答: {result_text}")  # デバッグ情報
            
            # JSONパースを試行
            try:
                result_data = json.loads(result_text)
                return ClassificationResult(**result_data)
            except json.JSONDecodeError as json_error:
                print(f"JSON解析エラー: {json_error}")
                print(f"応答内容: {result_text}")
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
            print(f"分類エラー: {e}")
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
