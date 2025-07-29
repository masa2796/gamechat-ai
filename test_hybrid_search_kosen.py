#!/usr/bin/env python3
"""
修正後のハイブリッド検索システム全体をテストするスクリプト
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
    from app.services.hybrid_search_service import HybridSearchService
    from app.models.rag_models import SearchRequest
except ImportError:
    print("ハイブリッド検索サービスのインポートに失敗しました。")
    sys.exit(1)

async def test_hybrid_search_kosen():
    """ハイブリッド検索システム全体で「交戦時」クエリをテスト"""
    
    # データパスを明示的に設定
    data_path = os.path.join(project_root, 'data/data.json')
    print(f"データファイルパス: {data_path}")
    
    # HybridSearchServiceを初期化
    service = HybridSearchService(data_path=data_path)
    print(f"モック環境: {getattr(service.classification_service, 'is_mocked', 'Unknown')}")
    
    # テストクエリ
    test_queries = [
        "交戦時に能力を発動するカード",
        "交戦時能力を持つカード",
        "交戦時カード"
    ]
    
    for query in test_queries:
        print(f"\n=== ハイブリッド検索テスト: {query} ===")
        try:
            request = SearchRequest(query=query, top_k=10)
            result = await service.search(request)
            
            print(f"分類結果:")
            print(f"  - タイプ: {result.classification.query_type}")
            print(f"  - 要約: {result.classification.summary}")
            print(f"  - 信頼度: {result.classification.confidence}")
            print(f"  - フィルターキーワード: {result.classification.filter_keywords}")
            
            print(f"検索戦略:")
            print(f"  - DB検索実行: {result.search_strategy.use_db}")
            print(f"  - ベクトル検索実行: {result.search_strategy.use_vector}")
            print(f"  - マージ戦略: {result.search_strategy.merge_strategy}")
            
            print(f"DB検索結果: {len(result.db_results)}件")
            for i, item in enumerate(result.db_results[:3]):  # 最初の3件のみ表示
                print(f"  {i+1}. {item}")
            
            print(f"ベクトル検索結果: {len(result.vector_results)}件")
            for i, item in enumerate(result.vector_results[:3]):  # 最初の3件のみ表示
                print(f"  {i+1}. {item.title if hasattr(item, 'title') else item}")
            
            print(f"マージ結果: {len(result.merged_results)}件")
            for i, item in enumerate(result.merged_results[:3]):  # 最初の3件のみ表示
                print(f"  {i+1}. {item.title if hasattr(item, 'title') else item}")
            
            # 「交戦時」クエリの期待される結果の判定
            if "交戦時" in query:
                if result.classification.query_type.value == "FILTERABLE":
                    print("✅ 正常: 「交戦時」クエリがFILTERABLEに分類されました")
                else:
                    print("❌ 問題: 「交戦時」クエリがFILTERABLEに分類されませんでした")
                
                if len(result.db_results) > 0:
                    print("✅ 正常: DB検索で結果が見つかりました")
                else:
                    print("❌ 問題: DB検索で結果が見つかりませんでした")
                
                # 「煌翼のフェザーフォルク・リノ」が含まれているかチェック
                found_rino = False
                all_results = result.db_results + [item.title if hasattr(item, 'title') else str(item) for item in result.merged_results]
                for item_name in all_results:
                    if "煌翼のフェザーフォルク・リノ" in str(item_name):
                        found_rino = True
                        break
                
                if found_rino:
                    print("✅ 正常: 期待されるカード「煌翼のフェザーフォルク・リノ」が見つかりました")
                else:
                    print("❌ 問題: 期待されるカード「煌翼のフェザーフォルク・リノ」が見つかりませんでした")
                
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hybrid_search_kosen())
