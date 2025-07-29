#!/usr/bin/env python3
"""
モック環境での「交戦時」キーワード検索をテストするスクリプト
"""

import os
import sys
import asyncio
import json

# プロジェクトルートを計算してパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'backend'))

# モック環境設定
os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"

try:
    from app.services.database_service import DatabaseService
except ImportError:
    print("DatabaseServiceのインポートに失敗しました。")
    sys.exit(1)

async def test_kosen_mock():
    """モック環境での交戦時検索をテスト"""
    
    # データパスを明示的に設定
    data_path = os.path.join(project_root, 'data/data.json')
    print(f"データファイルパス: {data_path}")
    
    # DatabaseServiceを初期化
    service = DatabaseService(data_path=data_path)
    service.debug = True  # デバッグモードを有効化
    
    print(f"ロードしたデータ数: {len(service.data_cache)}")
    print(f"モック環境: {service.is_mocked}")
    
    # 手動で「交戦時」を含むカードを確認
    print("\n=== 手動検索: 「交戦時」を含むカード ===")
    kosen_cards = []
    for item in service.data_cache:
        keywords = item.get("keywords", [])
        if isinstance(keywords, list) and "交戦時" in keywords:
            kosen_cards.append(item)
            print(f"発見: {item.get('name', '')} - keywords: {keywords}")
    
    print(f"手動検索結果: {len(kosen_cards)}件")
    
    # モッククエリ解析をテスト
    print("\n=== モッククエリ解析テスト ===")
    test_query = "交戦時に能力を発動するカード"
    try:
        analysis = await service._analyze_query_with_llm(test_query)
        print(f"クエリ: {test_query}")
        print("モック解析結果:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
        # keywordsフィールドに「交戦時」が含まれているかチェック
        keywords = analysis.get("conditions", {}).get("keywords", [])
        if "交戦時" in keywords:
            print("✅ 正常: keywordsフィールドに「交戦時」が含まれています")
        else:
            print("❌ 問題: keywordsフィールドに「交戦時」が含まれていません")
            print(f"実際のkeywords: {keywords}")
        
        # モック環境でLLMマッチングをテスト
        if kosen_cards and keywords:
            print("\n=== LLMマッチングテスト ===")
            test_item = kosen_cards[0]
            print(f"テストカード: {test_item.get('name', '')}")
            
            match_result = await service._match_filterable_llm(test_item, analysis)
            print(f"マッチング結果: {match_result}")
            
            if match_result:
                print("✅ 正常: カードが正しくマッチしました")
            else:
                print("❌ 問題: カードがマッチしませんでした")
        
        # 検索全体をテスト
        print("\n=== 統合検索テスト ===")
        result = await service.filter_search_llm_async(test_query, top_k=10)
        print(f"検索結果: {result}")
        
        if result:
            print(f"✅ 正常: {len(result)}件のカードが見つかりました")
            for card_name in result:
                print(f"  - {card_name}")
        else:
            print("❌ 問題: カードが見つかりませんでした")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kosen_mock())
