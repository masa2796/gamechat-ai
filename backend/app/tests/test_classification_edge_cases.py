import pytest
from unittest.mock import MagicMock
from backend.app.services.classification_service import ClassificationService
from backend.app.models.classification_models import ClassificationRequest, ClassificationResult, QueryType

class TestClassificationEdgeCases:
    """分類サービスのエッジケース・例外パターンテスト"""

    @pytest.fixture
    def classification_service(self):
        return ClassificationService()

    @pytest.mark.asyncio
    async def test_classify_inappropriate_content(self, classification_service, monkeypatch):
        """不適切コンテンツの分類テスト"""
        # 攻撃的言葉遣いの場合のモック
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "greeting",
            "summary": "不適切な表現",
            "confidence": 0.9,
            "filter_keywords": [],
            "search_keywords": [],
            "reasoning": "不適切な表現を検出、検索は不要"
        }"""
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        inappropriate_queries = [
            "お前バカか？",
            "クソゲーだな",
            "うざい",
            "死ね"
        ]
        
        for query in inappropriate_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # 不適切なコンテンツは検索をスキップ
            assert result.query_type == QueryType.GREETING
            assert len(result.search_keywords) == 0
            assert len(result.filter_keywords) == 0

    @pytest.mark.asyncio
    async def test_classify_off_topic_questions(self, classification_service, monkeypatch):
        """ゲーム以外の話題の分類テスト"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "greeting",
            "summary": "話題逸脱",
            "confidence": 0.8,
            "filter_keywords": [],
            "search_keywords": [],
            "reasoning": "ゲーム以外の話題のため検索不要"
        }"""
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        off_topic_queries = [
            "今日の天気は？",
            "株価について教えて",
            "コロナの情報は？",
            "政治のニュースを知りたい",
            "料理のレシピを教えて"
        ]
        
        for query in off_topic_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # ゲーム以外の話題は検索をスキップ
            assert result.query_type == QueryType.GREETING
            assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_classify_ambiguous_questions(self, classification_service, monkeypatch):
        """曖昧で分類困難な質問のテスト"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "semantic",
            "summary": "曖昧な質問",
            "confidence": 0.3,
            "filter_keywords": [],
            "search_keywords": ["それ", "何"],
            "reasoning": "意図が不明瞭、低信頼度で意味検索を試行"
        }"""
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        ambiguous_queries = [
            "それって何？",
            "どうですか？",
            "いいですね",
            "はい",
            "なるほど"
        ]
        
        for query in ambiguous_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # 曖昧な質問は低信頼度
            assert result.confidence <= 0.5

    @pytest.mark.asyncio
    async def test_classify_empty_and_invalid_input(self, classification_service, monkeypatch):
        """空文字列・不正入力のテスト"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "greeting",
            "summary": "無効な入力",
            "confidence": 0.1,
            "filter_keywords": [],
            "search_keywords": [],
            "reasoning": "無効な入力のため検索不要"
        }"""
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        invalid_inputs = [
            "",
            "   ",
            "！！！",
            "???",
            "abcdefghijklmnopqrstuvwxyz" * 10,  # 極端に長い文字列
            "😀😀😀",  # 絵文字のみ
            "12345"  # 数字のみ
        ]
        
        for query in invalid_inputs:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # 無効な入力は検索をスキップ
            assert result.query_type == QueryType.GREETING
            assert result.confidence <= 0.3

    @pytest.mark.asyncio
    async def test_classify_emotional_expressions(self, classification_service, monkeypatch):
        """感情表現・文脈理解のテスト"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "query_type": "greeting", 
            "summary": "感情表現",
            "confidence": 0.7,
            "filter_keywords": [],
            "search_keywords": [],
            "reasoning": "感情表現、具体的な質問ではない"
        }"""
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(classification_service, "client", mock_client)
        
        emotional_queries = [
            "やったー！",
            "がっかりした...",
            "嬉しいです",
            "困ったなあ",
            "最高！",
            "つまらない"
        ]
        
        for query in emotional_queries:
            request = ClassificationRequest(query=query)
            result = await classification_service.classify_query(request)
            
            # 感情表現は検索をスキップまたは低信頼度
            assert result.query_type == QueryType.GREETING or result.confidence <= 0.5
