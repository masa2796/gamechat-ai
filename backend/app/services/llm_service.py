from typing import List, Optional, Dict, Any
import openai
import os
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationResult, QueryType
from ..core.config import settings

class LLMService:
    def __init__(self):
        # OpenAI クライアントを初期化
        api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

    async def generate_answer(
        self, 
        query: str, 
        context_items: List[ContextItem],
        classification: Optional[ClassificationResult] = None,
        search_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """検索結果と元の質問、分類結果を元にLLMで回答を生成"""
        if not self.client:
            return "申し訳ありませんが、現在回答生成サービスが利用できません。"
        
        # 挨拶の場合は専用の応答を生成
        if classification and classification.query_type == QueryType.GREETING:
            return self._generate_greeting_response(query, classification)
        
        try:
            # コンテキストテキストを結合（より構造化された形式で）
            context_text = self._format_context_items(context_items)
            
            # コンテキスト品質を分析
            context_quality = self._analyze_context_quality(context_items)
            
            # 分類結果の要約テキスト生成
            classification_summary = self._format_classification_info(classification)
            
            # 検索情報の要約（品質分析結果を含む）
            search_summary = self._format_search_info(search_info, context_quality)
            
            # 改良されたシステムプロンプト
            system_prompt = self._get_optimized_system_prompt()
            
            # より文脈に沿ったユーザープロンプト構成
            user_prompt = self._build_enhanced_user_prompt(
                query, context_text, classification_summary, search_summary, context_quality
            )

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,  # 簡潔な回答を促すため削減
                temperature=0.3,  # より一貫性のある回答のため下げる
                presence_penalty=0.1,  # 冗長性を減らす
                frequency_penalty=0.1  # 繰り返しを減らす
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM回答生成エラー: {e}")
            return f"申し訳ありませんが、「{query}」に関する回答の生成中にエラーが発生しました。"

    def _generate_greeting_response(self, query: str, classification: ClassificationResult) -> str:
        """挨拶専用の応答を生成"""
        # 一般的な挨拶パターンに対する定型応答
        greeting_responses = {
            "こんにちは": "こんにちは！今日はどんなポケモンカードについて知りたいですか？",
            "おはよう": "おはようございます！何かポケモンカードで調べたいことはありますか？",
            "こんばんは": "こんばんは！ポケモンカードについて何でもお聞きください。",
            "はじめまして": "はじめまして！ポケモンカードの情報なら何でもお任せください。",
            "ありがとう": "どういたしまして！他にもポケモンカードについて知りたいことがあればお気軽にどうぞ。",
            "お疲れさま": "お疲れさまです！ポケモンカードで何か調べたいことはありますか？",
            "よろしく": "こちらこそよろしくお願いします！ポケモンカードについて何でもお聞きください。"
        }
        
        # クエリを正規化（ひらがな・カタカナ・漢字の違いを吸収）
        normalized_query = query.lower().strip()
        
        # 部分一致で挨拶を検出
        for greeting, response in greeting_responses.items():
            if greeting in normalized_query:
                return response
        
        # デフォルトの挨拶応答
        return "こんにちは！ポケモンカードについて何でもお聞きください。どんなカードについて知りたいですか？"

    def _analyze_context_quality(self, context_items: List[ContextItem]) -> Dict[str, Any]:
        """コンテキストの品質を分析し、回答戦略を決定"""
        if not context_items:
            return {
                "avg_score": 0.0,
                "quality_level": "no_results",
                "response_strategy": "alternative_suggestion"
            }
        
        avg_score = sum(item.score for item in context_items) / len(context_items)
        best_score = max(item.score for item in context_items)
        
        if best_score >= 0.8:
            quality_level = "high"
            response_strategy = "detailed_answer"
        elif best_score >= 0.6:
            quality_level = "medium"
            response_strategy = "focused_answer"
        elif best_score >= 0.4:
            quality_level = "low"
            response_strategy = "general_guidance"
        else:
            quality_level = "very_low"
            response_strategy = "alternative_suggestion"
        
        return {
            "avg_score": avg_score,
            "best_score": best_score,
            "quality_level": quality_level,
            "response_strategy": response_strategy,
            "result_count": len(context_items)
        }

    def _format_context_items(self, context_items: List[ContextItem]) -> str:
        """コンテキストアイテムを構造化された形式でフォーマット"""
        if not context_items:
            return "関連する情報が見つかりませんでした。"
        
        formatted_items = []
        for i, item in enumerate(context_items, 1):
            formatted_items.append(
                f"【参考情報 {i}】\n"
                f"タイトル: {item.title}\n"
                f"関連度: {item.score:.2f}\n"
                f"内容: {item.text}\n"
            )
        
        return "\n".join(formatted_items)
    
    def _format_classification_info(self, classification: Optional[ClassificationResult]) -> str:
        """分類結果の情報をフォーマット"""
        if not classification:
            return ""
        
        return f"""
【質問の分析結果】
- 質問タイプ: {classification.query_type.value}
- 要約: {classification.summary}
- 信頼度: {classification.confidence:.2f}
- 分類理由: {classification.reasoning}
"""
    
    def _format_search_info(self, search_info: Optional[Dict[str, Any]], context_quality: Optional[Dict[str, Any]] = None) -> str:
        """検索情報をフォーマット"""
        if not search_info and not context_quality:
            return ""
        
        info_parts = []
        
        if search_info:
            info_parts.append(f"""
【検索実行情報】
- DB検索結果数: {search_info.get('db_results_count', 0)}件
- ベクトル検索結果数: {search_info.get('vector_results_count', 0)}件
- 検索品質評価: {search_info.get('search_quality', {}).get('overall_score', 'N/A')}""")
        
        if context_quality:
            info_parts.append(f"""
【回答品質指標】
- 関連度スコア: {context_quality.get('best_score', 0.0):.2f}
- 回答戦略: {context_quality.get('response_strategy', 'standard')}
- 結果件数: {context_quality.get('result_count', 0)}件""")
        
        return "\n".join(info_parts)
    
    def _get_optimized_system_prompt(self) -> str:
        """最適化されたシステムプロンプトを返す"""
        return """あなたは専門的なゲーム攻略AIアシスタントです。以下の指針に従って回答してください。

### 回答方針:
1. **文脈重視**: 提供された質問分析結果と検索情報を活用し、ユーザーの意図に正確に応答する
2. **簡潔性**: 冗長な説明を避け、要点を明確に伝える（理想的な文字数：100-200文字）
3. **親しみやすさ**: フレンドリーな口調を保ちつつ、専門性を示す
4. **価値提供**: 単純な情報提供でなく、ユーザーの判断に役立つ洞察を含める

### 応答パターン:

**具体的な情報検索（関連度高）**:
- 検索結果の核心を2-3文で要約
- 数値やスペックは正確に記載
- 実用的なアドバイスを1文で追加
- 冗長な前置きや説明は省略

**一般的な質問（関連度中）**:
- 検索結果から最も関連性の高い情報を選択
- 具体例を1つ提示
- 「他にも〇〇については△△ですよ」形式で補足
- 必要に応じて追加質問を促す

**関連度低・検索結果不足**:
- 「〇〇についての詳細情報は見つからませんでしたが」で開始
- 類似項目や代替案を提案
- 検索キーワードの改善案を提示

**雑談・あいさつ**:
- 1文で簡潔に応答
- 自然にゲーム関連の話題に誘導
- 例：「こんにちは！今日はどんなカードについて知りたいですか？」

**範囲外の質問**:
- 「ゲーム関連のことでしたらお手伝いできます」
- 追加の説明や謝罪は不要

**不適切な内容**:
- 「申し訳ありませんが、そのような内容にはお答えできません」
- 追加説明なし

### 口調・文体の指針:
- 敬語は使用せず、丁寧で親しみやすい口調
- 「です・ます」調で統一
- 感嘆符（！）は適度に使用（1回答につき1-2個まで）
- 絵文字は使用しない
- 「〜ですね」「〜ますよ」で自然な親しみやすさを演出

### 冗長性の排除:
❌ 避けるべき表現:
- 「詳しく説明しますと」「まず最初に」
- 「ご質問いただきありがとうございます」
- 「以下のような情報があります」
- 過度な修飾語や装飾的表現

✅ 推奨表現:
- 結論を先に述べる
- 必要な情報のみを簡潔に
- 自然で読みやすい文章構成

### 回答の品質基準:
- 高関連度（0.8以上）: 詳細で具体的な回答（150-200文字）
- 中関連度（0.5-0.8）: 要点を絞った回答（100-150文字）
- 低関連度（0.5未満）: 代替提案中心（80-120文字）

必ず上記の方針に従い、質問の文脈を考慮した適切で簡潔な回答を生成してください。"""
    
    def _build_enhanced_user_prompt(
        self, 
        query: str, 
        context_text: str, 
        classification_summary: str, 
        search_summary: str,
        context_quality: Optional[Dict[str, Any]] = None
    ) -> str:
        """強化されたユーザープロンプトを構築"""
        prompt_parts = [f"【ユーザーの質問】\n{query}"]
        
        if classification_summary:
            prompt_parts.append(classification_summary)
        
        if search_summary:
            prompt_parts.append(search_summary)
        
        prompt_parts.append(f"【検索結果】\n{context_text}")
        
        # 回答戦略に基づく具体的な指示
        strategy_instructions = self._get_strategy_instructions(context_quality)
        
        prompt_parts.append(f"""
【回答指示】
上記の質問分析結果と検索結果を参考に、以下の条件を満たす回答を生成してください：

{strategy_instructions}

1. **簡潔性重視**: 100-200文字程度で要点を明確に
2. **文脈活用**: 分類結果で示された質問の意図を正確に理解
3. **関連度考慮**: 検索結果の関連度スコアに基づいて回答の詳細度を調整
4. **実用性**: ユーザーの判断や行動に直接役立つ情報を優先
5. **自然な口調**: 親しみやすく、専門的すぎない表現

前置きや冗長な説明は省略し、核心となる情報を中心に構成してください。
""")
        
        return "\n".join(prompt_parts)
    
    def _get_strategy_instructions(self, context_quality: Optional[Dict[str, Any]]) -> str:
        """回答戦略に基づく具体的な指示を生成"""
        if not context_quality:
            return "**標準的な回答**: 利用可能な情報を基に適切に回答してください。"
        
        strategy = context_quality.get("response_strategy", "standard")
        
        strategy_map = {
            "detailed_answer": "**詳細回答**: 高い関連度の検索結果を活用し、具体的で実用的な情報を中心に回答してください。",
            "focused_answer": "**要点回答**: 最も関連性の高い情報を選択し、簡潔に要点をまとめて回答してください。",
            "general_guidance": "**一般的案内**: 限られた情報から可能な範囲でアドバイスし、追加の質問を促してください。",
            "alternative_suggestion": "**代替提案**: 直接的な回答は困難ですが、関連する情報や改良された検索提案を行ってください。"
        }
        
        return strategy_map.get(strategy, "**標準的な回答**: 利用可能な情報を基に適切に回答してください。")

    # 下位互換性のための旧メソッド
    async def generate_answer_legacy(self, query: str, context_items: List[ContextItem]) -> str:
        """下位互換性のための旧generate_answerメソッド"""
        return await self.generate_answer(query, context_items)