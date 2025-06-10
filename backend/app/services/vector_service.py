from typing import List, Optional
from upstash_vector import Index
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationResult, QueryType
from ..core.config import settings
import os
from dotenv import load_dotenv
load_dotenv()

class VectorService:
    def __init__(self):
        upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
        upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        self.vector_index = Index(url=upstash_url, token=upstash_token)
    
    async def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 50, 
        namespaces: List[str] = None,
        classification: Optional[ClassificationResult] = None,
        min_score: Optional[float] = None
    ) -> List[ContextItem]:
        """
        ベクトル検索を実行（分類結果に基づく最適化対応）
        
        Args:
            query_embedding: クエリの埋め込みベクトル
            top_k: 取得する最大件数
            namespaces: 検索対象のネームスペース
            classification: 分類結果（最適化に使用）
            min_score: 最小スコア閾値
            
        Returns:
            検索結果のリスト
        """
        try:
            # 分類結果に基づく最適化
            if classification:
                top_k, min_score, namespaces = self._optimize_search_params(
                    classification, top_k, min_score, namespaces
                )
            
            # デフォルト値の設定
            if namespaces is None:
                namespaces = self._get_default_namespaces(classification)
            
            if min_score is None:
                min_score = settings.VECTOR_SEARCH_CONFIG["minimum_score"]
            
            all_results = []
            print("=== 最適化されたベクトル検索開始 ===")
            print(f"検索対象ネームスペース: {namespaces}")
            print(f"最大取得件数: {top_k}")
            print(f"最小スコア閾値: {min_score}")
            print(f"分類タイプ: {classification.query_type if classification else 'N/A'}")
            print(f"信頼度: {classification.confidence if classification else 'N/A'}")
            
            for namespace in namespaces:
                try:
                    print(f"\n--- Namespace: {namespace} での検索中 ---")
                    results = self.vector_index.query(
                        vector=query_embedding,
                        top_k=top_k,
                        namespace=namespace,
                        include_metadata=True,
                        include_vectors=True
                    )
                    
                    matches = results.matches if hasattr(results, "matches") else results
                    print(f"  検索結果件数: {len(matches)}")
                    
                    for i, match in enumerate(matches):
                        score = getattr(match, 'score', None) or float(match.score) if hasattr(match, 'score') else 0
                        
                        # スコア閾値による除外
                        if score < min_score:
                            print(f"    [{i+1}] スコア不足により除外: {score:.4f} < {min_score}")
                            continue
                            
                        meta = getattr(match, 'metadata', None)
                        text = meta.get('text') if meta else getattr(match, 'text', None)
                        title = meta.get('title', f"{namespace} - 情報") if meta else f"{namespace} - 情報"
                        
                        print(f"    [{i+1}] ID: {getattr(match, 'id', 'N/A')}")
                        print(f"        Score: {score:.4f}")
                        print(f"        Title: {title}")
                        print(f"        Text: {text[:100] if text else 'N/A'}{'...' if text and len(text) > 100 else ''}")
                        
                        if text:
                            all_results.append({
                                "title": title,
                                "text": text,
                                "score": score,
                                "namespace": namespace,
                                "id": getattr(match, 'id', None)
                            })
                            
                except Exception as ns_error:
                    print(f"  ❌ Namespace {namespace} での検索エラー: {ns_error}")
                    continue
            
            print("\n=== 全体検索結果サマリー ===")
            print(f"閾値通過件数: {len(all_results)}")
            
            if all_results:
                all_results.sort(key=lambda x: x["score"] or 0, reverse=True)
                
                print(f"トップ{min(top_k, len(all_results))}件:")
                for i, result in enumerate(all_results[:top_k]):
                    print(f"  {i+1}. [{result['namespace']}] {result['title']} (Score: {result['score']:.4f})")                
                best_match = max(all_results, key=lambda x: x["score"] or 0)
                print(f"\n最高スコア: {best_match['score']:.4f} (namespace: {best_match['namespace']})")
                
                return [
                    ContextItem(
                        title=result["title"],
                        text=result["text"],
                        score=result["score"]
                    )
                    for result in all_results[:top_k]
                ]
            else:
                print("❌ 閾値を通過した検索結果なし")
                # フォールバック処理
                return self._handle_no_results(classification)
            
        except Exception as e:
            print(f"❌ ベクトル検索エラー: {e}")
            return self._handle_search_error(classification, e)
    
    def _optimize_search_params(
        self, 
        classification: ClassificationResult, 
        top_k: int, 
        min_score: Optional[float], 
        namespaces: Optional[List[str]]
    ) -> tuple[int, float, List[str]]:
        """分類結果に基づいて検索パラメータを最適化"""
        
        config = settings.VECTOR_SEARCH_CONFIG
        
        # 分類タイプ別の検索件数調整
        if classification.query_type in config["search_limits"]:
            vector_limit = config["search_limits"][classification.query_type]["vector"]
            top_k = min(top_k, vector_limit)
        
        # 信頼度による類似度閾値調整
        confidence_level = "high" if classification.confidence >= 0.8 else (
            "medium" if classification.confidence >= 0.5 else "low"
        )
        
        if min_score is None:
            base_threshold = config["similarity_thresholds"].get(
                classification.query_type, config["minimum_score"]
            )
            confidence_adjustment = config["confidence_adjustments"][confidence_level]
            min_score = base_threshold * confidence_adjustment
        
        # ネームスペース最適化
        if namespaces is None:
            namespaces = self._get_optimized_namespaces(classification)
        
        print(f"[VectorService] パラメータ最適化完了:")
        print(f"  top_k: {top_k}, min_score: {min_score:.3f}")
        print(f"  信頼度レベル: {confidence_level}")
        
        return top_k, min_score, namespaces
    
    def _get_optimized_namespaces(self, classification: ClassificationResult) -> List[str]:
        """分類結果に基づいてネームスペースを最適化"""
        
        # 分類タイプ別のネームスペース優先順位
        if classification.query_type == QueryType.SEMANTIC:
            # セマンティック検索では要約や説明を重視
            return ["summary", "flavor", "attacks", "evolves", "type", "category", 
                   "hp", "weakness", "height", "weight", "set-info", "releaseDate", "rarity"]
        
        elif classification.query_type == QueryType.FILTERABLE:
            # フィルタ可能検索では具体的な属性を重視
            return ["hp", "type", "weakness", "category", "rarity", "attacks", 
                   "height", "weight", "set-info", "releaseDate", "summary", "flavor", "evolves"]
        
        else:  # HYBRID
            # ハイブリッドではバランス良く
            return ["summary", "hp", "type", "attacks", "flavor", "weakness", "category", 
                   "evolves", "height", "weight", "set-info", "releaseDate", "rarity"]
    
    def _get_default_namespaces(self, classification: Optional[ClassificationResult]) -> List[str]:
        """デフォルトのネームスペースリストを取得"""
        if classification:
            return self._get_optimized_namespaces(classification)
        
        return [
            "summary", "flavor", "attacks", "height", "weight", "evolves",
            "hp", "weakness", "type", "set-info", "releaseDate", "category", "rarity"
        ]
    
    def _handle_no_results(self, classification: Optional[ClassificationResult]) -> List[ContextItem]:
        """検索結果がない場合のフォールバック処理"""
        
        config = settings.VECTOR_SEARCH_CONFIG
        
        if not config["fallback_enabled"]:
            return []
        
        print("📝 フォールバック: 該当する情報が見つかりませんでした")
        
        # ユーザーに有用な情報を提供
        fallback_message = self._generate_fallback_message(classification)
        
        return [
            ContextItem(
                title="検索結果について",
                text=fallback_message,
                score=0.1  # 低スコアでフォールバックと識別
            )
        ]
    
    def _handle_search_error(self, classification: Optional[ClassificationResult], error: Exception) -> List[ContextItem]:
        """検索エラー時の処理"""
        
        print(f"🚨 検索エラー処理: {error}")
        
        error_message = (
            "申し訳ございませんが、検索中にエラーが発生しました。"
            "しばらく時間をおいて再度お試しください。"
        )
        
        return [
            ContextItem(
                title="エラー",
                text=error_message,
                score=0.0
            )
        ]
    
    def _generate_fallback_message(self, classification: Optional[ClassificationResult]) -> str:
        """フォールバック用のメッセージを生成"""
        
        if not classification:
            return (
                "お探しの情報が見つかりませんでした。"
                "別のキーワードで検索してみてください。"
            )
        
        if classification.query_type == QueryType.SEMANTIC:
            return (
                f"「{classification.summary or '検索内容'}」に関する情報が見つかりませんでした。"
                "より具体的なポケモン名やカード名で検索してみてください。"
            )
        
        elif classification.query_type == QueryType.FILTERABLE:
            keywords = ", ".join(classification.filter_keywords) if classification.filter_keywords else "指定の条件"
            return (
                f"「{keywords}」の条件に一致する情報が見つかりませんでした。"
                "検索条件を変更して再度お試しください。"
            )
        
        else:  # HYBRID
            return (
                "お探しの条件に一致する情報が見つかりませんでした。"
                "検索キーワードや条件を変更して再度お試しください。"
            )