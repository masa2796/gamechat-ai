#!/usr/bin/env python3
"""
改善されたプロンプトのテスト用スクリプト

LLMプロンプトの改善が正しく機能しているかテストします。
"""

import os
import sys
import asyncio

# バックエンドのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.classification_service import ClassificationService
from backend.app.models.classification_models import ClassificationRequest

# モック環境を設定
os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"
os.environ["BACKEND_TESTING"] = "true"

async def test_improved_prompt():
    """改善されたプロンプトのテスト"""
    
    service = ClassificationService()
    
    # テストケース: 集約クエリ
    test_cases = [
        "一番高いHPのカード",
        "最大ダメージのカード", 
        "上位3位のコストカード",
        "HPが50から100の間のカード",
        "コストが1または2のカード",
        "約100のHPのカード",
        "強いドラゴンカード",
        "最高攻撃力で人気のカード"
    ]
    
    print("=== 改善されたプロンプトのテスト ===")
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{i}. テストクエリ: '{query}'")
        
        try:
            request = ClassificationRequest(query=query)
            result = await service.classify_query(request)
            
            print(f"   分類タイプ: {result.query_type}")
            print(f"   信頼度: {result.confidence}")
            print(f"   フィルターキーワード: {result.filter_keywords}")
            print(f"   検索キーワード: {result.search_keywords}")
            print(f"   推論: {result.reasoning}")
            
        except Exception as e:
            print(f"   エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_improved_prompt())
