import asyncio
import os
from app.services.classification_service import ClassificationService
from app.models.classification_models import ClassificationRequest


async def test_debug_classification():
    """分類結果をデバッグするためのテスト"""
    os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"
    service = ClassificationService()
    
    test_queries = [
        "一番高いHPのカード",
        "最大ダメージのカード", 
        "最高コストのカード",
        "HPがトップのカード",
        "一番低いHPのカード",
        "最小コストのカード"
    ]
    
    for query in test_queries:
        request = ClassificationRequest(query=query)
        result = await service.classify_query(request)
        
        print(f"\nクエリ: {query}")
        print(f"タイプ: {result.query_type}")
        print(f"フィルターキーワード: {result.filter_keywords}")
        print(f"検索キーワード: {result.search_keywords}")
        print(f"理由: {result.reasoning}")


if __name__ == "__main__":
    asyncio.run(test_debug_classification())
