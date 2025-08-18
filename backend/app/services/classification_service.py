import asyncio
import json
import os
import random
import re
import openai
from ..models.classification_models import ClassificationRequest, ClassificationResult, QueryType, SearchStrategy
from ..core.config import settings
from ..core.exceptions import ClassificationException
from ..core.logging import GameChatLogger


class ClassificationService:
    """
    LLMによるクエリ分類・要約サービス。

    OpenAI GPT-4oを使用してユーザーのクエリを分析し、最適な検索戦略を決定します。
    """

    def __init__(self) -> None:
        # モック環境のチェック
        mock_external = os.getenv("BACKEND_MOCK_EXTERNAL_SERVICES", "false").lower() == "true"
        is_testing = os.getenv("BACKEND_TESTING", "false").lower() == "true"

        self.is_mocked = bool(mock_external or is_testing)
        self.client = None

        if not self.is_mocked:
            # OpenAI クライアントを初期化
            api_key = getattr(settings, "BACKEND_OPENAI_API_KEY", None) or os.getenv("BACKEND_OPENAI_API_KEY")
            if not api_key or api_key in {"your_openai_api_key", "your_actual_openai_api_key_here", "sk-test_openai_key"}:
                raise ClassificationException(
                    "OpenAI APIキーが設定されていません。.envファイルでBACKEND_OPENAI_API_KEYを設定してください。"
                )
            self.client = openai.OpenAI(api_key=api_key)

        # システムプロンプト（固定の方針。効果検索の扱いも明記）
        self.system_prompt = (
            "あなたはカードゲームのデータベース検索アシスタントです。\n"
            "ユーザーのクエリを解析し、検索分類とキーワード抽出を行ってください。\n\n"
            "分類タイプ:\n"
            "- greeting: 挨拶・雑談（検索不要）\n"
            "- filterable: 数値/集約/属性などでDBフィルタ可能\n"
            "- semantic: 効果/挙動など意味検索\n"
            "- hybrid: filterable と semantic の両方\n\n"
            "効果検索の扱い（重要）:\n"
            "- 『〜な効果』『〜できる』『〜の効果』など、カードの効果・挙動を自然言語で聞く場合は原則 semantic。\n"
            "- ただし効果に加え、コスト/クラス/レア/HP/攻撃/ダメージ等の数値・集約・属性条件が併記される場合は hybrid。\n"
            "  例:『コスト3以下でドローできるカード』→ hybrid,『エルフで疾走を付与できるカード』→ hybrid,\n"
            "     『継続ダメージを与えるカード』『守護を無視して攻撃できるカード』→ semantic。\n\n"
            "必ず以下のJSONのみを出力してください:\n"
            "{\n"
            "  \"query_type\": \"greeting|filterable|semantic|hybrid\",\n"
            "  \"summary\": \"要約\",\n"
            "  \"confidence\": 0.0,\n"
            "  \"filter_keywords\": [],\n"
            "  \"search_keywords\": [],\n"
            "  \"reasoning\": \"分類理由\"\n"
            "}"
        )

    async def classify_query(self, request: ClassificationRequest) -> ClassificationResult:
        """クエリを分類して結果を返す（モック時はヒューリスティック）。"""

        # モック/テスト環境ではLLMを呼ばずに判定
        if self.is_mocked:
            return self._mock_classify(request)

        # LLMに渡すユーザープロンプト（例と最終質問を添付）
        user_prompt = (
            "以下の方針に従って分類してください。\n"
            "- 数値/集約/属性がある → filterable\n"
            "- 効果だけ → semantic\n"
            "- 効果 + 数値/集約/属性 → hybrid\n\n"
            "例1:『継続ダメージを与えるカード』→ semantic\n"
            "例2:『コスト3以下でドローできるカード』→ hybrid (コスト+効果)\n"
            "例3:『エルフで疾走を付与できるカード』→ hybrid (属性+効果)\n\n"
            f"質問: {request.query}"
        )

        max_retries = 3
        base_delay = 1.0
        response = None

        for attempt in range(max_retries + 1):
            try:
                GameChatLogger.log_info(
                    "classification_service",
                    f"OpenAI API呼び出し開始 (試行 {attempt + 1}/{max_retries + 1})",
                )

                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=300,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    timeout=10,
                )

                GameChatLogger.log_success(
                    "classification_service", f"OpenAI API呼び出し成功 (試行 {attempt + 1})"
                )
                break

            except openai.AuthenticationError as e:
                GameChatLogger.log_error(
                    "classification_service",
                    "OpenAI認証エラー",
                    e,
                    {
                        "api_key_prefix": (
                            getattr(settings, "OPENAI_API_KEY", "None")[:10]
                            if getattr(settings, "OPENAI_API_KEY", None)
                            else "None"
                        )
                    },
                )
                raise ClassificationException(
                    message="OpenAI APIキーが無効です。正しいAPIキーを設定してください。",
                    code="INVALID_API_KEY",
                ) from e

            except openai.RateLimitError as e:
                if attempt == max_retries:
                    GameChatLogger.log_error(
                        "classification_service",
                        "OpenAI レート制限、全リトライ試行完了",
                        e,
                    )
                    raise ClassificationException(
                        message="OpenAI APIのレート制限に達しました。しばらく待ってから再試行してください。",
                        code="RATE_LIMIT_EXCEEDED",
                    ) from e
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                GameChatLogger.log_warning(
                    "classification_service",
                    f"OpenAI APIレート制限エラー、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})",
                )
                await asyncio.sleep(delay)

            except openai.OpenAIError as e:
                error_str = str(e)
                if (
                    "429" in error_str
                    or "rate_limit" in error_str.lower()
                    or "too many requests" in error_str.lower()
                ):
                    if attempt == max_retries:
                        GameChatLogger.log_error(
                            "classification_service",
                            f"OpenAI APIレート制限（その他）、全リトライ試行完了: {error_str}",
                            e,
                        )
                        raise ClassificationException(
                            message="現在多くのリクエストが集中しているため処理できません。少し時間をおいてからもう一度お試しください。",
                            code="RATE_LIMIT_EXCEEDED",
                        ) from e
                    delay = base_delay * (2**attempt) + random.uniform(0, 1)
                    GameChatLogger.log_warning(
                        "classification_service",
                        f"OpenAI APIレート制限エラー（その他）、{delay:.1f}秒後にリトライします (試行 {attempt + 1}/{max_retries + 1})",
                    )
                    await asyncio.sleep(delay)
                else:
                    GameChatLogger.log_error(
                        "classification_service", "OpenAI APIエラー", e
                    )
                    raise ClassificationException(
                        message=f"OpenAI APIでエラーが発生しました: {error_str}",
                        code="OPENAI_API_ERROR",
                    ) from e

            except Exception as e:
                GameChatLogger.log_error(
                    "classification_service",
                    f"予期しないエラー (試行 {attempt + 1})",
                    e,
                )
                raise ClassificationException(
                    message=f"分類処理中に予期しないエラーが発生しました: {str(e)}",
                    code="UNEXPECTED_ERROR",
                ) from e

        if response is None:
            # ここに来るのは通常例外済みだが、念のためフォールバック
            return ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary=request.query,
                confidence=0.3,
                search_keywords=[request.query],
                reasoning="LLM応答なしフォールバック",
            )

        result_text = (response.choices[0].message.content or "").strip()
        if not result_text:
            raise ClassificationException(
                message="OpenAI APIからの応答が空です", code="EMPTY_RESPONSE"
            )

        GameChatLogger.log_info(
            "classification_service",
            "LLM応答取得完了",
            {"response_length": len(result_text)},
        )
        GameChatLogger.log_info(
            "classification_service",
            "LLM生応答(JSON)",
            {"llm_raw_response": result_text[:1000]},
        )

        try:
            result_data = json.loads(result_text)

            # 必須フィールド補完
            required_fields = [
                "query_type",
                "summary",
                "confidence",
                "filter_keywords",
                "search_keywords",
                "reasoning",
            ]
            defaults = {
                "query_type": "semantic",
                "summary": request.query,
                "confidence": 0.3,
                "filter_keywords": [],
                "search_keywords": [],
                "reasoning": "",
            }
            missing = [
                f for f in required_fields if f not in result_data or result_data[f] is None
            ]
            if missing:
                GameChatLogger.log_warning(
                    "classification_service",
                    "OpenAI応答に必須フィールド欠落（デフォルト補完）",
                    {"missing_fields": missing, "response_text": result_text[:200]},
                )
                for f in missing:
                    result_data[f] = defaults[f]

            # 型の整形
            if isinstance(result_data.get("query_type"), str):
                result_data["query_type"] = QueryType(result_data["query_type"])
            for k in ("filter_keywords", "search_keywords"):
                if not isinstance(result_data.get(k), list):
                    result_data[k] = []
            if not isinstance(result_data.get("reasoning"), str):
                result_data["reasoning"] = (
                    str(result_data["reasoning"]) if result_data.get("reasoning") is not None else ""
                )

            # 補助: キーワードが空ならクエリから抽出
            def extract_keywords_fallback(query: str) -> list[str]:
                keywords: list[str] = []

                class_names = [
                    "エルフ",
                    "ドラゴン",
                    "ロイヤル",
                    "ウィッチ",
                    "ネクロマンサー",
                    "ビショップ",
                    "ネメシス",
                    "ヴァンパイア",
                    "ニュートラル",
                ]
                for cname in class_names:
                    if cname in query and cname not in keywords:
                        keywords.append(cname)

                patterns = [
                    r"(\d+)\s*コスト",
                    r"コスト\s*(\d+)",
                    r"(\d+)\s*HP|HP\s*(\d+)",
                    r"(\d+)\s*ダメージ|ダメージ\s*(\d+)",
                ]
                for pat in patterns:
                    for m in re.finditer(pat, query, re.IGNORECASE):
                        kw = m.group(0).strip()
                        if kw and kw not in keywords:
                            keywords.append(kw)

                for w in re.split(r"[\s　,、]+", query):
                    w = w.strip()
                    if w and w not in keywords:
                        keywords.append(w)

                return keywords

            if (
                (not result_data["filter_keywords"] or not result_data["search_keywords"]) and result_data["query_type"] != QueryType.GREETING
            ):
                GameChatLogger.log_warning(
                    "classification_service",
                    "OpenAI応答のfilter_keywordsまたはsearch_keywordsが空です（自動抽出で補完）",
                    {
                        "filter_keywords": result_data["filter_keywords"],
                        "search_keywords": result_data["search_keywords"],
                        "response_text": result_text[:200],
                    },
                )
                if not result_data["filter_keywords"]:
                    result_data["filter_keywords"] = extract_keywords_fallback(request.query)
                if not result_data["search_keywords"]:
                    result_data["search_keywords"] = extract_keywords_fallback(request.query)

            classification = ClassificationResult.parse_obj(result_data)
            GameChatLogger.log_success(
                "classification_service",
                "クエリ分類完了",
                {
                    "query_type": classification.query_type,
                    "confidence": classification.confidence,
                    "filter_keywords_count": len(classification.filter_keywords or []),
                    "search_keywords_count": len(classification.search_keywords or []),
                },
            )
            return classification

        except json.JSONDecodeError as json_error:
            GameChatLogger.log_warning(
                "classification_service",
                "JSON解析エラー - フォールバック実行",
                {"json_error": str(json_error), "response_text": result_text[:100]},
            )
            return ClassificationResult(
                query_type=QueryType.FILTERABLE,
                summary=request.query,
                confidence=0.5,
                filter_keywords=["コスト", "HP", "ダメージ"],
                search_keywords=[request.query],
                reasoning="JSON解析エラー - 手動キーワード抽出で対応",
            )
        except Exception as e:
            GameChatLogger.log_error(
                "classification_service", "必須フィールド欠落または型不整合", e
            )
            return ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary=request.query,
                confidence=0.3,
                search_keywords=[request.query],
                reasoning=f"分類エラー: {str(e)}",
            )

    def _mock_classify(self, request: ClassificationRequest) -> ClassificationResult:
        """モック/テスト用の簡易ルール分類。効果検索の優先規則を実装。"""
        q = request.query.strip()

        # 挨拶検出
        greeting_words = [
            "こんにちは",
            "おはよう",
            "こんばんは",
            "ありがとう",
            "よろしく",
            "元気",
            "調子は",
        ]
        if any(w in q for w in greeting_words):
            return ClassificationResult(
                query_type=QueryType.GREETING,
                summary="挨拶",
                confidence=0.99,
                filter_keywords=[],
                search_keywords=[],
                reasoning="挨拶語を検出",
            )

        # 効果ワード（例示）
        effect_words = [
            # 汎用
            "効果",
            "できる",
            "付与",
            "与える",
            # ドロー系
            "ドロー",
            "カードを引く",
            # 貫通/キーワード能力
            "守護を無視",
            "疾走",
            "必殺",
            "ドレイン",
            "バリア",
            # ダメージ/バーン
            "継続ダメージ",
            "バーン",
            "ダメージを与える",
            # 破壊/除去系（追加）
            "破壊",
            "破壊する",
            "破壊できる",
            "除去",
            "消滅",
            "相手のカードを破壊",
            "相手のフォロワーを破壊",
            "フォロワーを破壊",
        ]
        has_effect = any(w in q for w in effect_words)

        # 数値/集約/属性
        numeric_words = [
            "以上",
            "以下",
            "未満",
            "より",
            "から",
            "まで",
            "〜",
            "約",
            "程度",
            "およそ",
            "または",
            "か",
            "-",
            "コスト",
            "HP",
            "攻撃",
            "ダメージ",
            "\n",
        ]
        aggregate_words = [
            "一番",
            "一番高い",
            "一番低い",
            "最大",
            "最高",
            "最小",
            "最低",
            "上位",
            "トップ",
            "ボトム",
            "ベスト",
        ]
        class_words = [
            "エルフ",
            "ドラゴン",
            "ロイヤル",
            "ウィッチ",
            "ネクロマンサー",
            "ビショップ",
            "ネメシス",
            "ヴァンパイア",
            "ニュートラル",
        ]
        has_numeric = bool(re.search(r"\d+", q)) or any(w in q for w in numeric_words)
        has_aggregate = any(w in q for w in aggregate_words)
        has_attribute = any(w in q for w in class_words)

        filter_keywords: list[str] = []
        search_keywords: list[str] = []

        # ルール
        if has_effect and (has_numeric or has_aggregate or has_attribute):
            qt = QueryType.HYBRID
            conf = 0.92
            # 効果はsearchへ、条件はfilterへ
            search_keywords = [w for w in effect_words if w in q]
            filter_keywords = [w for w in (numeric_words + aggregate_words + class_words) if w in q]
            if not filter_keywords and has_numeric:
                filter_keywords.append("数値条件")
        elif has_effect:
            qt = QueryType.SEMANTIC
            conf = 0.9
            search_keywords = [w for w in effect_words if w in q] or [q]
            filter_keywords = []
        else:
            if has_numeric or has_aggregate or has_attribute:
                qt = QueryType.FILTERABLE
                conf = 0.9
                filter_keywords = [w for w in (numeric_words + aggregate_words + class_words) if w in q]
                search_keywords = [q]
            else:
                qt = QueryType.SEMANTIC
                conf = 0.6
                search_keywords = [q]
                filter_keywords = []

        return ClassificationResult(
            query_type=qt,
            summary=q,
            confidence=conf,
            filter_keywords=filter_keywords,
            search_keywords=search_keywords,
            reasoning="モック分類ルールに基づく推定",
        )

    def determine_search_strategy(self, classification: ClassificationResult) -> SearchStrategy:
        """分類結果に基づいて検索戦略を決定"""
        if classification.query_type == QueryType.GREETING:
            return SearchStrategy(use_db_filter=False, use_vector_search=False)
        elif classification.query_type == QueryType.FILTERABLE:
            return SearchStrategy(
                use_db_filter=True,
                use_vector_search=False,
                db_filter_params={
                    "keywords": classification.filter_keywords,
                    "confidence": classification.confidence,
                },
            )
        elif classification.query_type == QueryType.SEMANTIC:
            return SearchStrategy(
                use_db_filter=False,
                use_vector_search=True,
                vector_search_params={
                    "keywords": classification.search_keywords,
                    "confidence": classification.confidence,
                },
            )
        else:  # HYBRID
            return SearchStrategy(
                use_db_filter=True,
                use_vector_search=True,
                db_filter_params={
                    "keywords": classification.filter_keywords,
                    "confidence": classification.confidence,
                },
                vector_search_params={
                    "keywords": classification.search_keywords,
                    "confidence": classification.confidence,
                },
            )
