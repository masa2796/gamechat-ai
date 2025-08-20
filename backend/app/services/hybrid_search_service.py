from typing import List, Dict, Any
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationRequest, ClassificationResult, QueryType
from ..core.config import settings
from .classification_service import ClassificationService
from .database_service import DatabaseService
from .vector_service import VectorService
from .embedding_service import EmbeddingService
from .query_normalization_service import QueryNormalizationService
from ..core.logging import GameChatLogger

class HybridSearchService:
    def _merge_results_weighted(
        self,
        db_titles: list[str],
        vector_titles: list[str],
        db_scores: dict,
        vector_scores: dict,
        classification: ClassificationResult,
        top_k: int,
        search_quality: dict,
    quality_threshold: float = 0.0
    ) -> list[str]:
        """
        スコア加重型のマージロジック（カード名リスト）
        - DB/ベクトル両方のスコアを活用し、重複除去・加重平均・スコア順ソート
        - 設計方針（重複除去・優先順位・重み付け・クエリタイプ分岐）に準拠
        """
        if not db_titles and not vector_titles:
            return self._handle_no_results_optimized(classification)

        # クエリタイプを正規化
        qtype = getattr(classification, "query_type", None)
        try:
            # Enumなら値に変換
            qtype_value = qtype.value  # type: ignore[attr-defined]
        except Exception:
            qtype_value = str(qtype).lower() if qtype is not None else "semantic"

        # 重み初期値（デフォルトはバランス）
        db_weight = 0.5
        vector_weight = 0.5

        # 種別に応じた重みチューニング
        if qtype_value in ("filterable", "querytype.filterable"):
            db_weight, vector_weight = 0.8, 0.2
        elif qtype_value in ("semantic", "querytype.semantic"):
            db_weight, vector_weight = 0.3, 0.7
        else:  # hybrid 他
            db_weight, vector_weight = 0.4, 0.6

        # 信頼度が高い場合は優勢側を微増
        try:
            conf = float(getattr(classification, "confidence", 0.0))
        except Exception:
            conf = 0.0
        if conf >= 0.85:
            if vector_weight > db_weight:
                vector_weight = min(0.8, vector_weight + 0.1)
                db_weight = 1.0 - vector_weight
            else:
                db_weight = min(0.9, db_weight + 0.05)
                vector_weight = 1.0 - db_weight
        merged_scores = {}
        all_titles = list(dict.fromkeys(db_titles + vector_titles))
        for title in all_titles:
            db_score = db_scores.get(title)
            vec_score = vector_scores.get(title)
            if db_score is not None and vec_score is not None:
                merged_scores[title] = db_score * db_weight + vec_score * vector_weight
            elif db_score is not None:
                merged_scores[title] = db_score
            elif vec_score is not None:
                merged_scores[title] = vec_score
            else:
                merged_scores[title] = 0.0

        # クエリタイプごとに優先度を調整
        if qtype_value in ("filterable", "querytype.filterable"):
            # DBスコアを優先
            sorted_titles = sorted(all_titles, key=lambda t: (t in db_titles, merged_scores[t]), reverse=True)
        elif qtype_value in ("semantic", "querytype.semantic"):
            # ベクトルスコアを優先
            sorted_titles = sorted(all_titles, key=lambda t: (t in vector_titles, merged_scores[t]), reverse=True)
        else:
            # 加重スコア順
            sorted_titles = sorted(all_titles, key=lambda t: merged_scores[t], reverse=True)

        # 品質スコアによるフィルタリング
        if quality_threshold > 0.0:
            filtered_titles = [t for t in sorted_titles if merged_scores.get(t, 0.0) >= quality_threshold]
        else:
            filtered_titles = sorted_titles

        # 上位N件抽出
        result_titles = filtered_titles[:top_k]

        # 不足時の補完・提案メッセージ生成（但し、提案は別途処理）
        # result_titlesはカード名のみとし、提案メッセージは含めない
        return result_titles
    """分類に基づく統合検索サービス（最適化対応）"""
    
    def __init__(self) -> None:
        self.classification_service = ClassificationService()
        self.database_service = DatabaseService()
        self.vector_service = VectorService()
        self.embedding_service = EmbeddingService()
        self.query_normalizer = QueryNormalizationService()
    
    async def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        クエリを分類し、最適化された検索戦略でカード名リストを返却

        このメソッドはハイブリッド検索システムの中核となる機能で、
        LLMによる分類結果に基づいて最適な検索戦略を選択し、
        データベース検索とベクトル検索を組み合わせて最適な結果を返します。

        Args:
            query: 検索クエリ文字列
            top_k: 返却する最大結果数 (デフォルト: 3)

        Returns:
            検索結果情報の辞書
        """
        print("=== 最適化統合検索開始 ===")
        print(f"クエリ: {query}")

        # Step 0: クエリ正規化（前処理）
        preprocessed_query = self.query_normalizer.preprocess(query)
        print(f"[Normalize] 原文→前処理: '{query}' -> '{preprocessed_query}'")
        # DEBUG: 正規化前後のクエリを記録
        try:
            GameChatLogger.log_debug(
                "hybrid_search",
                "クエリ正規化",
                {
                    "raw_query": str(query)[:500],
                    "preprocessed_query": str(preprocessed_query)[:500],
                },
            )
        except Exception:
            # ログで例外を起こさないため安全に無視
            pass

        # Step 1: LLMによる分類・要約（前処理後のクエリを入力）
        classification = await self._classify_query(preprocessed_query)

        # 挨拶の場合は検索をスキップ
        if self._is_greeting(classification):
            return self._create_greeting_response(classification)

        # Step 2: 検索戦略の決定と最適化
        search_strategy = self.classification_service.determine_search_strategy(classification)
        optimized_limits = self._get_optimized_limits(classification, top_k)

        print(f"検索戦略: DB={search_strategy.use_db_filter}, Vector={search_strategy.use_vector_search}")
        print(f"最適化限界: {optimized_limits}")

        # Step 3: 各検索の実行
        db_titles, vector_titles = await self._execute_searches(
            classification, search_strategy, optimized_limits, preprocessed_query
        )

        print(f"[DEBUG] After _execute_searches: db_titles type={type(db_titles)}, first_item_type={type(db_titles[0]) if db_titles else 'empty'}")
        if db_titles:
            print(f"[DEBUG] db_titles sample: {db_titles[:3]}")

        # Step 4: 結果の品質評価
        search_quality = self._evaluate_search_quality(
            db_titles, vector_titles, classification
        )

        # Step 5: 最適化されたマージ・選択
        db_scores = getattr(self.database_service, "last_scores", {}) if hasattr(self.database_service, "last_scores") else {}
        vector_scores = getattr(self.vector_service, "last_scores", {}) if hasattr(self.vector_service, "last_scores") else {}

        try:
            qtype_value = classification.query_type.value  # Enum -> str
        except Exception:
            qtype_value = str(getattr(classification, "query_type", "semantic")).lower()

        base_threshold_map = {
            "filterable": 0.20,
            "semantic": 0.35,
            "hybrid": 0.30
        }
        quality_threshold = base_threshold_map.get(qtype_value, 0.30)
        conf = getattr(classification, "confidence", 0.0) or 0.0
        if conf >= 0.85:
            quality_threshold = min(0.5, quality_threshold + 0.05)
        elif conf < 0.5:
            quality_threshold = max(0.15, quality_threshold - 0.05)

        merged_titles = self._merge_results_weighted(
            db_titles, vector_titles, db_scores, vector_scores, classification, top_k, search_quality, quality_threshold=quality_threshold
        )

        query_type_str = str(classification.query_type).lower()
        if query_type_str == "filterable" or query_type_str == "querytype.filterable" or classification.query_type == QueryType.FILTERABLE:
            if db_titles and isinstance(db_titles[0], str):
                title_strings = db_titles
            else:
                title_strings = [str(item) for item in db_titles]
            card_details = self.database_service.get_card_details_by_titles(title_strings)
            context = card_details
            if len(card_details) == 0:
                suggestion_message = self._generate_search_suggestion(classification)
                context.append({"name": "検索のご提案", "suggestion": suggestion_message})
            print(f"最終結果: {len(context)}件（FILTERABLE: DB検索結果全件）")
        else:
            details = self.database_service.get_card_details_by_titles(merged_titles)
            context = []
            context.extend(details)
            if len(details) == 0:
                suggestion_message = self._generate_search_suggestion(classification)
                context.append({"name": "検索のご提案", "suggestion": suggestion_message})
            print(f"最終結果: {len(context)}件（詳細: {len(details)}件＋提案: {len(context)-len(details)}件）")
        print(f"検索品質: {search_quality}")

        return {
            "context": context,
            "classification": classification,
            "search_quality": search_quality,
            "search_info": {
                "query_type": classification.query_type.value if hasattr(classification, "query_type") and hasattr(classification.query_type, "value") else str(getattr(classification, "query_type", QueryType.SEMANTIC)),
                "confidence": classification.confidence if hasattr(classification, "confidence") else getattr(classification, "confidence", 0.0),
                "db_results_count": len(db_titles),
                "vector_results_count": len(vector_titles)
            }
        }

    async def _classify_query(self, query: str) -> ClassificationResult:
        """クエリを分類する"""
        classification_request = ClassificationRequest(query=query)
        classification = await self.classification_service.classify_query(classification_request)
        
        print(f"分類結果: {classification.query_type}")
        print(f"要約: {classification.summary}")
        print(f"信頼度: {classification.confidence}")
        
        # ClassificationResultオブジェクトであることを確認
        if not isinstance(classification, ClassificationResult):
            raise ValueError("Classification service returned unexpected type")
        
        return classification

    def _is_greeting(self, classification: ClassificationResult) -> bool:
        """挨拶かどうかを判定"""
        return classification.query_type == QueryType.GREETING

    def _create_greeting_response(self, classification: ClassificationResult) -> Dict[str, Any]:
        """挨拶用のレスポンスを作成"""
        print("=== 挨拶検出: 検索をスキップ ===")
        return {
            "context": [],  # 空のcontext
            "classification": classification,
            "search_quality": {
                "overall_score": 1.0,
                "greeting_detected": True,
                "search_needed": False
            },
            "search_info": {
                "query_type": classification.query_type.value if hasattr(classification.query_type, "value") else str(classification.query_type),
                "confidence": classification.confidence,
                "db_results_count": 0,
                "vector_results_count": 0
            }
        }

    async def _execute_searches(
        self, 
        classification: ClassificationResult, 
        search_strategy: Any, 
        optimized_limits: Dict[str, int],
        query: str
    ) -> tuple[list[str], list[str]]:
        """各検索を実行しカード名リストを返却"""
        db_titles = []
        vector_titles = []
        
        if search_strategy.use_db_filter and classification.filter_keywords:
            print("--- 最適化データベースフィルター検索実行 ---")
            # 正規化: DB向けは強め（OR展開）
            expanded_keywords = self.query_normalizer.expand_keywords_for_db(classification.filter_keywords)
            print(f"[DBフィルタ条件] expanded_keywords: {expanded_keywords}")
            db_limit = optimized_limits["db_limit"]
            db_titles = await self.database_service.filter_search_titles_async(
                expanded_keywords, db_limit
            )
            print(f"DB検索結果: {len(db_titles)}件")
        
        if search_strategy.use_vector_search:
            print("--- 最適化ベクトル意味検索実行 ---")
            # 分類結果に基づく最適化された埋め込み生成
            # Embedding向けは軽めに展開（代表同義語の少数追加）
            expanded_for_embed = self.query_normalizer.expand_text_for_embedding(query)
            print(f"[Embedding] expanded_text: {expanded_for_embed}")
            # DEBUG: 埋め込み用正規化後テキストを記録
            try:
                GameChatLogger.log_debug(
                    "hybrid_search",
                    "埋め込み用テキスト（展開後）",
                    {"expanded_for_embedding": str(expanded_for_embed)[:800]},
                )
            except Exception:
                pass
            query_embedding = await self.embedding_service.get_embedding_from_classification(
                expanded_for_embed, classification
            )
            
            # 最適化されたベクトル検索
            vector_limit = optimized_limits["vector_limit"]
            vector_titles = await self.vector_service.search(
                query_embedding, 
                top_k=vector_limit,
                classification=classification
            )
            print(f"ベクトル検索結果: {len(vector_titles)}件")
        
        return db_titles, vector_titles
    
    def _get_optimized_limits(self, classification: ClassificationResult, top_k: int) -> Dict[str, int]:
        """分類結果に基づいて検索限界を最適化（パフォーマンス改善版）"""
        
        config = settings.VECTOR_SEARCH_CONFIG["search_limits"]
        
        # 型安全なconfig辞書アクセス
        if isinstance(config, dict) and classification.query_type.value in config:
            limits = config[classification.query_type.value]
            if isinstance(limits, dict):
                vector_limit = limits.get("vector", 15)
                db_limit = limits.get("db", 5)
            else:
                vector_limit = 15
                db_limit = 5
        else:
            # デフォルト設定
            vector_limit = 10
            db_limit = 10
        
        # パフォーマンス最適化：全体的な制限を厳しく
        vector_limit = min(vector_limit, 20)  # 最大20に制限
        db_limit = min(db_limit, 15)  # 最大15に制限
        
        # 信頼度による調整（より控えめに）
        if classification.confidence >= 0.8:
            # 高信頼度でも制限を設ける
            vector_limit = min(int(vector_limit * 1.1), 25)
            db_limit = min(int(db_limit * 1.1), 18)
        elif classification.confidence < 0.5:
            # 低信頼度の場合、さらに結果を絞る
            vector_limit = max(5, int(vector_limit * 0.7))
            db_limit = max(3, int(db_limit * 0.7))
        
        # top_kに応じた最終調整
        if top_k <= 10:
            vector_limit = min(vector_limit, 15)
            db_limit = min(db_limit, 10)
        
        return {
            "vector_limit": vector_limit,
            "db_limit": db_limit
        }
    
    def _evaluate_search_quality(
        self, 
        db_titles: list[str], 
        vector_titles: list[str],
        classification: ClassificationResult
    ) -> dict:
        """
        検索結果の品質を評価（カード名リスト用）
        """
        quality = {
            "overall_score": 1.0 if db_titles or vector_titles else 0.0,
            "db_quality": 1.0 if db_titles else 0.0,
            "vector_quality": 1.0 if vector_titles else 0.0,
            "result_count": len(db_titles) + len(vector_titles),
            "has_high_confidence_results": bool(db_titles or vector_titles),
            "avg_score": 1.0 if db_titles or vector_titles else 0.0
        }
        return quality
    
    def _merge_results_optimized(
        self, 
        db_titles: list[str], 
        vector_titles: list[str],
        classification: ClassificationResult,
        top_k: int,
        search_quality: dict
    ) -> list[str]:
        """最適化されたマージロジック（カード名リスト）"""
        
        # 結果がない場合の処理
        if not db_titles and not vector_titles:
            return self._handle_no_results_optimized(classification)

        query_type = getattr(classification, "query_type", None)
        # FILTERABLE: DB優先、足りなければベクトルで補完
        if query_type == "filterable":
            merged = db_titles[:top_k]
            if len(merged) < top_k:
                remaining = top_k - len(merged)
                # ベクトル結果からDBにないものを追加
                supplement = [t for t in vector_titles if t not in merged][:remaining]
                merged.extend(supplement)
            return merged
        # SEMANTIC: ベクトル優先、足りなければDBで補完
        elif query_type == "semantic":
            merged = vector_titles[:top_k]
            if len(merged) < top_k:
                remaining = top_k - len(merged)
                supplement = [t for t in db_titles if t not in merged][:remaining]
                merged.extend(supplement)
            return merged
        # HYBRIDまたはその他: DB→ベクトルの順で重複除去しつつ結合
        else:
            all_titles = db_titles + [t for t in vector_titles if t not in db_titles]
            return all_titles[:top_k]
    
    def _filter_by_quality(
        self, 
        titles: list[str], 
        search_quality: dict, 
        top_k: int
    ) -> list[str]:
        """品質に基づく結果フィルタリング（カード名リスト）"""
        
        return titles[:top_k]
    
    def _handle_no_results_optimized(self, classification: ClassificationResult) -> list[str]:
        """最適化された結果なし時の処理（カード名リスト）"""
        # 空のリストを返す（提案は後で別途処理）
        return []
    
    def _generate_search_suggestion(self, classification: ClassificationResult) -> str:
        """検索提案を生成"""
        
        base_message = "お探しの情報が見つかりませんでした。以下をお試しください：\n\n"
        
        if classification.query_type == QueryType.SEMANTIC:
            suggestions = [
                "• より具体的なカード名やキャラクター名で検索",
                "• 「効果」「HP」「攻撃力」などの具体的な属性を含めた検索",
                "• 「フェアリーのカード」のように条件を明確化"
            ]
        
        elif classification.query_type == QueryType.FILTERABLE:
            suggestions = [
                "• 数値条件を調整（例：HP100以上 → HP80以上）",
                "• 複数条件を単一条件に簡素化",
                "• より一般的なタイプや属性で検索"
            ]
        
        else:  # HYBRID
            suggestions = [
                "• 検索条件を分けて段階的に検索",
                "• より一般的なキーワードから開始",
                "• 具体的な条件と意味的な検索を組み合わせ"
            ]
        
        return base_message + "\n".join(suggestions)
    
    # 下位互換性のためのレガシーメソッド
    def _merge_results(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        classification: ClassificationResult,
        top_k: int
    ) -> List[str]:
        """検索結果をマージして最適な結果を選択（レガシー）"""
        
        # レガシー用途: ContextItem型のままの時のみ利用
        if not db_results and not vector_results:
            return []
        if not db_results:
            return [item.title for item in vector_results[:top_k]]
        if not vector_results:
            return [item.title for item in db_results[:top_k]]
        # HYBRID/その他: DB→ベクトルの順で重複除去しつつ結合
        all_titles = [item.title for item in db_results]
        all_titles += [item.title for item in vector_results if item.title not in all_titles]
        return all_titles[:top_k]
    
