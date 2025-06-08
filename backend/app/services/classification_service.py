import openai
import json
from ..models.classification_models import ClassificationRequest, ClassificationResult, QueryType, SearchStrategy
from ..core.config import settings

openai.api_key = settings.OPENAI_API_KEY

class ClassificationService:
    """LLMによるクエリ分類・要約サービス"""
    
    def __init__(self):
        self.system_prompt = """あなたはゲーム攻略データベースのクエリ分類システムです。
ユーザーの質問を分析し、最適な検索戦略を決定してください。

分類タイプ:
1. "filterable" - 具体的な条件での絞り込み検索
   例：「HPが100以上のポケモン」「炎タイプのカード」「レアリティがRRのカード」
2. "semantic" - 意味的な検索
   例：「強いポケモンを教えて」「おすすめの戦略」「初心者向けのデッキ」
3. "hybrid" - 両方の組み合わせ
   例：「炎タイプで強いポケモン」「HPが高くて使いやすいポケモン」

フィルターキーワードの例:
- 数値条件: "HP", "100以上", "50以上", "200以下"
- タイプ: "炎", "水", "草", "電気", "超", "闘", "悪", "鋼", "フェアリー"
- レアリティ: "C", "UC", "R", "RR", "SR", "SAR"
- 種類: "たね", "1進化", "2進化", "ex", "V", "VMAX"

検索キーワードの例:
- 抽象的概念: "強い", "弱い", "おすすめ", "人気", "使いやすい"
- 戦略: "攻撃的", "守備的", "サポート", "コンボ"

必ず以下のJSON形式で回答してください:
{
    "query_type": "filterable|semantic|hybrid",
    "summary": "要約されたクエリ",
    "confidence": 0.0-1.0の信頼度,
    "filter_keywords": ["フィルター用キーワード"],
    "search_keywords": ["検索用キーワード"],
    "reasoning": "分類理由"
}"""

    async def classify_query(self, request: ClassificationRequest) -> ClassificationResult:
        """クエリを分類・要約する"""
        try:
            user_prompt = f"質問: {request.query}"
            
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.1  # 一貫性のために低めに設定
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSONパースを試行
            try:
                result_data = json.loads(result_text)
                return ClassificationResult(**result_data)
            except json.JSONDecodeError:
                # JSONパースに失敗した場合のフォールバック
                return ClassificationResult(
                    query_type=QueryType.SEMANTIC,
                    summary=request.query,
                    confidence=0.5,
                    search_keywords=[request.query],
                    reasoning="JSON解析エラー - デフォルト分類を適用"
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
        if classification.query_type == QueryType.FILTERABLE:
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
