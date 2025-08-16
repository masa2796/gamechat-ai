from typing import List, Optional
from upstash_vector import Index
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationResult, QueryType
from ..core.config import settings
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

class VectorService:
    # 検索ごとにカード名→スコアの辞書を保持
    last_scores: dict = {}
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    """Upstash Vector を使用した類似検索サービス（最適化対応）"""
    
    def __init__(self) -> None:
        upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
        upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        environment = os.getenv("ENVIRONMENT", "development")
        
        # テスト環境では設定不要
        if is_test_mode:
            GameChatLogger.log_info("vector_service", "テストモード: Vector検索は無効化されています")
            self.vector_index = None
            return
        
        # 本番環境では設定が必須
        if not upstash_url or not upstash_token:
            if environment == "production":
                error = Exception(f"Upstash Vector設定が不完全です。URL: {bool(upstash_url)}, Token: {bool(upstash_token)}")
                GameChatLogger.log_error(
                    "vector_service", 
                    "本番環境でUpstash Vector設定が不完全です",
                    error
                )
            else:
                GameChatLogger.log_warning(
                    "vector_service", 
                    "🟡 Upstash Vector設定が不完全です。一部機能が制限されます。"
                )
            self.vector_index = None
        else:
            try:
                self.vector_index = Index(url=upstash_url, token=upstash_token)
                GameChatLogger.log_info("vector_service", "Upstash Vector初期化完了")
            except Exception as e:
                GameChatLogger.log_error("vector_service", f"Upstash Vector初期化失敗: {e}", e)
                self.vector_index = None
    
    @handle_service_exceptions("vector", fallback_return=[])
    async def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 50, 
        namespaces: Optional[List[str]] = None,
        classification: Optional[ClassificationResult] = None,
        min_score: Optional[float] = None
    ) -> List[str]:
        """
        ベクトル検索を実行し、カード名リストを返却
        
        Args:
            query_embedding: クエリの埋め込みベクトル
            top_k: 取得する最大件数
            namespaces: 検索対象のネームスペース
            classification: 分類結果（最適化に使用）
            min_score: 最小スコア閾値
            
        Returns:
            検索結果のリスト
        """
        # 設定がない場合は空の結果を返す
        if self.vector_index is None:
            GameChatLogger.log_warning("vector_service", "Upstash Vector未設定のため空の結果を返します")
            return []
        
        # 分類結果に基づく最適化
        if classification:
            top_k, min_score, namespaces = self._optimize_search_params(
                classification, top_k, min_score, namespaces
            )
        
        # デフォルト値の設定
        if namespaces is None:
            namespaces = self._get_default_namespaces(classification)
        
        if min_score is None:
            config = settings.VECTOR_SEARCH_CONFIG
            min_score_value = config.get("minimum_score")
            if isinstance(min_score_value, (int, float)):
                min_score = float(min_score_value)
            else:
                min_score = 0.5
        
        GameChatLogger.log_info("vector_service", "ベクトル検索を開始", {
            "namespaces": namespaces,
            "top_k": top_k,
            "min_score": min_score,
            "classification_type": classification.query_type if classification else None,
            "confidence": classification.confidence if classification else None
        })
        
        all_titles = []
        scores = {}
        
        for namespace in namespaces:
            try:
                GameChatLogger.log_info("vector_service", f"Namespace {namespace} で検索中")
                results = self.vector_index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    namespace=namespace,
                    include_metadata=True,
                    include_vectors=True
                )
                
                matches = results.matches if hasattr(results, "matches") else results
                
                for match in matches:
                    # scoreの型安全な取得
                    score_value = getattr(match, 'score', None)
                    score = float(score_value) if score_value is not None else 0.0
                    
                    # スコア閾値による除外
                    if min_score is not None and score < min_score:
                        continue
                    meta = getattr(match, 'metadata', None)
                    if meta and hasattr(meta, 'get'):
                        title = meta.get('title', f"{namespace} - 情報")
                    else:
                        title = f"{namespace} - 情報"
                    if title:
                        all_titles.append(title)
                        scores[title] = score
                        
            except Exception as ns_error:
                GameChatLogger.log_error("vector_service", f"Namespace {namespace} での検索エラー", ns_error, {
                    "namespace": namespace
                })
                continue
        
        GameChatLogger.log_success("vector_service", "ベクトル検索完了", {
            "total_results": len(all_titles)
        })
        self.last_scores = scores
        return all_titles[:top_k]
    
    def _optimize_search_params(
        self, 
        classification: ClassificationResult, 
        top_k: int, 
        min_score: Optional[float], 
        namespaces: Optional[List[str]]
    ) -> tuple[int, float, List[str]]:
        """分類結果に基づいて検索パラメータを最適化"""
        
        config = settings.VECTOR_SEARCH_CONFIG
        
        # 分類タイプ別の検索件数調整 (型安全)
        search_limits = config.get("search_limits", {})
        if isinstance(search_limits, dict) and classification.query_type.value in search_limits:
            type_limits = search_limits[classification.query_type.value]
            if isinstance(type_limits, dict):
                vector_limit = type_limits.get("vector", 15)
                top_k = min(top_k, vector_limit)
        
        # 信頼度による類似度閾値調整
        confidence_level = "high" if classification.confidence >= 0.8 else (
            "medium" if classification.confidence >= 0.5 else "low"
        )
        
        if min_score is None:
            # 型安全なconfig辞書アクセス
            similarity_thresholds = config.get("similarity_thresholds", {})
            if isinstance(similarity_thresholds, dict):
                base_threshold = similarity_thresholds.get(classification.query_type.value, 0.7)
            else:
                minimum_score = config.get("minimum_score", 0.5)
                if isinstance(minimum_score, (int, float)):
                    base_threshold = float(minimum_score)
                else:
                    base_threshold = 0.7
                
            confidence_adjustments = config.get("confidence_adjustments", {})
            if isinstance(confidence_adjustments, dict):
                confidence_adjustment = confidence_adjustments.get(confidence_level, 0.7)
            else:
                confidence_adjustment = 0.7
                
            min_score = base_threshold * confidence_adjustment
        
        # ネームスペース最適化
        if namespaces is None:
            namespaces = self._get_optimized_namespaces(classification)
        
        print("[VectorService] パラメータ最適化完了:")
        print(f"  top_k: {top_k}, min_score: {min_score:.3f}")
        print(f"  信頼度レベル: {confidence_level}")
        
        return top_k, min_score, namespaces
    
    def _get_optimized_namespaces(self, classification: ClassificationResult) -> List[str]:
        """データファイルから存在するnamespace一覧を動的に取得"""
        return self._get_all_namespaces()
    
    def _get_default_namespaces(self, classification: Optional[ClassificationResult]) -> List[str]:
        """デフォルトのネームスペースリストを取得（データから動的に取得）"""
        return self._get_all_namespaces()

    def _get_all_namespaces(self) -> List[str]:
        """convert_data.jsonからユニークなnamespace一覧を抽出"""
        import os
        import json
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "convert_data.json")
        namespaces = set()
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        # JSON Lines形式 or 配列形式両対応
                        if line.strip().startswith("["):
                            # 配列形式
                            f.seek(0)
                            items = json.load(f)
                            for item in items:
                                ns = item.get("namespace")
                                if ns:
                                    namespaces.add(ns)
                            break
                        else:
                            # JSON Lines形式
                            item = json.loads(line)
                            ns = item.get("namespace")
                            if ns:
                                namespaces.add(ns)
                    except Exception:
                        continue
        except Exception:
            # ファイルが読めない場合は空リスト
            return []
        return sorted(list(namespaces))
    
    def _handle_no_results(self, classification: Optional[ClassificationResult]) -> List[str]:
        """
        検索結果がない場合のフォールバック（カード名リスト）
        """
        return ["検索結果について"]
    
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
                "より具体的なカード名やカード名で検索してみてください。"
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
    
    async def _search_namespace_async(self, namespace: str, query_embedding: List[float], top_k: int, min_score: Optional[float]) -> List[dict]:
        """
        単一ネームスペースの検索を非同期で実行
        """
        try:
            GameChatLogger.log_info("vector_service", f"Namespace {namespace} で検索中")
            
            # 同期検索を非同期実行
            loop = asyncio.get_event_loop()
            if self.vector_index is not None:
                results = await loop.run_in_executor(
                    None,
                    lambda: self.vector_index.query(  # type: ignore
                        vector=query_embedding,
                        top_k=top_k,
                        namespace=namespace,
                        include_metadata=True,
                        include_vectors=True
                    )
                )
            else:
                results = None
            
            if results is not None:
                matches = results.matches if hasattr(results, "matches") else results
            GameChatLogger.log_info("vector_service", "検索結果取得", {
                "namespace": namespace,
                "results_count": len(matches)
            })
            
            namespace_results = []
            for match in matches:
                # scoreの型安全な取得
                score_value = getattr(match, 'score', None)
                if score_value is not None:
                    score = float(score_value)
                else:
                    score = 0.0
                
                # スコア閾値による除外
                if min_score is not None and score < min_score:
                    continue
                    
                meta = getattr(match, 'metadata', None)
                if meta and hasattr(meta, 'get'):
                    text = meta.get('text')
                    title = meta.get('title', f"{namespace} - 情報")
                else:
                    text = getattr(match, 'text', None)
                    title = f"{namespace} - 情報"
                
                if text:
                    namespace_results.append({
                        "title": title,
                        "text": text,
                        "score": score,
                        "namespace": namespace,
                        "id": getattr(match, 'id', None)
                    })
            
            return namespace_results
            
        except Exception as ns_error:
            GameChatLogger.log_error("vector_service", f"Namespace {namespace} での検索エラー", ns_error, {
                "namespace": namespace
            })
            return []

    async def search_parallel(
        self, 
        query_embedding: List[float], 
        top_k: int = 50, 
        namespaces: Optional[List[str]] = None,
        classification: Optional[ClassificationResult] = None,
        min_score: Optional[float] = None
    ) -> List[str]:
        """
        並列ベクトル検索を実行（パフォーマンス最適化版）
        """
        if not self.vector_index:
            GameChatLogger.log_warning("vector_service", "Vector index が設定されていません")
            return []
        
        # パラメータ最適化（classificationがある場合のみ）
        if classification is not None:
            top_k, min_score, namespaces = self._optimize_search_params(
                classification, top_k, min_score, namespaces
            )
        
        # ネームスペースの確認
        if namespaces is None:
            namespaces = self._get_default_namespaces(classification)
        
        # 並列検索タスクを作成
        tasks = []
        for namespace in namespaces:
            task = self._search_namespace_async(namespace, query_embedding, top_k, min_score)
            tasks.append(task)
        
        # 並列実行（タイムアウト付き）
        try:
            results_list = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=10.0  # 10秒タイムアウト
            )
        except asyncio.TimeoutError:
            GameChatLogger.log_warning("vector_service", "並列検索がタイムアウトしました")
            return []
        
        # 結果をマージ
        all_results = []
        for result in results_list:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                GameChatLogger.log_error("vector_service", "並列検索でエラー", result)
        
        GameChatLogger.log_success("vector_service", "並列ベクトル検索完了", {
            "total_results": len(all_results),
            "namespaces_processed": len(namespaces) if namespaces else 0
        })
        
        if all_results:
            # スコア順でソート
            all_results.sort(key=lambda x: x["score"] or 0, reverse=True)
            
            best_match = max(all_results, key=lambda x: x["score"] or 0)
            GameChatLogger.log_info("vector_service", "最高スコア結果", {
                "score": best_match['score'],
                "namespace": best_match['namespace'],
                "title": best_match['title'][:50]
            })
        
        # カード名リストに変換
        return [result["title"] for result in all_results if "title" in result]
    
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