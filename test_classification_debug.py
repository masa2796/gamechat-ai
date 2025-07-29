#!/usr/bin/env python3
"""
分類サービスの「交戦時」キーワード検出をテストするスクリプト
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
    from app.services.classification_service import ClassificationService
    from app.models.classification_models import ClassificationRequest
except ImportError:
    print("分類サービスのインポートに失敗しました。")
    sys.exit(1)

async def test_classification_debug():
    """分類サービスの交戦時キーワード検出をテスト"""
    
    # ClassificationServiceを初期化
    service = ClassificationService()
    print(f"モック環境: {service.is_mocked}")
    
    # テストクエリ
    test_queries = [
        "交戦時に能力を発動するカード",
        "交戦時",
        "交戦時能力を持つカード",
        "交戦時カード",
        "ファンファーレカード",  # 比較用
        "HP100以上のカード"  # 比較用
    ]
    
    for query in test_queries:
        print(f"\n=== テストクエリ: {query} ===")
        try:
            request = ClassificationRequest(query=query)
            result = await service.classify_query(request)
            print(f"分類タイプ: {result.query_type}")
            print(f"要約: {result.summary}")
            print(f"信頼度: {result.confidence}")
            print(f"フィルターキーワード: {result.filter_keywords}")
            print(f"検索キーワード: {result.search_keywords}")
            print(f"理由: {result.reasoning}")
            
            # 期待される結果の判定
            if "交戦時" in query and result.query_type.value == "FILTERABLE":
                print("✅ 正常: 「交戦時」クエリがFILTERABLEに分類されました")
            elif "交戦時" in query:
                print("❌ 問題: 「交戦時」クエリがFILTERABLEに分類されませんでした")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_classification_debug())
