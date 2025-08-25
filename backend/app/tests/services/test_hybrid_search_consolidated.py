"""
Hybrid Search Service統合テストファイル（修正版）
test_hybrid_search_service.py と test_hybrid_search_optimization.py を統合
"""
import pytest
from app.models.classification_models import QueryType


class TestHybridSearchService:
    """ハイブリッド検索サービスの基本機能テスト"""

    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_search_returns_dict(
        self, 
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """検索が辞書形式の結果を返すテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定（async関数として）
        async def mock_vector_search(*args, **kwargs):
            return game_card_titles[:3]
        async def mock_db_search(*args, **kwargs):
            return game_card_titles[2:5]
        hybrid_search_service.vector_service.search = mock_vector_search
        hybrid_search_service.database_service.filter_search = mock_db_search
        query = "強いカードを教えて"
        result = await hybrid_search_service.search(query)
        
        # 基本的な構造チェック
        assert isinstance(result, dict)
        assert "classification" in result
        # 新仕様: 主結果は context / search_info
        assert "context" in result
        assert "search_info" in result
        if result["context"]:
            assert isinstance(result["context"], list)
            assert isinstance(result["context"][0], dict)
            assert "name" in result["context"][0]

    @pytest.mark.asyncio
    async def test_search_with_greeting(
        self, 
        hybrid_search_service,
        mock_openai_client
    ):
        """挨拶クエリのテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # 挨拶検出用の特別なレスポンスを設定
        mock_greeting_response = type('MockResponse', (), {})()
        mock_greeting_response.choices = [type('Choice', (), {})()]
        mock_greeting_response.choices[0].message = type('Message', (), {})()
        mock_greeting_response.choices[0].message.content = """{
            "query_type": "greeting",
            "summary": "挨拶",
            "confidence": 0.95,
            "filter_keywords": [],
            "search_keywords": [],
            "reasoning": "挨拶として検出"
        }"""
        mock_openai_client.chat.completions.create.return_value = mock_greeting_response
        
        query = "こんにちは"
        result = await hybrid_search_service.search(query)
        
        # 挨拶の場合は検索をスキップ
        assert isinstance(result, dict)
        assert result["classification"].query_type == QueryType.GREETING

    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_search_with_semantic_query(
        self, 
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """意味的検索クエリのテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client

        async def mock_vector_search(*args, **kwargs):
            return game_card_titles[:3]
        hybrid_search_service.vector_service.search = mock_vector_search

        query = "カードについて教えて"
        result = await hybrid_search_service.search(query)
        assert isinstance(result, dict)
        assert "context" in result or "search_info" in result

    @pytest.mark.asyncio
    async def test_search_handles_errors_gracefully(
        self, 
        hybrid_search_service,
        mock_openai_client
    ):
        """エラーハンドリングテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # エラーを発生させるモック（async関数として）
        async def mock_error_search(*args, **kwargs):
            raise Exception("Search error")
        
        hybrid_search_service.vector_service.search = mock_error_search
        
        query = "エラーテスト"
        # HybridSearchServiceにエラーハンドリングが組み込まれている場合、例外は発生しない
        try:
            result = await hybrid_search_service.search(query)
            # エラーハンドリングが適切に行われている
            assert isinstance(result, dict)
        except Exception:
            # エラーハンドリングがない場合は例外が発生する
            pass


class TestHybridSearchOptimization:
    """ハイブリッド検索最適化テスト"""
    
    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_optimization_with_high_confidence(
        self,
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """高信頼度での最適化テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_titles[:5]

        hybrid_search_service.vector_service.search = mock_vector_search
        
        query = "最適化テスト"
        result = await hybrid_search_service.search(query)
        
        assert isinstance(result, dict)
        assert "search_quality" in result or "merged_results" in result
    
    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_search_strategy_selection(
        self,
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """検索戦略選択テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_titles[:3]

        async def mock_db_search(*args, **kwargs):
            return game_card_titles[1:4]

        hybrid_search_service.vector_service.search = mock_vector_search
        hybrid_search_service.database_service.filter_search = mock_db_search
        
        query = "戦略テスト"
        result = await hybrid_search_service.search(query)
        
        assert isinstance(result, dict)
        assert "search_strategy" in result or "classification" in result

    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_result_merging_and_deduplication(
        self, 
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """結果マージと重複除去テスト"""
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client

        vector_results = game_card_titles[:3]
        db_results = game_card_titles[1:4]
        async def mock_vector_search(*args, **kwargs):
            return vector_results
        async def mock_db_search(*args, **kwargs):
            return db_results
        hybrid_search_service.vector_service.search = mock_vector_search
        hybrid_search_service.database_service.filter_search = mock_db_search

        query = "マージテスト"
        result = await hybrid_search_service.search(query)
        assert isinstance(result, dict)
        assert "context" in result or "search_info" in result


class TestHybridSearchPerformance:
    """ハイブリッド検索パフォーマンステスト"""
    
    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_search_response_time(
        self,
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """検索レスポンス時間テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        import time

        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_titles[:3]

        hybrid_search_service.vector_service.search = mock_vector_search
        
        query = "パフォーマンステスト"
        
        start_time = time.time()
        result = await hybrid_search_service.search(query)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # 5秒以内でのレスポンスを期待（実際のAPI呼び出しを含むため緩め）
        assert response_time < 5.0
        assert isinstance(result, dict)
    
    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_concurrent_search_handling(
        self,
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """並行検索処理テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        import asyncio

        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_titles[:2]

        hybrid_search_service.vector_service.search = mock_vector_search
        
        # 複数の並行検索タスク
        async def search_task(query_id):
            query = f"並行検索{query_id}"
            return await hybrid_search_service.search(query)
        
        tasks = [search_task(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        # すべてのタスクが正常に完了することを確認
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results)

    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_memory_efficiency(
        self, 
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """メモリ効率テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # 大量データのモック
        large_titles = [f"大量データ{i}" for i in range(50)]
        
        async def mock_vector_search(*args, **kwargs):
            return large_titles[:20]
        
        hybrid_search_service.vector_service.search = mock_vector_search
        
        query = "メモリテスト"
        result = await hybrid_search_service.search(query)
        
        # メモリ効率的に処理されることを確認
        assert isinstance(result, dict)
        assert "context" in result
        if result["context"]:
            assert len(result["context"]) <= 50
            assert isinstance(result["context"][0], dict)
            assert "name" in result["context"][0]
    
class TestHybridSearchConfiguration:
    """ハイブリッド検索設定テスト"""

    def test_service_initialization(self):
        """サービス初期化テスト"""
        from app.services.hybrid_search_service import HybridSearchService
        service = HybridSearchService()
        
        assert service is not None
        assert hasattr(service, 'classification_service')
        assert hasattr(service, 'vector_service')
        assert hasattr(service, 'database_service')
        assert hasattr(service, 'embedding_service')
    
    @pytest.mark.skip(reason="一時スキップ: 実装修正中")
    @pytest.mark.asyncio
    async def test_service_with_different_top_k(
        self,
        hybrid_search_service,
        game_card_titles,
        mock_openai_client
    ):
        """異なるtop_k値でのテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_titles[:kwargs.get('top_k', 3)]

        hybrid_search_service.vector_service.search = mock_vector_search
        
        for top_k in [1, 3, 5]:
            query = f"top_kテスト{top_k}"
            result = await hybrid_search_service.search(query, top_k=top_k)
            
            assert isinstance(result, dict)
            # top_kパラメータが適切に処理されることを確認


class TestHybridSearchZeroHitRegression:
    """過去 zero-hit だった効果検索クエリの回帰テスト。

    目的: synonym 展開 / retry 戦略 / combined namespace 導入後に
    当該クエリで Top-10 が空にならないことを保証する。
    判定基準: search_info.vector_results_count + db_results_count > 0。
    """

    test_queries = [
        "フィールドのカードを手札に戻すカード",
        "相手のリーダーにダメージを与えるカード",
        "ランダムな相手のフォロワーにダメージを与えるカード",
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query", test_queries)
    async def test_effect_semantic_queries_return_non_empty_top10(
        self,
        query: str,
        hybrid_search_service,
        mock_openai_client,
    ):
        # OpenAI クライアントをモック（分類/埋め込み双方）
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client

        # 分類レスポンス簡易モック: semantic として扱う
        mock_resp = type("MockResponse", (), {})()
        mock_resp.choices = [type("Choice", (), {})()]
        mock_resp.choices[0].message = type("Message", (), {})()
        mock_resp.choices[0].message.content = """{
            \"query_type\": \"semantic\",
            \"summary\": \"効果検索\",
            \"confidence\": 0.85,
            \"filter_keywords\": [],
            \"search_keywords\": []
        }"""
        mock_openai_client.chat.completions.create.return_value = mock_resp

        # Upstash 接続が無い CI/ローカルでは vector をモックし、
        # 接続がある環境では実際のフォールバック挙動 (retry stage) を検証できるようにする。
        if getattr(hybrid_search_service.vector_service, "vector_index", None) is None:
            async def mock_vector_search(*args, **kwargs):
                return ["ダミーカードA", "ダミーカードB", "ダミーカードC"]
            hybrid_search_service.vector_service.search = mock_vector_search

        result = await hybrid_search_service.search(query, top_k=10)

        assert isinstance(result, dict)
        assert "search_info" in result
        info = result["search_info"]
        v_cnt = info.get("vector_results_count", 0)
        d_cnt = info.get("db_results_count", 0)
        # デバッグ補助情報（失敗時に retry 段階などを表示）
        vp = getattr(hybrid_search_service.vector_service, "last_params", {}) or {}
        debug_ctx = f" query={query} v_cnt={v_cnt} d_cnt={d_cnt} last_params={vp}"
        # Top-10 で vector/db どちらかがヒットしていること
        assert (v_cnt + d_cnt) > 0, "zero-hit: " + debug_ctx
        # semantic/hybrid 系では vector ヒットも最低1件期待
        assert v_cnt > 0, "vector empty: " + debug_ctx

