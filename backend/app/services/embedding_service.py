from typing import List, Dict, Any
import openai
import os
import asyncio
import random
from dotenv import load_dotenv
from ..models.classification_models import ClassificationResult, QueryType
from ..core.exceptions import EmbeddingException
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger

load_dotenv()

class EmbeddingService:
    def __init__(self) -> None:
        # モック環境のチェック
        mock_external = os.getenv("BACKEND_MOCK_EXTERNAL_SERVICES", "false").lower() == "true"
        is_testing = os.getenv("BACKEND_TESTING", "false").lower() == "true"
        
        if mock_external or is_testing:
            # モック環境では実際のOpenAIクライアントは初期化しない
            self.client = None
            self.is_mocked = True
        else:
            # OpenAI クライアントを初期化（環境変数からAPIキーを取得）
            api_key = os.getenv("BACKEND_OPENAI_API_KEY")
            
            # テスト用のダミーキーの除外
            invalid_keys = ["sk-test_openai_key", "test-api-key"]
            
            if not api_key or api_key in invalid_keys:
                raise EmbeddingException(
                    message="OpenAI APIキーが設定されていません",
                    code="API_KEY_NOT_SET"
                )
            
            # テスト用のダミーAPIキーの場合はそのまま通す
            self.client = openai.OpenAI(api_key=api_key)
            self.is_mocked = False

    @handle_service_exceptions("embedding")
    async def get_embedding(self, query: str) -> List[float]:
        """質問文をOpenAI APIでエンベディングに変換"""
        # モック環境での処理
        if self.is_mocked:
            GameChatLogger.log_info("embedding_service", "モック環境で埋め込み生成", {
                "query_length": len(query),
                "query_preview": query[:50]
            })
            # 固定のダミー埋め込みベクトル（1536次元）を返す
            import hashlib
            hash_object = hashlib.md5(query.encode())
            hash_hex = hash_object.hexdigest()
            # ハッシュから決定論的にベクトルを生成
            dummy_embedding = []
            for i in range(1536):
                dummy_embedding.append((int(hash_hex[i % len(hash_hex)], 16) - 7.5) / 7.5)
            return dummy_embedding
        
        if not self.client:
            raise EmbeddingException(
                message="OpenAI APIキーが設定されていません",
                code="API_KEY_NOT_SET"
            )
        
        GameChatLogger.log_info("embedding_service", "埋め込み生成開始", {
            "query_length": len(query),
            "query_preview": query[:50]
        })
        
        # レート制限対応のためのリトライ処理
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                GameChatLogger.log_info("embedding_service", f"OpenAI Embedding API呼び出し開始 (試行 {attempt + 1}/{max_retries + 1})")
                
                response = self.client.embeddings.create(
                    input=query,
                    model="text-embedding-3-small",
                    timeout=10  # API呼び出しタイムアウト
                )
                
                GameChatLogger.log_success("embedding_service", "埋め込み生成完了", {
                    "embedding_dimension": len(response.data[0].embedding),
                    "attempt": attempt + 1
                })
                
                return response.data[0].embedding
                
            except openai.RateLimitError as e:
                if attempt == max_retries:
                    GameChatLogger.log_error("embedding_service", "OpenAI Embedding APIレート制限、全リトライ試行完了", e)
                    raise EmbeddingException(
                        message="OpenAI APIのレート制限に達しました。しばらく待ってから再試行してください。",
                        code="RATE_LIMIT_EXCEEDED"
                    ) from e
                else:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    GameChatLogger.log_warning("embedding_service", f"OpenAI Embedding APIレート制限エラー、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})")
                    asyncio.run(asyncio.sleep(delay))
                    continue
                    
            except Exception as e:
                error_str = str(e)
                # その他のエラーもレート制限の可能性があるかチェック
                if "429" in error_str or "rate_limit" in error_str.lower() or "too many requests" in error_str.lower():
                    if attempt == max_retries:
                        GameChatLogger.log_error("embedding_service", f"OpenAI Embedding APIレート制限（その他）、全リトライ試行完了: {error_str}", e)
                        raise EmbeddingException(
                            message="現在多くのリクエストが集中しているため処理できません。少し時間をおいてからもう一度お試しください。",
                            code="RATE_LIMIT_EXCEEDED"
                        ) from e
                    else:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        GameChatLogger.log_warning("embedding_service", f"OpenAI Embedding APIレート制限エラー（その他）、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})")
                        asyncio.run(asyncio.sleep(delay))
                        continue
                else:
                    GameChatLogger.log_error("embedding_service", f"OpenAI Embedding API呼び出しエラー (試行 {attempt + 1}): {error_str}", e)
                    raise EmbeddingException(
                        message=f"埋め込み生成中にエラーが発生しました: {error_str}",
                        code="EMBEDDING_ERROR"
                    ) from e
        
        # ここには到達しないはずだが、フォールバック
        raise EmbeddingException(
            message="埋め込み生成中に予期しないエラーが発生しました",
            code="UNEXPECTED_ERROR"
        )

    @handle_service_exceptions("embedding", fallback_return=None)
    async def get_embedding_from_classification(
        self, 
        original_query: str, 
        classification: ClassificationResult
    ) -> List[float]:
        """
        分類結果に基づいて最適化された埋め込みを生成します。
        
        LLMによる分類結果の信頼度とクエリタイプに応じて、
        最適な埋め込み用テキストを決定し、ベクトル検索の精度を向上させます。
        
        Args:
            original_query: 元の質問文
                例: "HP100以上の強いカード"
            classification: LLMによる分類結果
                - query_type: SEMANTIC, FILTERABLE, HYBRID, GREETING
                - confidence: 0.0-1.0の信頼度
                - summary: LLMが生成した要約
                - search_keywords: セマンティック検索用キーワード
                - filter_keywords: フィルター検索用キーワード
                
        Returns:
            1536次元の埋め込みベクトル (text-embedding-3-small使用)
            
        Raises:
            EmbeddingException: OpenAI APIキーが設定されていない場合
            EmbeddingException: API呼び出しでエラーが発生した場合
            
        Examples:
            >>> service = EmbeddingService()
            >>> classification = ClassificationResult(
            ...     query_type=QueryType.SEMANTIC,
            ...     confidence=0.9,
            ...     summary="強いカードの情報を検索",
            ...     search_keywords=["強い", "カード"]
            ... )
            >>> embedding = await service.get_embedding_from_classification(
            ...     "強いカードを教えて", classification
            ... )
            >>> print(len(embedding))  # 1536
            
        Note:
            信頼度に基づくフォールバック戦略:
            - 高信頼度(0.8+): LLMの要約を使用
            - 中信頼度(0.5+): キーワード + 元質問
            - 低信頼度(0.5未満): 元質問をそのまま使用
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
        
        # レート制限対応のためのリトライ処理
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                GameChatLogger.log_info("embedding_service", f"OpenAI Embedding API呼び出し開始 (分類ベース) (試行 {attempt + 1}/{max_retries + 1})")
                
                response = self.client.embeddings.create(
                    input=embedding_text,
                    model="text-embedding-3-small",
                    timeout=10  # API呼び出しタイムアウト
                )
                
                result = response.data[0].embedding
                
                # フォールバック処理
                if not result:
                    GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
                    fallback_result = await self.get_embedding(original_query)
                    return fallback_result if fallback_result is not None else []
                    
                GameChatLogger.log_success("embedding_service", "埋め込み生成完了（分類ベース）", {
                    "embedding_dimension": len(result),
                    "attempt": attempt + 1
                })
                
                return result
                
            except openai.RateLimitError as e:
                if attempt == max_retries:
                    GameChatLogger.log_error("embedding_service", "OpenAI Embedding APIレート制限（分類ベース）、全リトライ試行完了", e)
                    # レート制限の場合はフォールバックを試行
                    GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
                    fallback_result = await self.get_embedding(original_query)
                    return fallback_result if fallback_result is not None else []
                else:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    GameChatLogger.log_warning("embedding_service", f"OpenAI Embedding APIレート制限エラー（分類ベース）、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})")
                    asyncio.run(asyncio.sleep(delay))
                    continue
                    
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str.lower() or "too many requests" in error_str.lower():
                    if attempt == max_retries:
                        GameChatLogger.log_error("embedding_service", f"OpenAI Embedding APIレート制限（分類ベース・その他）、全リトライ試行完了: {error_str}", e)
                        # レート制限の場合はフォールバックを試行
                        GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
                        fallback_result = await self.get_embedding(original_query)
                        return fallback_result if fallback_result is not None else []
                    else:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        GameChatLogger.log_warning("embedding_service", f"OpenAI Embedding APIレート制限エラー（分類ベース・その他）、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})")
                        asyncio.run(asyncio.sleep(delay))
                        continue
                else:
                    GameChatLogger.log_error("embedding_service", f"OpenAI Embedding API呼び出しエラー（分類ベース） (試行 {attempt + 1}): {error_str}", e)
                    # 通常のエラーの場合もフォールバックを試行
                    GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
                    fallback_result = await self.get_embedding(original_query)
                    return fallback_result if fallback_result is not None else []
        
        # ここには到達しないはずだが、フォールバック
        GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
        fallback_result = await self.get_embedding(original_query)
        return fallback_result if fallback_result is not None else []

    def _determine_embedding_text(
        self, 
        original_query: str, 
        classification: ClassificationResult
    ) -> str:
        """
        分類結果に基づいて埋め込み用のテキストを決定します。
        
        LLMによる分類の信頼度とクエリタイプに応じて、最適な埋め込み用テキストを選択します。
        高信頼度の場合はLLMの要約を使用し、中～低信頼度の場合は段階的にフォールバックします。
        
        Args:
            original_query: 元の質問文
                例: "HP100以上の強いカード"
            classification: LLMによる分類結果
                - confidence: 分類の信頼度（0.0-1.0）
                - summary: LLMが生成した要約
                - search_keywords: セマンティック検索用キーワード
                - filter_keywords: フィルター検索用キーワード
                - query_type: クエリタイプ（SEMANTIC, FILTERABLE, HYBRID, GREETING）
                
        Returns:
            埋め込み生成に使用するテキスト
            
        Raises:
            なし（フォールバック戦略により常に文字列を返す）
            
        Examples:
            >>> service = EmbeddingService()
            >>> classification = ClassificationResult(
            ...     confidence=0.9,
            ...     summary="HP100以上のカードの検索",
            ...     query_type=QueryType.FILTERABLE
            ... )
            >>> text = service._determine_embedding_text(
            ...     "HP100以上のカード", classification
            ... )
            >>> print(text)
            "HP100以上のカードの検索"
            
            >>> # 中信頼度の場合
            >>> classification = ClassificationResult(
            ...     confidence=0.7,
            ...     search_keywords=["強い", "カード"],
            ...     query_type=QueryType.SEMANTIC
            ... )
            >>> text = service._determine_embedding_text(
            ...     "強いカードを教えて", classification
            ... )
            >>> print(text)
            "強い カード 強いカードを教えて"
            
        Note:
            フォールバック戦略:
            1. 高信頼度（0.8以上）: 要約を優先使用
            2. 中信頼度（0.5以上）: キーワード + 元質問
            3. 低信頼度（0.5未満）: 元質問をそのまま使用
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
        # ゲームカード特有のキーワードが保持されているかチェック
        important_keywords = ["カード", "カード", "HP", "ダメージ", "技", "タイプ", "進化", "レアリティ"]
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
