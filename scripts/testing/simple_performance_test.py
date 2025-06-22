#!/usr/bin/env python3
"""
シンプルなパフォーマンステストスクリプト
- 基本的なHTTPリクエストテスト
- レスポンス時間の測定
- エラーハンドリングの確認
標準ライブラリのみを使用
"""
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List
import sys

class SimplePerformanceTest:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
    
    def test_health_endpoint(self) -> Dict[str, Any]:
        """ヘルスチェックエンドポイントをテスト"""
        start_time = time.perf_counter()
        
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                duration = time.perf_counter() - start_time
                
                return {
                    "endpoint": "health",
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200,
                    "response_data": data
                }
        except Exception as e:
            duration = time.perf_counter() - start_time
            return {
                "endpoint": "health",
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    def test_detailed_health_endpoint(self) -> Dict[str, Any]:
        """詳細ヘルスチェックエンドポイントをテスト"""
        start_time = time.perf_counter()
        
        try:
            with urllib.request.urlopen(f"{self.base_url}/health/detailed", timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                duration = time.perf_counter() - start_time
                
                return {
                    "endpoint": "health/detailed",
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200,
                    "database_status": data.get("checks", {}).get("database", {}).get("status"),
                    "storage_status": data.get("checks", {}).get("storage", {}).get("status")
                }
        except Exception as e:
            duration = time.perf_counter() - start_time
            return {
                "endpoint": "health/detailed",
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    def test_rag_endpoint(self, question: str) -> Dict[str, Any]:
        """RAGエンドポイントをテスト"""
        start_time = time.perf_counter()
        
        # リクエストデータを準備
        data = {
            "question": question,
            "top_k": 5,
            "with_context": True,
            "recaptchaToken": "test_token"
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        # HTTPリクエストを作成
        req = urllib.request.Request(
            f"{self.base_url}/api/rag/query",
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(json_data))
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                duration = time.perf_counter() - start_time
                
                return {
                    "endpoint": "rag/query",
                    "question": question,
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200,
                    "response_size": len(json.dumps(response_data)),
                    "has_answer": bool(response_data.get("answer")),
                    "context_count": len(response_data.get("context", []))
                }
        except Exception as e:
            duration = time.perf_counter() - start_time
            return {
                "endpoint": "rag/query",
                "question": question,
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    def run_basic_tests(self) -> List[Dict[str, Any]]:
        """基本的なテストを実行"""
        print("🔍 基本的なパフォーマンステストを開始します...")
        
        # ヘルスチェックテスト
        print("1. ヘルスチェックエンドポイントをテスト中...")
        health_result = self.test_health_endpoint()
        self.results.append(health_result)
        print(f"   - ステータス: {health_result['status']}")
        print(f"   - レスポンス時間: {health_result['duration']:.3f}秒")
        
        # 詳細ヘルスチェックテスト
        print("2. 詳細ヘルスチェックエンドポイントをテスト中...")
        detailed_health_result = self.test_detailed_health_endpoint()
        self.results.append(detailed_health_result)
        print(f"   - ステータス: {detailed_health_result['status']}")
        print(f"   - レスポンス時間: {detailed_health_result['duration']:.3f}秒")
        
        # RAGエンドポイントテスト（サーバーが起動している場合のみ）
        if health_result['success']:
            print("3. RAGエンドポイントをテスト中...")
            test_questions = [
                "ゲームの基本的な遊び方を教えて",
                "最新のアップデート情報は？",
                "初心者向けのアドバイスをください"
            ]
            
            for i, question in enumerate(test_questions):
                print(f"   - テスト質問 {i+1}: {question[:30]}...")
                rag_result = self.test_rag_endpoint(question)
                self.results.append(rag_result)
                print(f"     ステータス: {rag_result['status']}, 時間: {rag_result['duration']:.3f}秒")
        else:
            print("3. サーバーが利用できないため、RAGテストをスキップします")
        
        return self.results
    
    def run_load_test(self, iterations: int = 5) -> Dict[str, Any]:
        """簡単な負荷テストを実行"""
        print(f"\n⚡ 負荷テスト ({iterations}回) を開始します...")
        
        durations = []
        successes = 0
        
        for i in range(iterations):
            print(f"   テスト {i+1}/{iterations}...")
            result = self.test_health_endpoint()
            durations.append(result['duration'])
            if result['success']:
                successes += 1
        
        # 統計を計算
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        success_rate = (successes / iterations) * 100
        
        load_test_result = {
            "test_type": "load_test",
            "iterations": iterations,
            "success_rate": success_rate,
            "average_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "all_durations": durations
        }
        
        print(f"   - 成功率: {success_rate:.1f}%")
        print(f"   - 平均レスポンス時間: {avg_duration:.3f}秒")
        print(f"   - 最短レスポンス時間: {min_duration:.3f}秒")
        print(f"   - 最長レスポンス時間: {max_duration:.3f}秒")
        
        return load_test_result
    
    def print_summary(self):
        """テスト結果のサマリーを表示"""
        print("\n📊 テスト結果サマリー:")
        print("=" * 50)
        
        successful_tests = [r for r in self.results if r.get('success', False)]
        failed_tests = [r for r in self.results if not r.get('success', False)]
        
        print(f"総テスト数: {len(self.results)}")
        print(f"成功: {len(successful_tests)}")
        print(f"失敗: {len(failed_tests)}")
        
        if successful_tests:
            durations = [r['duration'] for r in successful_tests]
            avg_duration = sum(durations) / len(durations)
            print(f"平均レスポンス時間: {avg_duration:.3f}秒")
        
        if failed_tests:
            print("\n❌ 失敗したテスト:")
            for test in failed_tests:
                print(f"   - {test['endpoint']}: {test.get('error', 'Unknown error')}")
        
        print("\n✅ 成功したテスト:")
        for test in successful_tests:
            print(f"   - {test['endpoint']}: {test['duration']:.3f}秒")

def check_server_availability(base_url: str) -> bool:
    """サーバーの可用性をチェック"""
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=5) as response:
            return response.status == 200
    except Exception:
        return False

def main():
    """メイン関数"""
    base_url = "http://127.0.0.1:8000"
    
    print("🚀 シンプルパフォーマンステストツール")
    print("=" * 50)
    print(f"テスト対象: {base_url}")
    
    # サーバーの可用性をチェック
    if not check_server_availability(base_url):
        print(f"❌ サーバー {base_url} にアクセスできません")
        print("サーバーが起動していることを確認してください:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    print("✅ サーバーが利用可能です\n")
    
    # テストを実行
    tester = SimplePerformanceTest(base_url)
    
    # 基本テスト
    tester.run_basic_tests()
    
    # 負荷テスト
    tester.run_load_test(iterations=5)
    
    # サマリー表示
    tester.print_summary()
    
    print("\n🎉 テスト完了!")

if __name__ == "__main__":
    main()
