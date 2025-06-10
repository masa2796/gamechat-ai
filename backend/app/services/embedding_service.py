from typing import List, Dict, Any
import openai
from fastapi import HTTPException
import os
from dotenv import load_dotenv
from ..models.classification_models import ClassificationResult, QueryType

load_dotenv()

class EmbeddingService:
    def __init__(self):
        # OpenAI クライアントを初期化（環境変数からAPIキーを取得）
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

    async def get_embedding(self, query: str) -> List[float]:
        """質問文をOpenAI APIでエンベディングに変換"""
        if not self.client:
            raise HTTPException(status_code=500, detail={
                "message": "OpenAI APIキーが設定されていません",
                "code": "API_KEY_NOT_SET"
            })
        
        try:
            response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "message": f"エンベディング生成に失敗: {str(e)}",
                "code": "EMBEDDING_ERROR"
            })

    async def get_embedding_from_classification(
        self, 
        original_query: str, 
        classification: ClassificationResult
    ) -> List[float]:
        """
        分類結果に基づいて最適化された埋め込みを生成
        
        Args:
            original_query: 元の質問文
            classification: LLMによる分類結果
            
        Returns:
            埋め込みベクトル
        """
        if not self.client:
            raise HTTPException(status_code=500, detail={
                "message": "OpenAI APIキーが設定されていません",
                "code": "API_KEY_NOT_SET"
            })

        # 埋め込み対象テキストを決定
        embedding_text = self._determine_embedding_text(original_query, classification)
        
        print(f"[EmbeddingService] 埋め込み対象テキスト: {embedding_text}")
        print(f"[EmbeddingService] 分類タイプ: {classification.query_type}, 信頼度: {classification.confidence}")
        
        try:
            response = self.client.embeddings.create(
                input=embedding_text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[EmbeddingService] 埋め込み生成エラー: {e}")
            # フォールバック: 元の質問文で埋め込み生成
            return await self.get_embedding(original_query)

    def _determine_embedding_text(
        self, 
        original_query: str, 
        classification: ClassificationResult
    ) -> str:
        """
        分類結果に基づいて埋め込み用のテキストを決定
        
        フォールバック戦略:
        1. 高信頼度の要約がある場合 → 要約を使用
        2. 中信頼度で検索キーワードがある場合 → キーワード + 元質問
        3. 低信頼度またはエラー → 元質問を使用
        """
        
        # 信頼度による戦略選択
        if classification.confidence >= 0.8:
            # 高信頼度: 要約を優先
            if classification.summary and len(classification.summary.strip()) > 5:
                if self._is_summary_quality_good(classification.summary, original_query):
                    return classification.summary
                    
        elif classification.confidence >= 0.5:
            # 中信頼度: キーワードと組み合わせ
            if classification.query_type == QueryType.SEMANTIC and classification.search_keywords:
                # セマンティック検索の場合、検索キーワードを活用
                keywords_text = " ".join(classification.search_keywords)
                return f"{keywords_text} {original_query}"
            elif classification.query_type == QueryType.HYBRID:
                # ハイブリッドの場合、両方のキーワードを活用
                all_keywords = []
                if classification.search_keywords:
                    all_keywords.extend(classification.search_keywords)
                if classification.filter_keywords:
                    all_keywords.extend(classification.filter_keywords)
                if all_keywords:
                    keywords_text = " ".join(all_keywords)
                    return f"{keywords_text} {original_query}"
                    
        # フォールバック: 元質問を使用
        print(f"[EmbeddingService] フォールバック: 元質問を使用 (信頼度: {classification.confidence})")
        return original_query

    def _is_summary_quality_good(self, summary: str, original_query: str) -> bool:
        """
        要約の品質を評価
        
        評価基準:
        - 長さが適切か（5文字以上、元質問の150%以下）
        - 元質問の重要な要素を含んでいるか
        """
        summary = summary.strip()
        
        # 長さチェック
        if len(summary) < 5:
            print(f"[EmbeddingService] 要約が短すぎます: {len(summary)}文字")
            return False
            
        if len(summary) > len(original_query) * 1.5:
            print(f"[EmbeddingService] 要約が長すぎます: {len(summary)} > {len(original_query) * 1.5}")
            return False
        
        # 基本的な品質チェック（重要なキーワードの保持）
        # ポケモンカード特有のキーワードが保持されているかチェック
        important_keywords = ["ポケモン", "カード", "HP", "ダメージ", "技", "タイプ", "進化", "レアリティ"]
        original_has_keywords = any(keyword in original_query for keyword in important_keywords)
        summary_has_keywords = any(keyword in summary for keyword in important_keywords)
        
        if original_has_keywords and not summary_has_keywords:
            print("[EmbeddingService] 要約に重要なキーワードが含まれていません")
            return False
            
        return True

    def get_embedding_stats(self, classification: ClassificationResult) -> Dict[str, Any]:
        """埋め込み生成の統計情報を取得"""
        
        embedding_text = self._determine_embedding_text("sample query", classification)
        
        return {
            "strategy": self._get_embedding_strategy(classification),
            "text_length": len(embedding_text),
            "confidence_level": "high" if classification.confidence >= 0.8 else (
                "medium" if classification.confidence >= 0.5 else "low"
            ),
            "query_type": classification.query_type,
            "has_summary": bool(classification.summary and len(classification.summary.strip()) > 5),
            "has_search_keywords": bool(classification.search_keywords),
            "has_filter_keywords": bool(classification.filter_keywords)
        }
    
    def _get_embedding_strategy(self, classification: ClassificationResult) -> str:
        """使用される埋め込み戦略を取得"""
        
        if classification.confidence >= 0.8:
            if classification.summary and len(classification.summary.strip()) > 5:
                if self._is_summary_quality_good(classification.summary, "sample"):
                    return "summary_based"
        
        if classification.confidence >= 0.5:
            if classification.query_type == QueryType.SEMANTIC and classification.search_keywords:
                return "keywords_enhanced"
            elif classification.query_type == QueryType.HYBRID:
                return "hybrid_keywords"
        
        return "fallback_original"