#!/usr/bin/env python3
"""
「交戦時」キーワード検索の問題を調査するデバッグスクリプト
"""

import os
import sys
import asyncio
import json

# プロジェクトルートを計算してパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'backend'))

try:
    from app.services.database_service import DatabaseService
except ImportError:
    print("DatabaseServiceのインポートに失敗しました。backend/app/services/database_service.py の存在を確認してください。")
    sys.exit(1)

async def debug_kosen_search():
    """交戦時検索の問題をデバッグ"""
    
    # データパスを明示的に設定
    data_path = os.path.join(project_root, 'data/data.json')
    print(f"データファイルパス: {data_path}")
    
    # DatabaseServiceを初期化
    service = DatabaseService(data_path=data_path)
    service.debug = True  # デバッグモードを有効化
    
    print(f"ロードしたデータ数: {len(service.data_cache)}")
    
    # 「交戦時」を含むカードを手動検索
    print("\n=== 手動検索: 「交戦時」を含むカード ===")
    kosen_cards = []
    for item in service.data_cache:
        keywords = item.get("keywords", [])
        if isinstance(keywords, list) and "交戦時" in keywords:
            kosen_cards.append(item)
            print(f"発見: {item.get('name', '')} - keywords: {keywords}")
    
    print(f"\n手動検索結果: {len(kosen_cards)}件")
    
    # 各種検索メソッドをテスト
    test_queries = [
        "交戦時",
        "交戦時に能力を発動するカード",
        "交戦時 カード",
        ["交戦時"]
    ]
    
    for query in test_queries:
        print(f"\n=== テストクエリ: {query} ===")
        
        try:
            if isinstance(query, list):
                # キーワードリスト検索
                print("キーワードリスト検索:")
                result = await service.filter_search_async(query, top_k=10)
                print(f"結果: {result}")
                
                # 同期版キーワード検索
                print("同期版キーワード検索:")
                result_sync = service._filter_search_sync(query, top_k=10)
                print(f"結果: {result_sync}")
                
            else:
                # LLMベース検索
                print("LLMベース検索:")
                result_llm = await service.filter_search_llm_async(query, top_k=10)
                print(f"結果: {result_llm}")
                
                # スマート検索
                print("スマート検索:")
                result_smart = await service.smart_search_llm(query, top_k=10)
                print(f"結果: {result_smart}")
                
                # 統合検索
                print("統合検索:")
                result_unified = await service.smart_filter_search_async(query, top_k=10, use_llm=True)
                print(f"結果: {result_unified}")
                
        except Exception as e:
            print(f"エラー: {e}")
    
    # フォールバック処理をテスト
    print(f"\n=== フォールバック処理テスト ===")
    if kosen_cards:
        test_item = kosen_cards[0]
        print(f"テストアイテム: {test_item.get('name', '')}")
        
        # フォールバック関数を直接テスト
        test_keywords = ["交戦時", "交戦時に能力を発動"]
        for kw in test_keywords:
            result = service._match_filterable_fallback(test_item, kw)
            print(f"フォールバック判定 '{kw}': {result}")
    
    # LLMクエリ解析をテスト
    print(f"\n=== LLMクエリ解析テスト ===")
    try:
        analysis = await service._analyze_query_with_llm("交戦時に能力を発動するカード")
        print(f"LLM解析結果:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
        # LLMマッチング関数をテスト
        if kosen_cards:
            test_item = kosen_cards[0]
            match_result = await service._match_filterable_llm(test_item, analysis)
            print(f"LLMマッチング結果: {match_result}")
            
    except Exception as e:
        print(f"LLM処理エラー: {e}")

if __name__ == "__main__":
    asyncio.run(debug_kosen_search())
