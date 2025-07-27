#!/usr/bin/env python3
"""
LLMベースの拡張検索機能のテストスクリプト
"""

import asyncio
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.database_service import DatabaseService

async def test_llm_enhanced_search():
    """LLMベースの拡張検索機能をテスト"""
    print("=== LLMベースの拡張検索機能テスト ===\n")
    
    # DatabaseServiceを初期化（テスト環境用）
    db_service = DatabaseService()
    db_service.is_mocked = True  # モック環境でテスト
    db_service.debug = True      # デバッグ出力を有効化
    
    # データを読み込み
    db_service.reload_data()
    print(f"データ件数: {len(db_service.data_cache)}")
    
    # テストクエリ一覧
    test_queries = [
        "5コストのレジェンドカード",
        "HP100以上のカード", 
        "ダメージが40以上の技を持つカード",
        "水タイプのカード",
        "エルフクラスで攻撃30以上",
        "進化を持つゴールドレア",
        "コスト3以下でHPが50以上",
        "守護効果を持つビショップ"
    ]
    
    print("\n=== 従来の検索（キーワード分割）vs LLM統合検索 ===")
    
    for query in test_queries:
        print(f"\n【クエリ】: {query}")
        print("-" * 50)
        
        try:
            # 1. 従来の検索（キーワード分割）
            keywords = db_service._split_query_to_keywords(query)
            traditional_results = await db_service.filter_search_async(keywords, top_k=5)
            print(f"従来の検索結果 ({len(traditional_results)}件): {traditional_results}")
            
            # 2. LLM統合検索
            llm_results = await db_service.smart_search_llm(query, top_k=5)
            print(f"LLM統合検索結果 ({len(llm_results)}件): {llm_results}")
            
            # 3. LLMクエリ解析の結果を確認
            analysis = await db_service._analyze_query_with_llm(query)
            print(f"LLM解析結果: {analysis}")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 詳細条件テスト ===")
    
    # より複雑な条件のテスト
    complex_queries = [
        "攻撃力が50以上で体力も50以上のカード",
        "3コスト以下の炎タイプで疾走を持つカード", 
        "レジェンドかつエルフクラスで進化効果があるカード",
        "コスト5以上のドラゴンクラスでHPが80以上"
    ]
    
    for query in complex_queries:
        print(f"\n【複雑クエリ】: {query}")
        print("-" * 60)
        
        try:
            # LLM解析のみを実行して構造を確認
            analysis = await db_service._analyze_query_with_llm(query)
            print(f"解析結果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
            
            # 検索実行
            results = await db_service.smart_search_llm(query, top_k=3)
            print(f"検索結果 ({len(results)}件): {results}")
            
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    import json
    asyncio.run(test_llm_enhanced_search())
