#!/usr/bin/env python3
"""「疾走を持つカード」クエリの詳細デバッグ"""

import sys
import os
sys.path.append('backend')
os.environ["BACKEND_TESTING"] = "true"
os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"

from backend.app.services.database_service import DatabaseService

def debug_query_issue():
    """「疾走を持つカード」クエリのデバッグ"""
    
    # デバッグモードを有効化
    db_service = DatabaseService()
    db_service.debug = True  # デバッグモードON
    db_service.reload_data()
    
    print("=== 疾走・守護クエリのデバッグ ===")
    print(f'データ件数: {len(db_service.data_cache)}')
    
    # まず、疾走・守護キーワードを持つカードが実際に存在するか確認
    print("\n=== 疾走・守護キーワードを持つカードの確認 ===")
    haste_cards = []
    guard_cards = []
    
    for item in db_service.data_cache:
        keywords = item.get('keywords', [])
        if '疾走' in keywords:
            haste_cards.append(item.get('name', ''))
        if '守護' in keywords:
            guard_cards.append(item.get('name', ''))
    
    print(f"疾走キーワードを持つカード数: {len(haste_cards)}")
    print(f"疾走カード例: {haste_cards[:3]}")
    print(f"守護キーワードを持つカード数: {len(guard_cards)}")
    print(f"守護カード例: {guard_cards[:3]}")
    
    # 問題のクエリをテスト
    test_queries = [
        "疾走を持つカード",
        "守護を持つカード",
        "疾走",
        "守護"
    ]
    
    for query in test_queries:
        print(f"\n=== クエリ「{query}」のテスト ===")
        
        # 1. LLMベース検索のテスト
        print("【LLMベース検索】")
        try:
            result = db_service.filter_search_llm(query, top_k=3)
            print(f"結果: {result}")
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
        
        # 2. キーワードベース検索のテスト
        print("【キーワードベース検索】")
        try:
            result = db_service.filter_search([query], top_k=3)
            print(f"結果: {result}")
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
        
        # 3. LLMクエリ解析の詳細確認
        print("【LLMクエリ解析結果】")
        try:
            analysis = db_service._get_mock_query_analysis(query)
            print(f"解析結果: {analysis}")
        except Exception as e:
            print(f"解析エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_query_issue()
