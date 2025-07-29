#!/usr/bin/env python3
"""
RAGサービス全体で「交戦時」クエリをテストするスクリプト
"""

import os
import sys
import asyncio

# プロジェクトルートを計算してパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'backend'))

# モック環境設定
os.environ["BACKEND_MOCK_EXTERNAL_SERVICES"] = "true"

try:
    from app.services.rag_service import RagService
    from app.models.rag_models import RagRequest
except ImportError:
    print("RAGサービスのインポートに失敗しました。")
    sys.exit(1)

async def test_rag_kosen():
    """RAGサービス全体で「交戦時」クエリをテスト"""
    
    print("RAGサービステストを開始します...")
    
    # RAGServiceを初期化
    service = RagService()
    
    # テストクエリ
    test_queries = [
        "交戦時に能力を発動するカード",
        "交戦時能力を持つカード"
    ]
    
    for query in test_queries:
        print(f"\n=== RAG検索テスト: {query} ===")
        try:
            request = RagRequest(question=query, top_k=10, with_context=True)
            result = await service.process_query(request)
            
            print("レスポンス内容:")
            print(f"  - メッセージキー: {list(result.keys())}")
            
            # 分類結果
            classification = result.get('classification')
            if classification:
                print(f"  - 分類タイプ: {classification.get('query_type', 'N/A')}")
                print(f"  - 分類要約: {classification.get('summary', 'N/A')}")
                print(f"  - 信頼度: {classification.get('confidence', 'N/A')}")
                print(f"  - フィルターキーワード: {classification.get('filter_keywords', [])}")
            
            # コンテキスト
            context = result.get('context', [])
            print(f"  - コンテキスト件数: {len(context)}")
            
            # コンテキストに期待されるカードが含まれているかチェック
            found_rino = False
            for item in context:
                if isinstance(item, dict):
                    name = item.get('name', '')
                    if "煌翼のフェザーフォルク・リノ" in name:
                        found_rino = True
                        break
                elif isinstance(item, str) and "煌翼のフェザーフォルク・リノ" in item:
                    found_rino = True
                    break
            
            # 結果評価
            if "交戦時" in query:
                if classification and classification.get('query_type') == 'FILTERABLE':
                    print("✅ 正常: 「交戦時」クエリがFILTERABLEに分類されました")
                else:
                    print("❌ 問題: 「交戦時」クエリがFILTERABLEに分類されませんでした")
                    print(f"    実際の分類: {classification.get('query_type') if classification else 'None'}")
                
                if len(context) > 0:
                    print("✅ 正常: 検索結果が見つかりました")
                else:
                    print("❌ 問題: 検索結果が見つかりませんでした")
                
                if found_rino:
                    print("✅ 正常: 期待されるカード「煌翼のフェザーフォルク・リノ」が見つかりました")
                else:
                    print("❌ 問題: 期待されるカード「煌翼のフェザーフォルク・リノ」が見つかりませんでした")
                    print("コンテキスト一覧:")
                    for i, item in enumerate(context[:5]):  # 最初の5件のみ表示
                        if isinstance(item, dict):
                            print(f"  {i+1}. {item.get('name', 'No name')}")
                        else:
                            print(f"  {i+1}. {item}")
                
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_kosen())
