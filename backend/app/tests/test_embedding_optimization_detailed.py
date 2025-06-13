import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.embedding_service import EmbeddingService
from backend.app.models.classification_models import ClassificationResult, QueryType

class TestEmbeddingOptimizationDetailed:
    """埋め込み最適化の詳細テスト"""

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService()

    @pytest.fixture
    def mock_openai_embedding_response(self):
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1] * 1536
        return mock_response

    @pytest.mark.asyncio
    async def test_confidence_based_strategy_switching(self, embedding_service, mock_openai_embedding_response):
        """信頼度別埋め込み戦略の切り替えテスト"""
        
        confidence_test_cases = [
            {
                "confidence": 0.95,
                "expected_strategy": "use_summary",
                "summary": "高品質な要約テキスト",
                "keywords": ["テスト"]
            },
            {
                "confidence": 0.8,
                "expected_strategy": "use_summary",
                "summary": "品質の良い要約",
                "keywords": ["高品質"]
            },
            {
                "confidence": 0.7,
                "expected_strategy": "use_keywords_plus_query",
                "summary": "要約テキスト",
                "keywords": ["キーワード", "組み合わせ"]
            },
            {
                "confidence": 0.5,
                "expected_strategy": "use_keywords_plus_query", 
                "summary": "普通の要約",
                "keywords": ["キーワード"]
            },
            {
                "confidence": 0.3,
                "expected_strategy": "use_original_query",
                "summary": "低品質要約",
                "keywords": ["低品質"]
            }
        ]
        
        with patch.object(embedding_service, 'client') as mock_client:
            mock_client.embeddings.create.return_value = mock_openai_embedding_response
            
            for case in confidence_test_cases:
                classification = ClassificationResult(
                    query_type=QueryType.SEMANTIC,
                    summary=case["summary"],
                    confidence=case["confidence"],
                    search_keywords=case["keywords"],
                    reasoning="テスト用分類"
                )
                
                original_query = "元の質問テキスト"
                
                await embedding_service.get_embedding_from_classification(
                    original_query, classification
                )
                
                # 埋め込み生成が呼ばれたかを確認
                assert mock_client.embeddings.create.called
                
                # 使用されたテキストを確認
                call_args = mock_client.embeddings.create.call_args
                input_text = call_args[1]['input']
                
                if case["expected_strategy"] == "use_summary":
                    assert case["summary"] in input_text
                elif case["expected_strategy"] == "use_keywords_plus_query":
                    assert original_query in input_text
                    for keyword in case["keywords"]:
                        assert keyword in input_text
                elif case["expected_strategy"] == "use_original_query":
                    assert input_text == original_query
                
                # モッククリアして次のテストに備える
                mock_client.reset_mock()

    @pytest.mark.asyncio
    async def test_summary_quality_boundary_values(self, embedding_service, mock_openai_embedding_response):
        """要約品質の境界値テスト"""
        
        quality_test_cases = [
            {
                "summary": "HP",  # 5文字未満
                "original": "HPが高いポケモンを探しています", 
                "expected_quality": False,
                "reason": "too_short"
            },
            {
                "summary": "HP100以上のポケモン検索",  # 適切な長さ
                "original": "HPが100以上のポケモン",
                "expected_quality": True,
                "reason": "good_quality"
            },
            {
                "summary": "非常に強力で戦闘能力が高く、バトルで活躍できる優秀なポケモンの詳細な検索クエリで、多くの条件を満たす完璧なポケモンを見つけるための包括的な検索",  # 長すぎる
                "original": "強いポケモン",
                "expected_quality": False,
                "reason": "too_long"
            },
            {
                "summary": "検索クエリ",  # 重要キーワード欠落
                "original": "炎タイプのポケモンを探しています",
                "expected_quality": False,
                "reason": "missing_keywords"
            },
            {
                "summary": "炎タイプポケモンの検索",  # 重要キーワード保持
                "original": "炎タイプのポケモンを探しています",
                "expected_quality": True,
                "reason": "keywords_preserved"
            }
        ]
        
        for case in quality_test_cases:
            result = embedding_service._is_summary_quality_good(
                case["summary"], case["original"]
            )
            assert result == case["expected_quality"], f"Failed for {case['reason']}: {case['summary']}"

    @pytest.mark.asyncio
    async def test_query_type_specific_optimization(self, embedding_service, mock_openai_embedding_response):
        """クエリタイプ別最適化テスト"""
        
        with patch.object(embedding_service, 'client') as mock_client:
            mock_client.embeddings.create.return_value = mock_openai_embedding_response
            
            # SEMANTIC タイプ: 検索キーワードを前置
            semantic_classification = ClassificationResult(
                query_type=QueryType.SEMANTIC,
                summary="強いポケモンの検索",
                confidence=0.7,
                search_keywords=["強い", "おすすめ"],
                filter_keywords=[],
                reasoning="意味検索"
            )
            
            await embedding_service.get_embedding_from_classification(
                "強いポケモンを教えて", semantic_classification
            )
            
            call_args = mock_client.embeddings.create.call_args
            semantic_input = call_args[1]['input']
            assert "強い" in semantic_input
            assert "おすすめ" in semantic_input
            mock_client.reset_mock()
            
            # HYBRID タイプ: 両方のキーワードを組み合わせ
            hybrid_classification = ClassificationResult(
                query_type=QueryType.HYBRID,
                summary="炎タイプで強いポケモン",
                confidence=0.7,
                search_keywords=["強い"],
                filter_keywords=["炎", "タイプ"],
                reasoning="ハイブリッド検索"
            )
            
            await embedding_service.get_embedding_from_classification(
                "炎タイプで強いポケモン", hybrid_classification
            )
            
            call_args = mock_client.embeddings.create.call_args
            hybrid_input = call_args[1]['input']
            assert "強い" in hybrid_input
            assert "炎" in hybrid_input
            assert "タイプ" in hybrid_input
            mock_client.reset_mock()
            
            # FILTERABLE タイプ: 元質問を使用（フォールバック）
            filterable_classification = ClassificationResult(
                query_type=QueryType.FILTERABLE,
                summary="HP100以上のポケモン",
                confidence=0.7,
                search_keywords=[],
                filter_keywords=["HP", "100以上"],
                reasoning="フィルター検索"
            )
            
            original_query = "HPが100以上のポケモンを教えて"
            await embedding_service.get_embedding_from_classification(
                original_query, filterable_classification
            )
            
            call_args = mock_client.embeddings.create.call_args
            filterable_input = call_args[1]['input']
            assert filterable_input == original_query  # 元質問がそのまま使用される

    @pytest.mark.asyncio
    async def test_pokemon_card_keyword_preservation(self, embedding_service):
        """ポケモンカード特有キーワード保持テスト"""
        
        important_keywords = ["ポケモン", "カード", "HP", "ダメージ", "技", "タイプ", "進化", "レアリティ"]
        
        test_cases = [
            {
                "original": "ポケモンカードのHPが高い技について",
                "summary": "HPが高い技の情報",
                "should_preserve": ["ポケモン", "カード", "HP", "技"],
                "expected_quality": True  # HPと技は保持されているため
            },
            {
                "original": "炎タイプのポケモンの進化について",
                "summary": "炎タイプポケモンの進化情報",
                "should_preserve": ["ポケモン", "タイプ", "進化"],
                "expected_quality": True
            },
            {
                "original": "ダメージが高いレアリティの技",
                "summary": "高ダメージレア技",
                "should_preserve": ["ダメージ", "レアリティ", "技"],
                "expected_quality": True
            }
        ]
        
        for case in test_cases:
            result = embedding_service._is_summary_quality_good(
                case["summary"], case["original"]
            )
            assert result == case["expected_quality"]

    @pytest.mark.asyncio
    async def test_fallback_strategy_robustness(self, embedding_service, mock_openai_embedding_response):
        """フォールバック戦略の堅牢性テスト"""
        
        with patch.object(embedding_service, 'client') as mock_client:
            mock_client.embeddings.create.return_value = mock_openai_embedding_response
            
            # 異常なケースでもフォールバックが機能することを確認
            edge_cases = [
                {
                    "classification": ClassificationResult(
                        query_type=QueryType.SEMANTIC,
                        summary="",  # 空の要約
                        confidence=0.9,
                        search_keywords=[],
                        reasoning="空要約テスト"
                    ),
                    "original": "テスト質問",
                    "expected_fallback": "original_query"
                },
                {
                    "classification": ClassificationResult(
                        query_type=QueryType.SEMANTIC,
                        summary="",  # 空の要約（Noneではなく空文字列）
                        confidence=0.8,
                        search_keywords=["キーワード"],
                        reasoning="空要約テスト"
                    ),
                    "original": "テスト質問",
                    "expected_fallback": "keywords_plus_query"
                },
                {
                    "classification": ClassificationResult(
                        query_type=QueryType.SEMANTIC,
                        summary="普通の要約",
                        confidence=0.0,  # 極低信頼度
                        search_keywords=[],
                        reasoning="極低信頼度テスト"
                    ),
                    "original": "テスト質問",
                    "expected_fallback": "original_query"
                }
            ]
            
            for case in edge_cases:
                await embedding_service.get_embedding_from_classification(
                    case["original"], case["classification"]
                )
                
                # エラーが発生せず、何らかの埋め込みが生成されることを確認
                assert mock_client.embeddings.create.called
                call_args = mock_client.embeddings.create.call_args
                input_text = call_args[1]['input']
                assert len(input_text) > 0  # 空でないテキストが使用される
                
                mock_client.reset_mock()
