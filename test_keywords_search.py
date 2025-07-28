#!/usr/bin/env python3
"""
keywordsフィールドを使った検索機能のテストスクリプト
"""

import asyncio
import sys
import os
import json

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.database_service import DatabaseService

async def test_keywords_search():
    """keywordsフィールドを使った検索機能をテスト"""
    print("=== keywords検索機能テスト ===\n")
    
    # DatabaseServiceを初期化（テスト環境用）
    db_service = DatabaseService()
    db_service.is_mocked = True  # モック環境でテスト
    db_service.debug = True      # デバッグ出力を有効化
    
    # データを読み込み
    db_service.reload_data()
    print(f"データ件数: {len(db_service.data_cache)}")
    
    # データサンプルの確認（keywordsフィールドがあるか）
    sample_count = 0
    for item in db_service.data_cache[:10]:
        keywords = item.get("keywords", [])
        if keywords:
            print(f"カード名: {item.get('name', 'N/A')}")
            print(f"  keywords: {keywords}")
            sample_count += 1
        if sample_count >= 3:
            break
    
    print(f"\nkeywordsフィールドを持つカードのサンプル: {sample_count}件\n")
    
    # テストクエリ一覧（keywordsフィールドの効果を確認）
    test_queries = [
        "ファンファーレ効果を持つカード",
        "ラストワード効果を持つカード", 
        "コンボ効果を持つカード",
        "ファンファーレカード",
        "ラストワードカード",
        "コンボカード",
        "ファンファーレを持つエルフ",
        "ラストワードかコンボ",
        # 従来の検索と比較
        "エルフクラス",
        "1コスト",
        "シルバーレア"
    ]
    
    print("=== keywords検索テスト ===")
    
    for query in test_queries:
        print(f"\n【クエリ】: {query}")
        print("-" * 50)
        
        try:
            # キーワード分割での検索
            keywords = db_service._split_query_to_keywords(query)
            results = await db_service.filter_search_async(keywords, top_k=5)
            print(f"検索結果 ({len(results)}件): {results}")
            
            # LLM解析も実行（モック環境での動作確認）
            analysis = await db_service._analyze_query_with_llm(query)
            print(f"LLM解析結果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 詳細マッチングテスト ===")
    
    # 特定のカードでマッチング機能をテスト
    test_items = []
    for item in db_service.data_cache:
        keywords = item.get("keywords", [])
        if keywords and len(test_items) < 3:
            test_items.append(item)
    
    for item in test_items:
        print(f"\n【テストカード】: {item.get('name', 'N/A')}")
        print(f"keywords: {item.get('keywords', [])}")
        
        # 各keywordでマッチング試行
        item_keywords = item.get("keywords", [])
        for keyword in item_keywords:
            match_result = await db_service._match_filterable(item, keyword)
            print(f"  '{keyword}' マッチング結果: {match_result}")
            
            # フォールバック版でもテスト
            fallback_result = db_service._match_filterable_fallback(item, keyword)
            print(f"  '{keyword}' フォールバック結果: {fallback_result}")

if __name__ == "__main__":
    asyncio.run(test_keywords_search())
