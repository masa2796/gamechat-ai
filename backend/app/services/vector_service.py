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
        # DEBUG: 検索パラメータを詳細に出力
        try:
            GameChatLogger.log_debug(
                "vector_service",
                "検索パラメータ（初期）",
                {
                    "namespaces": (namespaces or [])[:20],
                    "threshold": float(min_score) if isinstance(min_score, (int, float)) else None,
                    "top_k": int(top_k),
                },
            )
        except Exception:
            pass
        # タイトル重複時は最大スコアで集約
        scores: dict[str, float] = {}

        def _query_namespaces(q_namespaces: List[str], threshold: Optional[float], inner_top_k: int) -> None:
            for namespace in q_namespaces:
                try:
                    GameChatLogger.log_info("vector_service", f"Namespace {namespace} で検索中")
                    results = self.vector_index.query(  # type: ignore
                        vector=query_embedding,
                        top_k=inner_top_k,
                        namespace=namespace,
                        include_metadata=True,
                        include_vectors=True
                    )
                    matches = results.matches if hasattr(results, "matches") else results
                    for match in matches:
                        score_value = getattr(match, 'score', None)
                        score = float(score_value) if score_value is not None else 0.0
                        if threshold is not None and score < threshold:
                            continue
                        meta = getattr(match, 'metadata', None)
                        if meta and hasattr(meta, 'get'):
                            title = meta.get('title', f"{namespace} - 情報")
                        else:
                            title = f"{namespace} - 情報"
                        if title:
                            prev = scores.get(title)
                            if prev is None or score > prev:
                                scores[title] = score
                except Exception as ns_error:
                    GameChatLogger.log_error("vector_service", f"Namespace {namespace} での検索エラー", ns_error, {
                        "namespace": namespace
                    })
                    continue

        # 段階的フォールバック戦略
        try:
            all_ns = self._get_all_namespaces()
        except Exception:
            all_ns = namespaces or []
        effect_ns = [ns for ns in (all_ns or []) if ns.startswith("effect_")]
        combined_first = ["effect_combined"] if "effect_combined" in effect_ns else []
        effect_others = [ns for ns in effect_ns if ns != "effect_combined"]
        effect_pref = (combined_first + effect_others) if effect_ns else (namespaces or all_ns)

        # フォールバック候補の段階
        from typing import Dict as _Dict
        steps: List[_Dict[str, object]] = [
            {"namespaces": namespaces or effect_pref, "min_score": float(min_score or 0.5), "top_k": int(top_k)},
            {"namespaces": list(dict.fromkeys((combined_first or []) + (namespaces or effect_pref))), "min_score": max(0.0, float(min_score or 0.5) - 0.1), "top_k": int(min(max(top_k, 20), 50))},
        ]
        # 追加: qa系も含める段階
        qa_aug = list(dict.fromkeys((effect_pref or []) + [ns for ns in (all_ns or []) if ns in ("qa_question", "qa_answer")]))
        steps.append({"namespaces": qa_aug or (namespaces or all_ns), "min_score": max(0.0, float(min_score or 0.5) - 0.2), "top_k": 50})
        # 最終段階: 全namespace + 最低しきい値0.0
        steps.append({"namespaces": all_ns or (namespaces or []), "min_score": 0.0, "top_k": 50})

        for i, step in enumerate(steps, start=1):
            if scores:
                break
            step_namespaces = step["namespaces"]  # type: ignore
            step_min_score = step["min_score"]  # type: ignore
            step_top_k = step["top_k"]  # type: ignore
            ns_list = step_namespaces if isinstance(step_namespaces, list) else (namespaces or all_ns)
            GameChatLogger.log_info("vector_service", f"フォールバック段階 {i} 実行", {
                "min_score": step_min_score,
                "namespaces_sample": (ns_list or [])[:10],
                "inner_top_k": step_top_k
            })
            # DEBUG: 各段階のパラメータ詳細
            try:
                GameChatLogger.log_debug(
                    "vector_service",
                    "フォールバック段階パラメータ",
                    {
                        "stage": i,
                        "namespaces": ns_list[:20] if isinstance(ns_list, list) else [],
                        "threshold": float(step_min_score) if isinstance(step_min_score, (int, float)) else None,
                        "top_k": int(step_top_k),
                    },
                )
            except Exception:
                pass
            _query_namespaces(ns_list, step_min_score if isinstance(step_min_score, (int, float)) else None, int(step_top_k))

        # スコアで降順ソートし、カード名を返却
        sorted_titles = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        # 上位5件をDEBUGログ（スコア可視化）
        top5 = [{"title": t, "score": s} for t, s in sorted_titles[:5]]
        GameChatLogger.log_success("vector_service", "ベクトル検索完了", {
            "total_results": len(sorted_titles),
            "top5": top5
        })
        # DEBUG: 上位5件のスコアを明示的に出力
        try:
            GameChatLogger.log_debug(
                "vector_service",
                "上位スコア（top5）",
                {"top5": top5},
            )
        except Exception:
            pass
        self.last_scores = scores
        return [title for title, _ in sorted_titles[:top_k]]
    
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
        all_namespaces = self._get_all_namespaces()
        return self._filter_namespaces_by_query_type(all_namespaces, classification.query_type)
    
    def _get_default_namespaces(self, classification: Optional[ClassificationResult]) -> List[str]:
        """デフォルトのネームスペースリストを取得（データから動的に取得）"""
        all_namespaces = self._get_all_namespaces()
        # 分類が無い場合は従来どおり全て。分類があれば種別に応じてフィルタ。
        if classification is None:
            return all_namespaces
        return self._filter_namespaces_by_query_type(all_namespaces, classification.query_type)

    def _get_all_namespaces(self) -> List[str]:
        """convert_data.jsonからユニークなnamespace一覧を抽出"""
        import os
        import json

        # NOTE: 既存実装は backend/data/convert_data.json を参照していたが、
        # 実際のファイルはリポジトリルート直下 data/convert_data.json に存在する。
        # そのため path が 1階層足りず namespace が常に空 -> ベクトル検索 0件 という不具合が発生。
        # 以下では複数候補を順に探索し、最初に見つかったファイルを採用する。

        service_dir = os.path.dirname(__file__)
        candidates: List[str] = []
        # 旧（誤りだった）パス: backend/data/convert_data.json
        candidates.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(service_dir))), "data", "convert_data.json"))  # legacy (残して後方互換)
        # 想定する正しいルート: プロジェクトルート/data/convert_data.json （services から4階層上）
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(service_dir))))
        candidates.append(os.path.join(project_root, "data", "convert_data.json"))
        # さらに環境変数 DATA_DIR があれば優先
        data_dir_env = os.getenv("DATA_DIR")
        if data_dir_env:
            candidates.insert(0, os.path.join(data_dir_env, "convert_data.json"))

        data_path = None
        for path in candidates:
            if os.path.exists(path):
                data_path = path
                break

        if data_path is None:
            GameChatLogger.log_warning(
                "vector_service",
                "convert_data.json が見つからず namespace を空集合として扱います",
                {"tried": candidates[:3]}
            )
            return []

        namespaces = set()
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                first_chunk = f.read(2048)
                f.seek(0)
                if first_chunk.lstrip().startswith("["):
                    # 配列形式
                    try:
                        items = json.load(f)
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    ns = item.get("namespace")
                                    if ns:
                                        namespaces.add(ns)
                    except Exception as e:  # フォールバックとして行単位再読込
                        GameChatLogger.log_warning("vector_service", "convert_data.json の配列読込に失敗。行単位フォールバック", {"error": str(e)})
                        f.seek(0)
                        for line in f:
                            try:
                                obj = json.loads(line)
                                if isinstance(obj, dict):
                                    ns = obj.get("namespace")
                                    if ns:
                                        namespaces.add(ns)
                            except Exception:
                                continue
                else:
                    # JSON Lines 形式
                    for line in f:
                        try:
                            obj = json.loads(line)
                            if isinstance(obj, dict):
                                ns = obj.get("namespace")
                                if ns:
                                    namespaces.add(ns)
                        except Exception:
                            continue
        except Exception as e:
            GameChatLogger.log_error("vector_service", "convert_data.json 読込でエラー", e, {"path": data_path})
            return []

        ns_list = sorted(list(namespaces))
        if not ns_list:
            GameChatLogger.log_warning("vector_service", "convert_data.json に namespace が検出されませんでした", {"path": data_path})
        else:
            try:
                GameChatLogger.log_debug("vector_service", "namespace 読込成功", {"count": len(ns_list), "sample": ns_list[:8]})
            except Exception:
                pass
        return ns_list

    def _filter_namespaces_by_query_type(self, all_namespaces: List[str], query_type: QueryType) -> List[str]:
        """クエリ種別に応じたnamespaceフィルタ
        - SEMANTIC/HYBRID: effect_* と effect_combined を優先/限定
        - その他(FILTERABLE/GREETING): 既定（全namespace）
        フォールバック: 該当がない場合は全namespaceを返す
        """
        try:
            if query_type in (QueryType.SEMANTIC, QueryType.HYBRID):
                effect_namespaces = [ns for ns in all_namespaces if ns.startswith("effect_")]
                # effect_combined が存在する場合は先頭に配置
                combined = [ns for ns in effect_namespaces if ns == "effect_combined"]
                effect_others = [ns for ns in effect_namespaces if ns != "effect_combined"]
                filtered = combined + sorted(effect_others)
                if filtered:
                    GameChatLogger.log_info("vector_service", "クエリ種別に応じてeffect系に限定", {
                        "query_type": query_type.value,
                        "selected_namespaces": filtered[:10],
                        "total": len(filtered)
                    })
                    return filtered
                # 該当が無い場合はフォールバック（全namespace）
                GameChatLogger.log_warning("vector_service", "effect系namespaceが見つからず全namespaceを使用します")
                return all_namespaces
            # FILTERABLE/GREETING 等は既定のまま
            return all_namespaces
        except Exception as e:
            GameChatLogger.log_error("vector_service", "namespaceフィルタ中にエラー", e)
            return all_namespaces
    
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
        # DEBUG: 並列検索の初期パラメータ
        try:
            GameChatLogger.log_debug(
                "vector_service",
                "検索パラメータ（並列）",
                {
                    "namespaces": (namespaces or [])[:20],
                    "threshold": float(min_score) if isinstance(min_score, (int, float)) else None,
                    "top_k": int(top_k),
                },
            )
        except Exception:
            pass
        
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
        
        # 結果をマージ（タイトル単位で最大スコア集約）
        score_by_title: dict[str, float] = {}
        for result in results_list:
            if isinstance(result, list):
                for r in result:
                    title = r.get("title")
                    score = float(r.get("score") or 0.0)
                    if title:
                        prev = score_by_title.get(title)
                        if prev is None or score > prev:
                            score_by_title[title] = score
            elif isinstance(result, Exception):
                GameChatLogger.log_error("vector_service", "並列検索でエラー", result)
        
        GameChatLogger.log_success("vector_service", "並列ベクトル検索完了", {
            "total_results": len(score_by_title),
            "namespaces_processed": len(namespaces) if namespaces else 0
        })
        
        if score_by_title:
            # スコア順でソート
            sorted_items = sorted(score_by_title.items(), key=lambda kv: kv[1], reverse=True)
            best_title, best_score = sorted_items[0]
            GameChatLogger.log_info("vector_service", "最高スコア結果", {
                "score": best_score,
                "title": best_title[:50]
            })
            # DEBUG: top5を詳細表示
            try:
                top5 = [{"title": t, "score": s} for t, s in sorted_items[:5]]
                GameChatLogger.log_debug(
                    "vector_service",
                    "上位スコア（top5, 並列）",
                    {"top5": top5},
                )
            except Exception:
                pass
        
        # カード名リストに変換
        return [title for title, _ in sorted(score_by_title.items(), key=lambda kv: kv[1], reverse=True)]
    
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