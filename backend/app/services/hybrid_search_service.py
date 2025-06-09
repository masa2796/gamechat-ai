from typing import List, Dict, Any
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationRequest, ClassificationResult
from .classification_service import ClassificationService
from .database_service import DatabaseService
from .vector_service import VectorService
from .embedding_service import EmbeddingService

class HybridSearchService:
    """分類に基づく統合検索サービス"""
    
    def __init__(self):
        self.classification_service = ClassificationService()
        self.database_service = DatabaseService()
        self.vector_service = VectorService()
        self.embedding_service = EmbeddingService()
    
    async def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        クエリを分類し、適切な検索戦略で結果を取得
        
        Returns:
            Dict containing:
            - classification: 分類結果
            - search_strategy: 使用した検索戦略
            - db_results: データベース検索結果 (if applicable)
            - vector_results: ベクトル検索結果 (if applicable)
            - merged_results: マージされた最終結果
        """
        print("=== 統合検索開始 ===")
        print(f"クエリ: {query}")
        
        # Step 1: LLMによる分類・要約
        classification_request = ClassificationRequest(query=query)
        classification = await self.classification_service.classify_query(classification_request)
        
        print(f"分類結果: {classification.query_type}")
        print(f"要約: {classification.summary}")
        print(f"信頼度: {classification.confidence}")
        
        # Step 2: 検索戦略の決定
        search_strategy = self.classification_service.determine_search_strategy(classification)
        
        print(f"検索戦略: DB={search_strategy.use_db_filter}, Vector={search_strategy.use_vector_search}")
        
        # Step 3: 各検索の実行
        db_results = []
        vector_results = []
        
        if search_strategy.use_db_filter and classification.filter_keywords:
            print("--- データベースフィルター検索実行 ---")
            # DB検索では全ての該当結果を取得（50件まで）
            db_results = await self.database_service.filter_search(
                classification.filter_keywords, 50
            )
            print(f"DB検索結果: {len(db_results)}件")
        
        if search_strategy.use_vector_search:
            print("--- ベクトル意味検索実行 ---")
            # 分類結果に基づく最適化された埋め込み生成
            query_embedding = await self.embedding_service.get_embedding_from_classification(
                query, classification
            )
            # ベクトル検索でも多めに結果を取得
            vector_results = await self.vector_service.search(query_embedding, 10)
            print(f"ベクトル検索結果: {len(vector_results)}件")
        
        # Step 4: 結果のマージ・選択
        merged_results = self._merge_results(
            db_results, vector_results, classification, top_k
        )
        
        print(f"最終結果: {len(merged_results)}件")
        
        return {
            "classification": classification,
            "search_strategy": search_strategy,
            "db_results": db_results,
            "vector_results": vector_results,
            "merged_results": merged_results
        }
    
    def _merge_results(
        self, 
        db_results: List[ContextItem], 
        vector_results: List[ContextItem],
        classification: ClassificationResult,
        top_k: int
    ) -> List[ContextItem]:
        """検索結果をマージして最適な結果を選択"""
        
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
        """重み付きマージ - スコアを正規化して統合"""
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
