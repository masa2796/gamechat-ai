from typing import List, Optional
import os
import asyncio
from upstash_vector import Index
from dotenv import load_dotenv
from ..models.rag_models import ContextItem
from ..models.classification_models import ClassificationResult, QueryType
from ..core.config import settings
from ..core.decorators import handle_service_exceptions
from ..core.logging import GameChatLogger
from ..core.metrics import inc_plateau_trigger

load_dotenv()

class VectorService:
    last_scores: dict = {}
    last_score_sources: dict = {}
    last_params: dict = {}
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
        upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        is_test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        env = os.getenv("ENVIRONMENT", "development")
        if is_test_mode:
            GameChatLogger.log_info("vector_service", "テストモード: Vector検索無効化")
            self.vector_index = None
            return
        if not upstash_url or not upstash_token:
            if env == "production":
                err = Exception("Upstash Vector設定が不完全です")
                GameChatLogger.log_error("vector_service", "本番設定不備", err)
            else:
                GameChatLogger.log_warning("vector_service", "🟡 Upstash Vector設定不足")
            self.vector_index = None
            return
        try:
            self.vector_index = Index(url=upstash_url, token=upstash_token)
            GameChatLogger.log_success("vector_service", "✅ Upstash Vector 初期化成功")
        except Exception as e:  # 初期化エラーは致命的にせずログのみ
            GameChatLogger.log_error("vector_service", "Upstash Vector 初期化失敗 (フォールバック: 無効化)", e)
            self.vector_index = None

    @handle_service_exceptions("vector_service")
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 50,
        namespaces: Optional[List[str]] = None,
        classification: Optional[ClassificationResult] = None,
        min_score: Optional[float] = None
    ) -> List[str]:
        """ベクトル検索 (Stage0: effect_combined除外→Plateau条件で挿入)"""
        if classification is not None:
            try:
                top_k, min_score, namespaces = self._optimize_search_params(classification, top_k, min_score, namespaces)
            except Exception as e:
                GameChatLogger.log_warning("vector_service", f"最適化失敗: {e}")
        if self.vector_index is None:
            return []

        scores: dict[str, float] = {}
        score_sources: dict[str, str] = {}
        # 統計計算（静的メソッド利用）
        def _calc_top3_stats(local: dict[str, float]):
            return self.calc_top3_stats(local)

        def _query_ns(ns_list: List[str], threshold: Optional[float], inner_top_k: int):
            for ns in ns_list:
                try:
                    res = self.vector_index.query(  # type: ignore
                        vector=query_embedding,
                        top_k=inner_top_k,
                        namespace=ns,
                        include_metadata=True,
                        include_vectors=True
                    )
                    matches = res.matches if hasattr(res, "matches") else res
                    if not matches:
                        continue
                    for m in matches:
                        sc = float(getattr(m, 'score', 0.0) or 0.0)
                        if threshold is not None and sc < threshold:
                            continue
                        meta = getattr(m, 'metadata', None)
                        title = meta.get('title', f"{ns} - 情報") if meta and hasattr(meta, 'get') else f"{ns} - 情報"
                        if not title:
                            continue
                        prev = scores.get(title)
                        if prev is None or sc > prev:
                            scores[title] = sc
                            score_sources[title] = ns
                except Exception as inner_e:
                    GameChatLogger.log_error("vector_service", f"Namespace {ns} 検索エラー", inner_e, {"namespace": ns})
                    continue

        # Namespace 設定
        try:
            all_ns = self._get_all_namespaces()
        except Exception:
            all_ns = namespaces or []
        has_combined = "effect_combined" in all_ns
        effect_like = [n for n in all_ns if n.startswith("effect_")]
        ordered_effect = sorted(effect_like)
        if has_combined and namespaces is None:
            stage0_list = [n for n in ordered_effect if n != "effect_combined"]
        else:
            stage0_list = namespaces or ordered_effect or all_ns
        second_namespaces = (["effect_combined"] + stage0_list) if has_combined and "effect_combined" not in stage0_list else stage0_list

        base_min = float(min_score or 0.5)
        conf = settings.VECTOR_SEARCH_CONFIG.get("plateau", {}) if isinstance(settings.VECTOR_SEARCH_CONFIG, dict) else {}
        plateau_enabled = conf.get("enable_combined", True)
        std_thr = conf.get("stddev", 0.005)
        spread_thr = conf.get("score_spread", 0.01)
        extra_min = conf.get("combined_extra_min_score", 0.02)
        combined_top_k = conf.get("combined_top_k", 12)

        plateau_triggered = False
        final_stage: Optional[int] = None
        used_ns: List[str] = []
        used_min: Optional[float] = None

        _query_ns(stage0_list, base_min, top_k)
        used_ns = stage0_list
        used_min = base_min
        if scores:
            final_stage = 0

        need_plateau = False
        stats = _calc_top3_stats(scores)
        if plateau_enabled:
            if not scores:
                need_plateau = True
            elif stats and (stats['stddev'] <= std_thr or stats['spread'] <= spread_thr):
                need_plateau = True
        if need_plateau and has_combined:
            plateau_triggered = True
            adj_min = base_min + extra_min
            _query_ns(second_namespaces, adj_min, min(max(combined_top_k, 10), 30))
            try:
                inc_plateau_trigger()
            except Exception:
                pass
            if scores and final_stage is None:
                final_stage = 1
            used_ns = second_namespaces
            used_min = adj_min

        sorted_titles = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top5 = [{"title": t, "score": s} for t, s in sorted_titles[:5]]
        GameChatLogger.log_success("vector_service", "ベクトル検索完了", {"total_results": len(sorted_titles), "top5": top5})
        self.last_scores = scores
        self.last_score_sources = score_sources
        try:
            self.last_params = {
                "final_stage": final_stage,
                "used_namespaces": used_ns,
                "min_score": used_min,
                "top5": top5,
                "requested_top_k": top_k,
                "stage0_excluded_combined": has_combined,
                "namespace_by_title_sample": {t: score_sources.get(t) for t,_ in sorted_titles[:5]},
                "plateau_triggered": plateau_triggered,
                "plateau_stats": stats,
            }
        except Exception:
            pass
        return [t for t,_ in sorted_titles[:top_k]]

    @staticmethod
    def calc_top3_stats(local: dict[str, float]):
        """上位3件スコアの標準偏差とスプレッドを計算（テスト容易性のため分離）。"""
        try:
            if not local:
                return None
            import math
            vs = sorted(local.values(), reverse=True)[:3]
            if len(vs) <= 1:
                return {"values": vs, "stddev": 0.0, "spread": 0.0}
            mean = sum(vs)/len(vs)
            var = sum((v-mean)**2 for v in vs)/len(vs)
            return {"values": vs, "stddev": math.sqrt(var), "spread": max(vs)-min(vs)}
        except Exception:
            return None
    
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
            # フォールバック: vector_index_effects.jsonl (インデックス監査ログ) から抽出
            audit_candidates = []
            audit_candidates.append(os.path.join(project_root, "data", "vector_index_effects.jsonl"))
            if data_dir_env:
                audit_candidates.insert(0, os.path.join(data_dir_env, "vector_index_effects.jsonl"))
            audit_path = None
            for ap in audit_candidates:
                if os.path.exists(ap):
                    audit_path = ap
                    break
            if audit_path is None:
                GameChatLogger.log_warning(
                    "vector_service",
                    "convert_data.json 及び 監査ファイルが見つからず namespace を空集合として扱います",
                    {"convert_tried": candidates[:3], "audit_tried": audit_candidates[:2]}
                )
                return []
            # 監査ファイルから抽出
            namespaces = set()
            try:
                with open(audit_path, "r", encoding="utf-8") as af:
                    for i, line in enumerate(af):
                        if i > 50000:  # 念のため安全上限
                            break
                        try:
                            obj = json.loads(line)
                            if isinstance(obj, dict):
                                ns = obj.get("namespace")
                                if ns:
                                    namespaces.add(ns)
                        except Exception:
                            continue
                ns_list = sorted(list(namespaces))
                if ns_list:
                    GameChatLogger.log_info(
                        "vector_service",
                        "監査ファイルから namespace 抽出成功",
                        {"count": len(ns_list), "sample": ns_list[:8]}
                    )
                else:
                    GameChatLogger.log_warning(
                        "vector_service",
                        "監査ファイルから namespace を抽出できませんでした",
                        {"audit_path": audit_path}
                    )
                return ns_list
            except Exception as e:
                GameChatLogger.log_error("vector_service", "監査ファイル読込でエラー", e, {"audit_path": audit_path})
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
                # effect_* / effect_combined / flavorText を検索対象候補とする
                effect_like = [ns for ns in all_namespaces if ns.startswith("effect_") or ns in ("effect_combined", "flavorText")]
                ordered: List[str] = []
                if "effect_combined" in effect_like:
                    ordered.append("effect_combined")
                ordered.extend(sorted([ns for ns in effect_like if ns.startswith("effect_")]))
                if "flavorText" in effect_like:
                    ordered.append("flavorText")
                if ordered:
                    GameChatLogger.log_info("vector_service", "クエリ種別に応じて effect/combined/flavorText を優先", {
                        "query_type": query_type.value,
                        "selected_namespaces": ordered[:10],
                        "total": len(ordered)
                    })
                    return ordered
                GameChatLogger.log_warning("vector_service", "effect系 namespace が見つからず全namespaceを使用します")
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