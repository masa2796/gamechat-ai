#!/usr/bin/env python3
"""
LLMベースのデータベース検索機能のテストスクリプト
"""
import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..backend'))

from backend.app.services.database_service import DatabaseService

async def test_llm_database_search():
    """LLMベースのデータベース検索をテスト"""
    print("=== LLMベースのデータベース検索テスト ===")
    
    # テスト環境設定
    os.environ["BACKEND_TESTING"] = "true"
    os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"
    
    # データベースサービス初期化
    db_service = DatabaseService()
    
    # テストクエリ
    test_queries = [
        "5コストのエルフカードを探して",
        "HP100以上のレジェンドカード",
        "3コストのドラゴンクラス",
        "体力50以下のブロンズカード",
        "コスト2のニュートラルカード"
    ]
    
    for query in test_queries:
        print(f"\n--- テストクエリ: {query} ---")
        
        try:
            # LLMクエリ解析をテスト
            analysis = await db_service._analyze_query_with_llm(query)
            print(f"解析結果: {analysis}")
            
            # LLMベースの検索を実行
            results = await db_service.filter_search_llm_async(query, top_k=5)
            print(f"検索結果: {len(results)}件")
            for i, result in enumerate(results[:3]):  # 最初の3件を表示
                print(f"  {i+1}. {result}")
                
        except Exception as e:
            print(f"エラー: {e}")
    
    print("\n=== スマートフィルタ検索テスト ===")
    
    # スマートフィルタ検索をテスト
    smart_query = "強いレジェンドカードを教えて"
    try:
        # LLM使用
        llm_results = await db_service.smart_filter_search_async(smart_query, top_k=3, use_llm=True)
        print(f"LLM検索結果: {llm_results}")
        
        # キーワード検索
        keyword_results = await db_service.smart_filter_search_async(smart_query, top_k=3, use_llm=False)
        print(f"キーワード検索結果: {keyword_results}")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_database_search())
