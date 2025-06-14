from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv
from ..models.classification_models import ClassificationResult, QueryType
from ..core.exceptions import EmbeddingException
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger

load_dotenv()

class EmbeddingService:
    def __init__(self):
        # OpenAI クライアントを初期化（環境変数からAPIキーを取得）
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

    @handle_service_exceptions("embedding")
    async def get_embedding(self, query: str) -> List[float]:
        """質問文をOpenAI APIでエンベディングに変換"""
        if not self.client:
            raise EmbeddingException(
                message="OpenAI APIキーが設定されていません",
                code="API_KEY_NOT_SET"
            )
        
        GameChatLogger.log_info("embedding_service", "埋め込み生成開始", {
            "query_length": len(query),
            "query_preview": query[:50]
        })
        
        response = self.client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        
        GameChatLogger.log_success("embedding_service", "埋め込み生成完了", {
            "embedding_dimension": len(response.data[0].embedding)
        })
        
        return response.data[0].embedding

    @handle_service_exceptions("embedding", fallback_return=None)
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
            raise EmbeddingException(
                message="OpenAI APIキーが設定されていません",
                code="API_KEY_NOT_SET"
            )

        # 埋め込み対象テキストを決定
        embedding_text = self._determine_embedding_text(original_query, classification)
        
        GameChatLogger.log_info("embedding_service", "分類ベース埋め込み生成", {
            "original_query": original_query[:50],
            "embedding_text": embedding_text[:50],
            "classification_type": classification.query_type,
            "confidence": classification.confidence
        })
        
        response = self.client.embeddings.create(
            input=embedding_text,
            model="text-embedding-3-small"
        )
        
        result = response.data[0].embedding
        
        # フォールバック処理
        if not result:
            GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
            return await self.get_embedding(original_query)
            
        return result

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
        GameChatLogger.log_info("embedding_service", "フォールバック: 元質問を使用", {
            "confidence": classification.confidence
        })
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
            GameChatLogger.log_warning("embedding_service", "要約が短すぎます", {
                "summary_length": len(summary)
            })
            return False
            
        if len(summary) > len(original_query) * 1.5:
            GameChatLogger.log_warning("embedding_service", "要約が長すぎます", {
                "summary_length": len(summary),
                "threshold": len(original_query) * 1.5
            })
            return False
        
        # 基本的な品質チェック（重要なキーワードの保持）
        # ポケモンカード特有のキーワードが保持されているかチェック
        important_keywords = ["ポケモン", "カード", "HP", "ダメージ", "技", "タイプ", "進化", "レアリティ"]
        original_has_keywords = any(keyword in original_query for keyword in important_keywords)
        summary_has_keywords = any(keyword in summary for keyword in important_keywords)
        
        if original_has_keywords and not summary_has_keywords:
            GameChatLogger.log_warning("embedding_service", "要約に重要なキーワードが含まれていません")
            return False
            
        return True

    def get_embedding_stats(self, classification: ClassificationResult) -> Dict[str, Any]:
        """埋め込み生成の統計情報を取得"""
        
        embedding_text = self._determine_embedding_text("sample query", classification)
        
        return {
            "strategy": self._get_embedding_strategy(classification),
            "embedding_text_length": len(embedding_text),
            "confidence": classification.confidence,
            "query_type": classification.query_type
        }

    def _get_embedding_strategy(self, classification: ClassificationResult) -> str:
        """現在の埋め込み戦略を取得"""
        if classification.confidence >= 0.8 and classification.summary:
            return "high_confidence_summary"
        elif classification.confidence >= 0.5 and (classification.search_keywords or classification.filter_keywords):
            return "medium_confidence_keywords"
        else:
            return "fallback_original"
