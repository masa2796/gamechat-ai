from typing import List, Dict, Any
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationRequest, ClassificationResult, QueryType
from ..core.config import settings
from .classification_service import ClassificationService
from .database_service import DatabaseService
from .vector_service import VectorService
from .embedding_service import EmbeddingService

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

        query_type = getattr(classification, "query_type", None)
        # スコア辞書を構築
        db_weight = 0.7
        vector_weight = 0.3
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
        if query_type == "filterable":
            # DBスコアを優先
            sorted_titles = sorted(all_titles, key=lambda t: (t in db_titles, merged_scores[t]), reverse=True)
        elif query_type == "semantic":
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

        # 不足時の補完・提案メッセージ生成
        if len(result_titles) < top_k:
            suggestion_title = self._generate_search_suggestion(classification)
            # ダミーのdictを返す場合はここでtitleを渡すだけ、詳細json化は呼び出し側で対応
            result_titles.append(suggestion_title)

        return result_titles
    """分類に基づく統合検索サービス（最適化対応）"""
    
    def __init__(self) -> None:
        self.classification_service = ClassificationService()
        self.database_service = DatabaseService()
        self.vector_service = VectorService()
        self.embedding_service = EmbeddingService()
    
    async def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        クエリを分類し、最適化された検索戦略でカード名リストを返却
        
        このメソッドはハイブリッド検索システムの中核となる機能で、
        LLMによる分類結果に基づいて最適な検索戦略を選択し、
        データベース検索とベクトル検索を組み合わせて最適な結果を返します。
        
        Args:
            query: 検索クエリ文字列
                例: "HP100以上のカード", "強いカードを教えて"
            top_k: 返却する最大結果数 (デフォルト: 3)
                
        Returns:
            検索結果を含む辞書:
            - classification: 分類結果 (ClassificationResult)
            - search_strategy: 使用した検索戦略 (SearchStrategy)
            - db_results: データベース検索結果 (List[ContextItem])
            - vector_results: ベクトル検索結果 (List[ContextItem])
            - merged_results: マージされた最終結果 (List[ContextItem])
            - search_quality: 検索品質評価 (Dict[str, Any])
            - optimization_applied: 最適化適用フラグ (bool)
            
        Raises:
            ClassificationException: クエリ分類に失敗した場合
            DatabaseException: データベース検索でエラーが発生した場合
            VectorException: ベクトル検索でエラーが発生した場合
            
        Examples:
            >>> service = HybridSearchService()
            >>> result = await service.search("HP100以上のカード", top_k=5)
            >>> print(result["classification"].query_type)
            QueryType.FILTERABLE
            >>> print(len(result["merged_results"]))
            5
            
            >>> # 挨拶の場合は検索をスキップ
            >>> result = await service.search("こんにちは")
            >>> print(result["classification"].query_type)
            QueryType.GREETING
        """
        print("=== 最適化統合検索開始 ===")
        print(f"クエリ: {query}")
        
        # Step 1: LLMによる分類・要約
        classification = await self._classify_query(query)
        
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
            classification, search_strategy, optimized_limits, query
        )
        
        # Step 4: 結果の品質評価
        search_quality = self._evaluate_search_quality(
            db_titles, vector_titles, classification
        )
        
        # Step 5: 最適化されたマージ・選択
        # DB/ベクトルのスコアを取得
        db_scores = getattr(self.database_service, "last_scores", {}) if hasattr(self.database_service, "last_scores") else {}
        vector_scores = getattr(self.vector_service, "last_scores", {}) if hasattr(self.vector_service, "last_scores") else {}
        # 品質スコア閾値（例: 0.3未満は除外）
        quality_threshold = 0.3
        merged_titles = self._merge_results_weighted(
            db_titles, vector_titles, db_scores, vector_scores, classification, top_k, search_quality, quality_threshold=quality_threshold
        )

        # context生成ロジック
        if str(classification.query_type).lower() == "filterable":
            # DB検索結果全件をcontextに返す
            card_details = self.database_service.get_card_details_by_titles(db_titles)
            context = card_details
            print(f"最終結果: {len(context)}件（FILTERABLE: DB検索結果全件）")
        else:
            # それ以外はmerged_titlesで詳細取得＋提案
            details = self.database_service.get_card_details_by_titles(merged_titles)
            found_names = {item.get("name") for item in details}
            context = []
            context.extend(details)
            for title in merged_titles:
                if title not in found_names:
                    context.append({
                        "name": "ご提案",
                        "type": "info",
                        "content": title,
                        "is_suggestion": True
                    })
            print(f"最終結果: {len(context)}件（詳細: {len(details)}件＋提案: {len(context)-len(details)}件）")
        print(f"検索品質: {search_quality}")

        return {
            "answer": "",  # LLM回答は空文字
            "context": context,  # contextにカード詳細jsonリスト
            "db_results": db_titles,
            "classification": classification,
            "search_info": {
                "query_type": classification.query_type if hasattr(classification, "query_type") else getattr(classification, "query_type", "unknown"),
                "confidence": classification.confidence if hasattr(classification, "confidence") else getattr(classification, "confidence", 0.0),
                "db_results_count": len(db_titles),
                "vector_results_count": len(vector_titles)
            },
            "performance": {
                "total_duration": None,  # rag_serviceで計測
                "search_duration": None,
                "llm_duration": 0.0,
                "cache_hit": False
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
            "classification": classification,
            "search_strategy": {
                "use_database": False,
                "use_vector": False,
                "skip_search": True,
                "reason": "greeting_detected"
            },
            "db_results": [],
            "vector_results": [],
            "merged_results": [],
            "search_quality": {
                "overall_score": 1.0,
                "greeting_detected": True,
                "search_needed": False
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
            print(f"[DBフィルタ条件] filter_keywords: {classification.filter_keywords}")
            db_limit = optimized_limits["db_limit"]
            db_titles = await self.database_service.filter_search_titles_async(
                classification.filter_keywords, db_limit
            )
            print(f"DB検索結果: {len(db_titles)}件")
        
        if search_strategy.use_vector_search:
            print("--- 最適化ベクトル意味検索実行 ---")
            # 分類結果に基づく最適化された埋め込み生成
            query_embedding = await self.embedding_service.get_embedding_from_classification(
                query, classification
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
        
        return ["検索のご提案"]
    
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
    
