from typing import List, Dict, Any
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationRequest, ClassificationResult, QueryType
from ..core.config import settings
from .classification_service import ClassificationService
from .database_service import DatabaseService
from .vector_service import VectorService
from .embedding_service import EmbeddingService

class HybridSearchService:
    """分類に基づく統合検索サービス（最適化対応）"""
    
    def __init__(self) -> None:
        self.classification_service = ClassificationService()
        self.database_service = DatabaseService()
        self.vector_service = VectorService()
        self.embedding_service = EmbeddingService()
    
    async def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        クエリを分類し、最適化された検索戦略で結果を取得
        
        Returns:
            Dict containing:
            - classification: 分類結果
            - search_strategy: 使用した検索戦略
            - db_results: データベース検索結果 (if applicable)
            - vector_results: ベクトル検索結果 (if applicable)
            - merged_results: マージされた最終結果
            - search_quality: 検索品質評価
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
        db_results, vector_results = await self._execute_searches(
            classification, search_strategy, optimized_limits, query
        )
        
        # Step 4: 結果の品質評価
        search_quality = self._evaluate_search_quality(
            db_results, vector_results, classification
        )
        
        # Step 5: 最適化されたマージ・選択
        merged_results = self._merge_results_optimized(
            db_results, vector_results, classification, top_k, search_quality
        )
        
        print(f"最終結果: {len(merged_results)}件")
        print(f"検索品質: {search_quality}")
        
        return {
            "classification": classification,
            "search_strategy": search_strategy,
            "db_results": db_results,
            "vector_results": vector_results,
            "merged_results": merged_results,
            "search_quality": search_quality,
            "optimization_applied": True
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
    ) -> tuple[List[ContextItem], List[ContextItem]]:
        """各検索を実行する"""
        db_results = []
        vector_results = []
        
        if search_strategy.use_db_filter and classification.filter_keywords:
            print("--- 最適化データベースフィルター検索実行 ---")
            db_limit = optimized_limits["db_limit"]
            db_results = await self.database_service.filter_search(
                classification.filter_keywords, db_limit
            )
            print(f"DB検索結果: {len(db_results)}件")
        
        if search_strategy.use_vector_search:
            print("--- 最適化ベクトル意味検索実行 ---")
            # 分類結果に基づく最適化された埋め込み生成
            query_embedding = await self.embedding_service.get_embedding_from_classification(
                query, classification
            )
            
            # 最適化されたベクトル検索
            vector_limit = optimized_limits["vector_limit"]
            vector_results = await self.vector_service.search(
                query_embedding, 
                top_k=vector_limit,
                classification=classification
            )
            print(f"ベクトル検索結果: {len(vector_results)}件")
        
        return db_results, vector_results
    
    def _get_optimized_limits(self, classification: ClassificationResult, top_k: int) -> Dict[str, int]:
        """分類結果に基づいて検索限界を最適化"""
        
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
        
        # 信頼度による調整
        if classification.confidence >= 0.8:
            # 高信頼度の場合、より多くの結果を取得
            vector_limit = int(vector_limit * 1.2)
            db_limit = int(db_limit * 1.2)
        elif classification.confidence < 0.5:
            # 低信頼度の場合、結果を絞る
            vector_limit = max(5, int(vector_limit * 0.8))
            db_limit = max(5, int(db_limit * 0.8))
        
        return {
            "vector_limit": vector_limit,
            "db_limit": db_limit
        }
    
    def _evaluate_search_quality(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """検索結果の品質を評価"""
        
        quality = {
            "overall_score": 0.0,
            "db_quality": 0.0,
            "vector_quality": 0.0,
            "result_count": len(db_results) + len(vector_results),
            "has_high_confidence_results": False,
            "avg_score": 0.0
        }
        
        all_scores = []
        
        # DB結果の品質評価
        if db_results:
            db_scores = [result.score for result in db_results if result.score > 0]
            if db_scores:
                quality["db_quality"] = sum(db_scores) / len(db_scores)
                all_scores.extend(db_scores)
        
        # ベクトル結果の品質評価
        if vector_results:
            vector_scores = [result.score for result in vector_results if result.score > 0]
            if vector_scores:
                quality["vector_quality"] = sum(vector_scores) / len(vector_scores)
                all_scores.extend(vector_scores)
        
        # 全体評価
        if all_scores:
            quality["avg_score"] = sum(all_scores) / len(all_scores)
            quality["has_high_confidence_results"] = any(score > 0.8 for score in all_scores)
            
            # 総合スコア計算（分類信頼度も考慮）
            base_score = quality["avg_score"]
            confidence_bonus = classification.confidence * 0.1
            result_count_factor = min(1.0, len(all_scores) / 5)  # 5件以上で満点
            
            quality["overall_score"] = (base_score + confidence_bonus) * result_count_factor
        
        return quality
    
    def _merge_results_optimized(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        classification: ClassificationResult,
        top_k: int,
        search_quality: Dict[str, Any]
    ) -> List[ContextItem]:
        """最適化されたマージロジック"""
        
        # 結果がない場合の処理
        if not db_results and not vector_results:
            return self._handle_no_results_optimized(classification)
        
        # 単一ソースの場合
        if not db_results:
            return self._filter_by_quality(vector_results, search_quality, top_k)
        
        if not vector_results:
            return self._filter_by_quality(db_results, search_quality, top_k)
        
        # 品質に基づくマージ戦略の調整
        if search_quality["overall_score"] < 0.5:
            print("🔍 低品質検出: より多くの結果を含めます")
            # 低品質の場合、より多くの結果を含める
            return self._merge_results_inclusive(db_results, vector_results, classification, top_k)
        
        # 通常のマージ処理
        return self._merge_results_standard(db_results, vector_results, classification, top_k)
    
    def _merge_results_standard(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        classification: ClassificationResult,
        top_k: int
    ) -> List[ContextItem]:
        """標準的なマージ処理"""
        
        if classification.query_type == QueryType.HYBRID:
            # ハイブリッドの場合は重み付けマージ
            return self._weighted_merge_optimized(db_results, vector_results, top_k)
        elif classification.query_type == QueryType.FILTERABLE:
            # フィルター優先の場合はDBの結果を優先し、不足分をベクトルで補完
            merged = db_results[:top_k]
            if len(merged) < top_k:
                remaining = top_k - len(merged)
                merged.extend(vector_results[:remaining])
            return merged
        else:  # SEMANTIC
            # 意味検索優先の場合はベクトルの結果を優先し、不足分をDBで補完
            merged = vector_results[:top_k]
            if len(merged) < top_k:
                remaining = top_k - len(merged)
                merged.extend(db_results[:remaining])
            return merged
    
    def _merge_results_inclusive(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        classification: ClassificationResult,
        top_k: int
    ) -> List[ContextItem]:
        """包括的マージ（低品質時）"""
        
        all_results = []
        
        # すべての結果を含めて、スコアで並び替え
        all_results.extend(db_results)
        all_results.extend(vector_results)
        
        # 重複除去（同一タイトルをチェック）
        seen_titles = set()
        unique_results = []
        
        for result in all_results:
            if result.title not in seen_titles:
                seen_titles.add(result.title)
                unique_results.append(result)
        
        # スコアで並び替え
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        return unique_results[:top_k]
    
    def _weighted_merge_optimized(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        top_k: int
    ) -> List[ContextItem]:
        """最適化された重み付きマージ"""
        
        config_merge = settings.VECTOR_SEARCH_CONFIG.get("merge_weights", {})
        if isinstance(config_merge, dict):
            db_weight = config_merge.get("db_weight", 0.4)
            vector_weight = config_merge.get("vector_weight", 0.6)
        else:
            db_weight = 0.4
            vector_weight = 0.6
        
        all_results = []
        
        # DBの結果に重み付け
        for item in db_results:
            weighted_item = ContextItem(
                title=f"[DB] {item.title}",
                text=item.text,
                score=item.score * db_weight
            )
            all_results.append(weighted_item)
        
        # ベクトルの結果に重み付け
        for item in vector_results:
            weighted_item = ContextItem(
                title=f"[Vec] {item.title}",
                text=item.text,
                score=item.score * vector_weight
            )
            all_results.append(weighted_item)
        
        # スコアでソートして上位を返す
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]
    
    def _filter_by_quality(
        self, 
        results: List[ContextItem], 
        search_quality: Dict[str, Any], 
        top_k: int
    ) -> List[ContextItem]:
        """品質に基づく結果フィルタリング"""
        
        config_min_score = settings.VECTOR_SEARCH_CONFIG.get("minimum_score", 0.5)
        if isinstance(config_min_score, (int, float)):
            min_score = float(config_min_score)
        else:
            min_score = 0.5
        
        # 最小スコア以上の結果のみ保持
        filtered_results = [
            result for result in results 
            if result.score >= min_score
        ]
        
        if not filtered_results and results:
            # すべてが最小スコア未満の場合、上位1件は保持
            print("⚠️ 全結果が最小スコア未満のため、上位1件を保持")
            return [results[0]]
        
        return filtered_results[:top_k]
    
    def _handle_no_results_optimized(self, classification: ClassificationResult) -> List[ContextItem]:
        """最適化された結果なし時の処理"""
        
        print("🔍 検索結果最適化: 該当なし時の処理")
        
        # 分類に基づく有用な提案を生成
        suggestion_text = self._generate_search_suggestion(classification)
        
        return [
            ContextItem(
                title="検索のご提案",
                text=suggestion_text,
                score=0.1
            )
        ]
    
    def _generate_search_suggestion(self, classification: ClassificationResult) -> str:
        """検索提案を生成"""
        
        base_message = "お探しの情報が見つかりませんでした。以下をお試しください：\n\n"
        
        if classification.query_type == QueryType.SEMANTIC:
            suggestions = [
                "• より具体的なポケモン名やカード名で検索",
                "• 「技」「HP」「タイプ」などの具体的な属性を含めた検索",
                "• 「強い草タイプのポケモン」のように条件を明確化"
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
    ) -> List[ContextItem]:
        """検索結果をマージして最適な結果を選択（レガシー）"""
        
        if not db_results and not vector_results:
            return []
        
        if not db_results:
            return vector_results[:top_k]
        
        if not vector_results:
            return db_results[:top_k]
        
        # 両方の結果がある場合のマージ戦略
        if classification.query_type == "hybrid":
            # ハイブリッドの場合は重み付けマージ
            return self._weighted_merge(db_results, vector_results, top_k)
        elif classification.query_type == "filterable":
            # フィルター優先の場合はDBの結果を優先し、不足分をベクトルで補完
            merged = db_results[:top_k]
            if len(merged) < top_k:
                remaining = top_k - len(merged)
                merged.extend(vector_results[:remaining])
            return merged
        else:  # semantic
            # 意味検索優先の場合はベクトルの結果を優先し、不足分をDBで補完
            merged = vector_results[:top_k]
            if len(merged) < top_k:
                remaining = top_k - len(merged)
                merged.extend(db_results[:remaining])
            return merged
    
    def _weighted_merge(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        top_k: int
    ) -> List[ContextItem]:
        """重み付きマージ - スコアを正規化して統合（レガシー）"""
        all_results = []
        
        # DBの結果に重み付け（0.4）
        for item in db_results:
            weighted_item = ContextItem(
                title=f"[DB] {item.title}",
                text=item.text,
                score=item.score * 0.4
            )
            all_results.append(weighted_item)
        
        # ベクトルの結果に重み付け（0.6）
        for item in vector_results:
            weighted_item = ContextItem(
                title=f"[Vec] {item.title}",
                text=item.text,
                score=item.score * 0.6
            )
            all_results.append(weighted_item)
        
        # スコアでソートして上位を返す
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]
