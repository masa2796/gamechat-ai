#!/usr/bin/env python3
"""
LLM応答生成機能の改修後パフォーマンス測定スクリプト
"""
import time
import requests
import json
from typing import List, Dict, Any

# テストケース
test_cases = [
    {
        "name": "挨拶 - 検索スキップ",
        "question": "こんにちは！",
        "expected_skip": True
    },
    {
        "name": "単純なセマンティック検索",
        "question": "ピカチュウの情報を教えて",
        "expected_skip": False
    },
    {
        "name": "複雑なフィルター検索",
        "question": "HP100以上の炎タイプのカードを教えて",
        "expected_skip": False
    },
    {
        "name": "挨拶2 - 検索スキップ",
        "question": "おはよう",
        "expected_skip": True
    },
    {
        "name": "具体的な質問",
        "question": "リザードンの技を教えて",
        "expected_skip": False
    }
]

def test_api_performance():
    """APIパフォーマンステスト"""
    base_url = "http://127.0.0.1:8000/api/rag/query"
    results = []
    
    print("🚀 LLM応答生成機能 パフォーマンステスト開始")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 テスト {i}/{len(test_cases)}: {test_case['name']}")
        print(f"質問: {test_case['question']}")
        
        # API呼び出し時間測定
        start_time = time.time()
        
        response = requests.post(
            base_url,
            json={
                "question": test_case['question'],
                "top_k": 5,
                "with_context": True,
                "recaptchaToken": "test_token"
            },
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # 検索スキップ確認
            search_skipped = (
                data.get("classification", {}).get("query_type") == "greeting" and
                data.get("search_info", {}).get("db_results_count", 0) == 0 and
                data.get("search_info", {}).get("vector_results_count", 0) == 0
            )
            
            skip_match = search_skipped == test_case['expected_skip']
            
            result = {
                "test_name": test_case['name'],
                "question": test_case['question'],
                "response_time": response_time,
                "search_skipped": search_skipped,
                "skip_expected": test_case['expected_skip'],
                "skip_match": skip_match,
                "answer_length": len(data.get("answer", "")),
                "context_count": len(data.get("context", [])),
                "classification": data.get("classification", {}),
                "search_info": data.get("search_info", {})
            }
            
            results.append(result)
            
            print(f"⏱️  応答時間: {response_time:.3f}秒")
            print(f"🔍 検索スキップ: {search_skipped} (期待値: {test_case['expected_skip']}) {'✅' if skip_match else '❌'}")
            print(f"📝 回答文字数: {result['answer_length']}文字")
            print(f"📚 コンテキスト数: {result['context_count']}件")
            
        else:
            print(f"❌ エラー: {response.status_code} - {response.text}")
            
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    if results:
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        greeting_tests = [r for r in results if r["skip_expected"]]
        non_greeting_tests = [r for r in results if not r["skip_expected"]]
        
        print(f"全体平均応答時間: {avg_response_time:.3f}秒")
        
        if greeting_tests:
            avg_greeting_time = sum(r["response_time"] for r in greeting_tests) / len(greeting_tests)
            print(f"挨拶応答平均時間: {avg_greeting_time:.3f}秒 (検索スキップ)")
            
        if non_greeting_tests:
            avg_search_time = sum(r["response_time"] for r in non_greeting_tests) / len(non_greeting_tests)
            print(f"検索応答平均時間: {avg_search_time:.3f}秒")
            
        # 検索スキップ精度
        skip_accuracy = sum(1 for r in results if r["skip_match"]) / len(results)
        print(f"検索スキップ精度: {skip_accuracy:.1%}")
        
        # 応答品質指標
        print(f"\n📈 応答品質指標:")
        for result in results:
            print(f"  {result['test_name']}: {result['answer_length']}文字, {result['context_count']}コンテキスト")
    
    return results

if __name__ == "__main__":
    try:
        results = test_api_performance()
        
        # 結果をJSONファイルに保存
        with open("/Users/masaki/Documents/gamechat-ai/performance_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 詳細結果を performance_results.json に保存しました")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
