#!/usr/bin/env python3
"""
ハイブリッド検索機能のデモ（APIキー不要版）
"""

import asyncio
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.database_service import DatabaseService

async def demo_database_search():
    """データベース検索のデモ"""
    print("=== データベース検索デモ ===\n")
    
    db_service = DatabaseService()
    
    test_queries = [
        (["HP", "100以上"], "HPが100以上の条件"),
        (["炎"], "炎タイプの条件"),
        (["フシギダネ"], "フシギダネ検索"),
        (["たね"], "たねポケモン検索"),
        (["RR"], "レアリティRR検索"),
    ]
    
    for keywords, description in test_queries:
        print(f"🔍 {description}")
        print(f"キーワード: {keywords}")
        
        try:
            results = await db_service.filter_search(keywords, top_k=3)
            print(f"結果: {len(results)}件")
            
            for i, item in enumerate(results[:2], 1):
                print(f"  {i}. {item.title} (スコア: {item.score:.3f})")
                print(f"     {item.text}")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(demo_database_search())
