#!/usr/bin/env python3
"""
ハイブリッド検索機能のテストスクリプト
"""

import asyncio
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.hybrid_search_service import HybridSearchService

async def test_queries():
    """様々なクエリをテストする"""
    hybrid_service = HybridSearchService()
    
    test_queries = [
        "HPが100以上のポケモンを教えて",  # フィルター可能
        "強いポケモンを教えて",           # 意味検索
        "炎タイプで強いポケモンは？",     # ハイブリッド
        "フシギダネについて教えて",       # 意味検索
        "レアリティがRRのカード",        # フィルター可能
        "おすすめの戦略を教えて",         # 意味検索
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"テスト {i}: {query}")
        print('='*50)
        
        try:
            result = await hybrid_service.search(query, top_k=3)
            
            print(f"✅ 分類: {result['classification'].query_type}")
            print(f"✅ 要約: {result['classification'].summary}")
            print(f"✅ 信頼度: {result['classification'].confidence}")
            print(f"✅ DB検索結果: {len(result['db_results'])}件")
            print(f"✅ ベクトル検索結果: {len(result['vector_results'])}件")
            print(f"✅ 最終結果: {len(result['merged_results'])}件")
            
            if result['merged_results']:
                print("\n📋 最終結果の詳細:")
                for j, item in enumerate(result['merged_results'][:2], 1):
                    print(f"  {j}. {item.title} (スコア: {item.score:.3f})")
                    print(f"     {item.text[:100]}...")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_queries())
