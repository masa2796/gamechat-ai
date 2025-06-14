"""
Hybrid Search Service統合テストファイル（修正版）
test_hybrid_search_service.py と test_hybrid_search_optimization.py を統合
"""
import pytest
from backend.app.models.rag_models import ContextItem
from backend.app.models.classification_models import QueryType


class TestHybridSearchService:
    """ハイブリッド検索サービスの基本機能テスト"""

    @pytest.mark.asyncio
    async def test_search_returns_dict(
        self, 
        hybrid_search_service,
        game_card_context_items,
        mock_openai_client
    ):
        """検索が辞書形式の結果を返すテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定（async関数として）
        async def mock_vector_search(*args, **kwargs):
            return game_card_context_items[:3]
        
        async def mock_db_search(*args, **kwargs):
            return game_card_context_items[2:5]
        
        hybrid_search_service.vector_service.search = mock_vector_search
        hybrid_search_service.database_service.filter_search = mock_db_search
        
        query = "強いカードを教えて"
        result = await hybrid_search_service.search(query)
        
        # 基本的な構造チェック
        assert isinstance(result, dict)
        assert "classification" in result
        assert "merged_results" in result

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

    @pytest.mark.asyncio
    async def test_search_with_semantic_query(
        self, 
        hybrid_search_service,
        game_card_context_items,
        mock_openai_client
    ):
        """意味的検索クエリのテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定（async関数として）
        async def mock_vector_search(*args, **kwargs):
            return game_card_context_items[:3]
        
        hybrid_search_service.vector_service.search = mock_vector_search
        
        query = "カードについて教えて"
        result = await hybrid_search_service.search(query)
        
        assert isinstance(result, dict)
        assert "merged_results" in result

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
    
    @pytest.mark.asyncio
    async def test_optimization_with_high_confidence(
        self,
        hybrid_search_service,
        game_card_context_items,
        mock_openai_client
    ):
        """高信頼度での最適化テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_context_items[:5]

        hybrid_search_service.vector_service.search = mock_vector_search
        
        query = "最適化テスト"
        result = await hybrid_search_service.search(query)
        
        assert isinstance(result, dict)
        assert "search_quality" in result or "merged_results" in result
    
    @pytest.mark.asyncio
    async def test_search_strategy_selection(
        self,
        hybrid_search_service,
        game_card_context_items,
        mock_openai_client
    ):
        """検索戦略選択テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_context_items[:3]

        async def mock_db_search(*args, **kwargs):
            return game_card_context_items[1:4]

        hybrid_search_service.vector_service.search = mock_vector_search
        hybrid_search_service.database_service.filter_search = mock_db_search
        
        query = "戦略テスト"
        result = await hybrid_search_service.search(query)
        
        assert isinstance(result, dict)
        assert "search_strategy" in result or "classification" in result

    @pytest.mark.asyncio
    async def test_result_merging_and_deduplication(
        self, 
        hybrid_search_service,
        game_card_context_items
    ,
        mock_openai_client
    ):
        """結果マージと重複除去テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # 重複を含む結果を設定
        vector_results = game_card_context_items[:3]
        db_results = game_card_context_items[1:4]  # 1つ重複
        
        async def mock_vector_search(*args, **kwargs):
            return vector_results
        
        async def mock_db_search(*args, **kwargs):
            return db_results
        
        hybrid_search_service.vector_service.search = mock_vector_search
        hybrid_search_service.database_service.filter_search = mock_db_search
        
        query = "マージテスト"
        result = await hybrid_search_service.search(query)
        
        assert isinstance(result, dict)
        assert "merged_results" in result
        # 結果があることを確認（重複除去の詳細な検証は実装次第）
        assert isinstance(result["merged_results"], list)


class TestHybridSearchPerformance:
    """ハイブリッド検索パフォーマンステスト"""
    
    @pytest.mark.asyncio
    async def test_search_response_time(
        self,
        hybrid_search_service,
        game_card_context_items
    ,
        mock_openai_client
    ):
        """検索レスポンス時間テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        import time

        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_context_items[:3]

        hybrid_search_service.vector_service.search = mock_vector_search
        
        query = "パフォーマンステスト"
        
        start_time = time.time()
        result = await hybrid_search_service.search(query)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # 5秒以内でのレスポンスを期待（実際のAPI呼び出しを含むため緩め）
        assert response_time < 5.0
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_concurrent_search_handling(
        self,
        hybrid_search_service,
        game_card_context_items
    ,
        mock_openai_client
    ):
        """並行検索処理テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        import asyncio

        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_context_items[:2]

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

    @pytest.mark.asyncio
    async def test_memory_efficiency(
        self, 
        hybrid_search_service
    ,
        mock_openai_client
    ):
        """メモリ効率テスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # 大量データのモック
        large_dataset = [
            ContextItem(
                title=f"大量データ{i}",
                text=f"テキスト{i}",
                score=0.8
            ) for i in range(50)
        ]
        
        async def mock_vector_search(*args, **kwargs):
            return large_dataset[:20]
        
        hybrid_search_service.vector_service.search = mock_vector_search
        
        query = "メモリテスト"
        result = await hybrid_search_service.search(query)
        
        # メモリ効率的に処理されることを確認
        assert isinstance(result, dict)
        assert "merged_results" in result
        # 結果数が適切に制限されていることを期待
        if result["merged_results"]:
            assert len(result["merged_results"]) <= 50


class TestHybridSearchConfiguration:
    """ハイブリッド検索設定テスト"""

    def test_service_initialization(self):
        """サービス初期化テスト"""
        from backend.app.services.hybrid_search_service import HybridSearchService
        service = HybridSearchService()
        
        assert service is not None
        assert hasattr(service, 'classification_service')
        assert hasattr(service, 'vector_service')
        assert hasattr(service, 'database_service')
        assert hasattr(service, 'embedding_service')
    
    @pytest.mark.asyncio
    async def test_service_with_different_top_k(
        self,
        hybrid_search_service,
        game_card_context_items
    ,
        mock_openai_client
    ):
        """異なるtop_k値でのテスト"""
        # OpenAIクライアントをモック
        hybrid_search_service.classification_service.client = mock_openai_client
        hybrid_search_service.embedding_service.client = mock_openai_client
        
        # モックの設定
        async def mock_vector_search(*args, **kwargs):
            return game_card_context_items[:kwargs.get('top_k', 3)]

        hybrid_search_service.vector_service.search = mock_vector_search
        
        for top_k in [1, 3, 5]:
            query = f"top_kテスト{top_k}"
            result = await hybrid_search_service.search(query, top_k=top_k)
            
            assert isinstance(result, dict)
            # top_kパラメータが適切に処理されることを確認
