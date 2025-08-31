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
from .query_normalization_service import QueryNormalizationService

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
        # クエリ正規化サービス（助詞の軽正規化/同義語の軽展開に利用）
        self._normalizer = QueryNormalizationService()
        # 軽正規化 / 同義語代表語追加の挙動を環境変数で制御 (ABテスト/将来調整用)
        self.enable_light_normalize = os.getenv("EMBED_LIGHT_NORMALIZE", "true").lower() == "true"
        self.enable_rep_terms = os.getenv("EMBED_ADD_REP_TERMS", "true").lower() == "true"

    @handle_service_exceptions("embedding")
    async def get_embedding(self, query: str) -> List[float]:
        """質問文をOpenAI APIでエンベディングに変換"""
        original_query = query
        if self.enable_light_normalize:
            try:
                # QueryNormalizationService に依存: tokenize + synonym map
                norm_result = self._normalizer.normalize(query)
                # 代表語を1語だけEmbedding用に後置（ノイズ抑制）
                if self.enable_rep_terms and norm_result.representative_terms:
                    rep = " ".join(norm_result.representative_terms[:3])  # 上限3語
                    query = f"{norm_result.normalized_query}\n{rep}" if rep else norm_result.normalized_query
                else:
                    query = norm_result.normalized_query
            except Exception as e:  # フォールバック: 元のクエリを使用
                GameChatLogger.log_warning("embedding_service", f"軽正規化失敗 fallback: {e}")
                query = original_query
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
            "query_preview": query[:50],
            "light_normalize": self.enable_light_normalize,
            "rep_terms": self.enable_rep_terms
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
                    await asyncio.sleep(delay)
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
                        await asyncio.sleep(delay)
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
            "confidence": classification.confidence,
        })

        # レート制限対応のためのリトライ処理
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                GameChatLogger.log_info(
                    "embedding_service",
                    f"OpenAI Embedding API呼び出し開始 (分類ベース) (試行 {attempt + 1}/{max_retries + 1})",
                )

                response = self.client.embeddings.create(
                    input=embedding_text,
                    model="text-embedding-3-small",
                    timeout=10,  # API呼び出しタイムアウト
                )

                result = response.data[0].embedding

                # フォールバック処理
                if not result:
                    GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
                    fallback_result = await self.get_embedding(original_query)
                    return fallback_result if fallback_result is not None else []

                GameChatLogger.log_success(
                    "embedding_service",
                    "埋め込み生成完了（分類ベース）",
                    {"embedding_dimension": len(result), "attempt": attempt + 1},
                )

                return result

            except openai.RateLimitError as e:
                if attempt == max_retries:
                    GameChatLogger.log_error(
                        "embedding_service",
                        "OpenAI Embedding APIレート制限（分類ベース）、全リトライ試行完了",
                        e,
                    )
                    # レート制限の場合はフォールバックを試行
                    GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
                    fallback_result = await self.get_embedding(original_query)
                    return fallback_result if fallback_result is not None else []
                else:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    GameChatLogger.log_warning(
                        "embedding_service",
                        f"OpenAI Embedding APIレート制限エラー（分類ベース）、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})",
                    )
                    asyncio.run(asyncio.sleep(delay))
                    continue

            except Exception as e:
                error_str = str(e)
                if (
                    "429" in error_str
                    or "rate_limit" in error_str.lower()
                    or "too many requests" in error_str.lower()
                ):
                    if attempt == max_retries:
                        GameChatLogger.log_error(
                            "embedding_service",
                            f"OpenAI Embedding APIレート制限（分類ベース・その他）、全リトライ試行完了: {error_str}",
                            e,
                        )
                        # レート制限の場合はフォールバックを試行
                        GameChatLogger.log_warning("embedding_service", "埋め込み生成失敗、フォールバック実行")
                        fallback_result = await self.get_embedding(original_query)
                        return fallback_result if fallback_result is not None else []
                    else:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        GameChatLogger.log_warning(
                            "embedding_service",
                            f"OpenAI Embedding APIレート制限エラー（分類ベース・その他）、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})",
                        )
                        asyncio.run(asyncio.sleep(delay))
                        continue
                else:
                    GameChatLogger.log_error(
                        "embedding_service",
                        f"OpenAI Embedding API呼び出しエラー（分類ベース） (試行 {attempt + 1}): {error_str}",
                        e,
                    )
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
        
        # 効果文らしさの簡易判定: 効果テキストに近い場合は原文を優先して保持
        def _looks_like_effect_text(text: str) -> bool:
            if not text:
                return False
            cues = [
                "破壊", "選ぶ", "与える", "ダメージ", "手札", "戻す", "ランダム",
                "フォロワー", "リーダー", "場", "盤面", "ボード", "フィールド",
                "1枚", "すべて", "ランダムに", "このターン", "相手の", "自分の"
            ]
            hit = sum(1 for c in cues if c in text)
            # 句点や命令調の文体もヒントに
            punctuation_bonus = 1 if ("。" in text or "！" in text or "する" in text) else 0
            return (hit + punctuation_bonus) >= 2

        effect_like = _looks_like_effect_text(original_query)

        # 効果検索寄り（SEMANTIC/HYBRID）の場合は、効果キーワード抽出と助詞の軽正規化を適用した要約に寄せる
        def _effect_focus_if_needed(text: str) -> str:
            if classification.query_type in (QueryType.SEMANTIC, QueryType.HYBRID):
                focused = self._build_effect_focused_text(text)
                return focused if focused else text
            return text

        # 信頼度による戦略選択
        if classification.confidence >= 0.8:
            # 高信頼度: 要約を優先
            if classification.summary and len(classification.summary.strip()) > 5:
                if self._is_summary_quality_good(classification.summary, original_query):
                    # 効果文らしい場合は原文も併用して情報を保持
                    combined = (
                        f"{original_query}\n{classification.summary}"
                        if effect_like
                        else classification.summary
                    )
                    return _effect_focus_if_needed(combined)

        elif classification.confidence >= 0.5:
            # 中信頼度: キーワードと組み合わせ
            if classification.query_type == QueryType.SEMANTIC and classification.search_keywords:
                # セマンティック検索の場合、検索キーワードを活用
                keywords_text = " ".join(classification.search_keywords)
                # 効果文らしい場合は原文を先頭に
                combined = (
                    f"{original_query} {keywords_text}"
                    if effect_like
                    else f"{keywords_text} {original_query}"
                )
                return _effect_focus_if_needed(combined)
            elif classification.query_type == QueryType.HYBRID:
                # ハイブリッドの場合、両方のキーワードを活用
                all_keywords: List[str] = []
                if classification.search_keywords:
                    all_keywords.extend(classification.search_keywords)
                if classification.filter_keywords:
                    all_keywords.extend(classification.filter_keywords)
                if all_keywords:
                    keywords_text = " ".join(all_keywords)
                    combined = (
                        f"{original_query} {keywords_text}"
                        if effect_like
                        else f"{keywords_text} {original_query}"
                    )
                    return _effect_focus_if_needed(combined)

        # フォールバック: 元質問を使用（効果文らしい場合はそのままが強い）
        GameChatLogger.log_info(
            "embedding_service",
            "フォールバック: 元質問を使用",
            {"confidence": classification.confidence},
        )
        return _effect_focus_if_needed(original_query)

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
    
    def extract_embedding_text(self, card: dict) -> str:
        """
        カードデータからembedding対象テキストを抽出する（新仕様対応）
        - effect_1, effect_2, effect_3 など複数effectフィールド
        - qaリスト内のquestion/answer
        - flavorText（存在する場合）
        """
        texts = []
        # effect系フィールド
        for key in [f"effect_{i}" for i in range(1, 10)]:
            if key in card and card[key]:
                texts.append(card[key])
        # Q&A
        if "qa" in card and isinstance(card["qa"], list):
            for qa_item in card["qa"]:
                if "question" in qa_item and qa_item["question"]:
                    texts.append(qa_item["question"])
                if "answer" in qa_item and qa_item["answer"]:
                    texts.append(qa_item["answer"])
        # flavorText
        if "flavorText" in card and card["flavorText"]:
            texts.append(card["flavorText"])
        return "\n".join(texts)

    # --- 要約強化: 効果キーワード優先 + 助詞の軽正規化 ---
    def _build_effect_focused_text(self, text: str) -> str:
        """
        効果検索向けに、入力テキストを軽く正規化しつつ、効果/対象キーワードを強調した短い要約を生成。
        - QueryNormalizationService.preprocess を使って軽正規化
        - 埋め込み用の軽い同義語展開（expand_text_for_embedding）
        - 効果キーワード/対象語を抽出して末尾に付加
        - 助詞を軽く間引いた簡潔版も先頭に配置
        """
        if not text:
            return ""

        # 軽正規化 + 同義語の軽展開
        pre = self._light_normalize_japanese(text)
        expanded = self._normalizer.expand_text_for_embedding(pre, max_extra_terms_per_group=1)

        # 効果/対象語の抽出
        terms = self._extract_effect_terms(expanded)
        effects = terms.get("effects", [])
        targets = terms.get("targets", [])

        # 助詞の軽間引きで簡潔化
        compact = self._remove_common_particles(pre)

        # 最終テキスト構成
        lines: List[str] = []
        if compact:
            lines.append(compact)
        # キーワード群を末尾に薄く足す（順序のばらつきを避けるためソート）
        if effects:
            lines.append(" ".join(sorted(set(effects))))
        if targets:
            lines.append(" ".join(sorted(set(targets))))

        focused = "\n".join([ln for ln in lines if ln])

        # ログ（デバッグ用）
        GameChatLogger.log_debug(
            "embedding_service",
            "effect_focused_summary",
            {
                "original_len": len(text),
                "focused_len": len(focused),
                "effects": effects[:8],
                "targets": targets[:8],
            },
        )
        return focused or pre

    def _light_normalize_japanese(self, text: str) -> str:
        """NFKC/空白統一 + よくある言い回しの軽統一（できる/可能 など）"""
        s = self._normalizer.preprocess(text)
        # 言い換えの軽統一
        replacements = {
            "することができる": "できる",
            "可能": "できる",
            "与えることができる": "与える",
            "ダメージを与える": "ダメージ",
        }
        for k, v in replacements.items():
            if k in s:
                s = s.replace(k, v)
        return s.strip()

    def _remove_common_particles(self, text: str) -> str:
        """
        日本語の頻出助詞を軽く間引く（過剰な破壊を避けるため単純置換）。
        - 目的: 埋め込みのノイズ低減。原文構造は保ちすぎない範囲で簡略化。
        注意: 日本語にはスペースがないため、単純置換で最小限に留める。
        """
        particles = [
            " を", " に", " が", " は", " で", " と", " から", " より", " へ", " まで", " の", " って", " とか", " など",
            "を", "に", "が", "は", "で", "と", "から", "より", "へ", "まで", "の", "って", "とか", "など",
        ]
        s = text
        for p in particles:
            s = s.replace(p, " ")
        # 余分な空白整形
        s = " ".join(s.split())
        return s.strip()

    def _extract_effect_terms(self, text: str) -> Dict[str, List[str]]:
        """効果・対象の代表キーワードを抽出して返す"""
        effects_vocab = [
            # ダメージ/除去系
            "ダメージ", "直接ダメージ", "バーン", "継続ダメージ", "破壊", "消滅", "除去", "全体除去", "AoE",
            # ドロー/サーチ
            "ドロー", "サーチ", "引く",
            # 強化/弱体
            "強化", "全体強化", "バフ", "弱体化", "デバフ",
            # 能力系
            "疾走", "突進", "守護付与", "守護", "守護無視", "貫通",
            # 回復/バウンス/ランダム
            "回復", "手札に戻す", "バウンス", "ランダム",
            # トークン/進化/コスト/カウント
            "トークン", "進化", "コスト軽減", "コストを下げる", "コスト-1", "カウントダウン", "カウント-1",
            # その他
            "守護を失わせる",
        ]
        targets_vocab = [
            "相手", "自分", "リーダー", "顔", "フォロワー", "アミュレット", "盤面", "場", "フィールド", "手札", "デッキ", "墓場", "全体", "単体",
        ]

        found_effects: List[str] = []
        found_targets: List[str] = []
        for t in effects_vocab:
            if t and t in text:
                found_effects.append(t)
        for t in targets_vocab:
            if t and t in text:
                found_targets.append(t)
        # ユニーク化
        found_effects = list(dict.fromkeys(found_effects))
        found_targets = list(dict.fromkeys(found_targets))
        return {"effects": found_effects, "targets": found_targets}
