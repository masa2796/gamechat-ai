#!/usr/bin/env python3
"""
挨拶検出と早期応答生成のテストスクリプト（改良版）
"""
import asyncio
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.rag_service import RagService
from backend.app.services.hybrid_search_service import HybridSearchService
from backend.app.services.llm_service import LLMService
from backend.app.models.rag_models import RagRequest
from backend.app.models.classification_models import QueryType

async def test_greeting_detection():
    """挨拶検出と早期応答の統合テスト"""
    
    print("🎉 挨拶検出システムのテスト開始（改良版）")
    print("=" * 50)
    
    rag_service = RagService()
    hybrid_search = HybridSearchService()
    llm_service = LLMService()
    
    # 挨拶パターンのテストケース
    greeting_test_cases = [
        "こんにちは",
        "おはようございます",
        "こんばんは",
        "ありがとうございます",
        "よろしくお願いします",
        "お疲れ様です",
        "元気ですか？",
        "今日はいい天気ですね"
    ]
    
    for i, greeting in enumerate(greeting_test_cases, 1):
        print(f"\n--- テストケース {i}: {greeting} ---")
        
        try:
            # RAGリクエストを作成
            rag_request = RagRequest(
                question=greeting,
                top_k=3,
                with_context=True
            )
            
            # 処理開始時間を記録
            import time
            start_time = time.time()
            
            # RAG処理実行
            result = await rag_service.process_query(rag_request)
            
            # 処理時間を計算
            processing_time = time.time() - start_time
            
            print(f"✅ 応答: {result['answer']}")
            print(f"⏱️  処理時間: {processing_time:.3f}秒")
            
            # 分類情報とコンテキストを確認
            if 'classification' in result:
                classification = result['classification']
                print(f"📊 分類タイプ: {classification['query_type']}")
                print(f"📊 信頼度: {classification['confidence']:.2f}")
                
            if 'search_info' in result:
                search_info = result['search_info']
                print(f"🔍 DB検索結果数: {search_info.get('db_results_count', 0)}")
                print(f"🔍 ベクトル検索結果数: {search_info.get('vector_results_count', 0)}")
                
            # コンテキストが空であることを確認（検索がスキップされたことを示す）
            if 'context' in result:
                context_count = len(result['context'])
                print(f"📄 コンテキスト件数: {context_count}")
                if context_count == 0:
                    print("✅ 検索がスキップされました（期待される動作）")
                else:
                    print("⚠️  検索が実行されました（予期しない動作）")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 検索が必要な質問のテスト")
    
    # 対照群として検索が必要な質問もテスト
    search_test_cases = [
        "リザードンexについて教えて",
        "HPが100以上のポケモンを教えて",
        "強いカードを教えて"
    ]
    
    for i, question in enumerate(search_test_cases, 1):
        print(f"\n--- 検索テストケース {i}: {question} ---")
        
        try:
            rag_request = RagRequest(
                question=question,
                top_k=3,
                with_context=True
            )
            
            start_time = time.time()
            result = await rag_service.process_query(rag_request)
            processing_time = time.time() - start_time
            
            print(f"✅ 応答: {result['answer'][:100]}..." if len(result['answer']) > 100 else f"✅ 応答: {result['answer']}")
            print(f"⏱️  処理時間: {processing_time:.3f}秒")
            
            if 'classification' in result:
                classification = result['classification']
                print(f"📊 分類タイプ: {classification['query_type']}")
                
            if 'search_info' in result:
                search_info = result['search_info']
                db_count = search_info.get('db_results_count', 0)
                vector_count = search_info.get('vector_results_count', 0)
                print(f"🔍 DB検索結果数: {db_count}")
                print(f"🔍 ベクトル検索結果数: {vector_count}")
                
                if db_count > 0 or vector_count > 0:
                    print("✅ 検索が実行されました（期待される動作）")
                else:
                    print("⚠️  検索がスキップされました（予期しない動作）")
                    
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print("\n" + "=" * 50)
    print("🎊 挨拶検出システムのテスト完了")

if __name__ == "__main__":
    asyncio.run(test_greeting_detection())
