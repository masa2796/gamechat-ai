#!/usr/bin/env python3
"""
パフォーマンス最適化問題解決用テストスクリプト
- 30秒以上のタイムアウト問題の測定
- 5秒以内の目標達成率チェック
- ボトルネック特定のための詳細プロファイリング
- キャッシュ効果の測定
- 並列処理テスト
標準ライブラリのみを使用
"""
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from locust import HttpUser, task
from typing import Dict, Any, List
import sys

class PerformanceOptimizationTest:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        self.timeout_threshold = 30.0  # 30秒タイムアウト閾値
        self.target_response_time = 5.0  # 5秒目標
        self.cache_test_results: List[Dict[str, Any]] = []
    
    def measure_detailed_timing(self, func, *args, **kwargs) -> Dict[str, Any]:
        """詳細なタイミング測定"""
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            total_duration = end_time - start_time
            
            return {
                "result": result,
                "total_duration": total_duration,
                "exceeds_target": total_duration > self.target_response_time,
                "exceeds_timeout": total_duration > self.timeout_threshold,
                "performance_grade": self._grade_performance(total_duration)
            }
        except Exception as e:
            end_time = time.perf_counter()
            total_duration = end_time - start_time
            return {
                "result": None,
                "error": str(e),
                "total_duration": total_duration,
                "exceeds_target": total_duration > self.target_response_time,
                "exceeds_timeout": total_duration > self.timeout_threshold,
                "performance_grade": "FAILED"
            }
    
    def _grade_performance(self, duration: float) -> str:
        """パフォーマンスをグレード評価"""
        if duration <= 1.0:
            return "EXCELLENT"
        elif duration <= 3.0:
            return "GOOD"
        elif duration <= 5.0:
            return "ACCEPTABLE"
        elif duration <= 10.0:
            return "POOR"
        elif duration <= 30.0:
            return "CRITICAL"
        else:
            return "TIMEOUT"
    
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
        
        # HTTPリクエストを作成（APIキー付き）
        req = urllib.request.Request(
            f"{self.base_url}/api/rag/query",
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(json_data)),
                'X-API-Key': 'dev-key-12345'  # 開発用APIキー
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
    
    def test_rag_endpoint_with_profiling(self, question: str, timeout: int = 35) -> Dict[str, Any]:
        """RAGエンドポイントをプロファイリング付きでテスト"""
        
        def make_rag_request():
            # リクエストデータを準備
            data = {
                "question": question,
                "top_k": 5,
                "with_context": True,
                "recaptchaToken": "test_token"
            }
            
            json_data = json.dumps(data).encode('utf-8')
            
            # HTTPリクエストを作成（APIキー付き）
            req = urllib.request.Request(
                f"{self.base_url}/api/rag/query",
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'Content-Length': str(len(json_data)),
                    'X-API-Key': 'dev-key-12345'  # 開発用APIキー
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                return {
                    "endpoint": "rag/query",
                    "question": question,
                    "status": response.status,
                    "success": response.status == 200,
                    "response_size": len(json.dumps(response_data)),
                    "has_answer": bool(response_data.get("answer")),
                    "context_count": len(response_data.get("context", [])),
                    "cache_hit": response_data.get("performance", {}).get("cache_hit", False),
                    "response_data": response_data
                }
        
        # 詳細タイミング測定を実行
        timing_result = self.measure_detailed_timing(make_rag_request)
        
        if timing_result["result"]:
            result = timing_result["result"]
            result.update({
                "duration": timing_result["total_duration"],
                "exceeds_target": timing_result["exceeds_target"],
                "exceeds_timeout": timing_result["exceeds_timeout"],
                "performance_grade": timing_result["performance_grade"]
            })
            return result
        else:
            return {
                "endpoint": "rag/query",
                "question": question,
                "status": 0,
                "duration": timing_result["total_duration"],
                "success": False,
                "error": timing_result.get("error", "Unknown error"),
                "exceeds_target": timing_result["exceeds_target"],
                "exceeds_timeout": timing_result["exceeds_timeout"],
                "performance_grade": timing_result["performance_grade"]
            }
    
    def test_cache_effectiveness(self) -> Dict[str, Any]:
        """キャッシュ効果をテスト"""
        print("🔄 キャッシュ効果をテスト中...", flush=True)
        
        test_question = "ゲームの基本的な遊び方を教えて"
        
        # 1回目のリクエスト（キャッシュなし）
        print("   - 1回目のリクエスト（キャッシュなし）...", flush=True)
        first_result = self.test_rag_endpoint_with_profiling(test_question)
        
        # 少し待機
        time.sleep(0.5)
        
        # 2回目のリクエスト（キャッシュあり期待）
        print("   - 2回目のリクエスト（キャッシュあり期待）...", flush=True)
        second_result = self.test_rag_endpoint_with_profiling(test_question)
        
        cache_improvement = 0
        if first_result['success'] and second_result['success']:
            cache_improvement = ((first_result['duration'] - second_result['duration']) / first_result['duration']) * 100
        
        cache_test_result = {
            "test_type": "cache_effectiveness",
            "first_request": {
                "duration": first_result.get('duration', 0),
                "cache_hit": first_result.get('cache_hit', False),
                "success": first_result.get('success', False)
            },
            "second_request": {
                "duration": second_result.get('duration', 0),
                "cache_hit": second_result.get('cache_hit', False),
                "success": second_result.get('success', False)
            },
            "cache_improvement_percent": cache_improvement,
            "cache_working": second_result.get('cache_hit', False) or cache_improvement > 10
        }
        
        self.cache_test_results.append(cache_test_result)
        
        print(f"   - 1回目: {first_result.get('duration', 0):.3f}秒", flush=True)
        print(f"   - 2回目: {second_result.get('duration', 0):.3f}秒", flush=True)
        print(f"   - キャッシュ改善: {cache_improvement:.1f}%", flush=True)
        
        return cache_test_result

    def run_basic_tests(self) -> List[Dict[str, Any]]:
        """基本的なテストを実行"""
        print("🔍 基本的なパフォーマンステストを開始します...", flush=True)
        
        # ヘルスチェックテスト
        print("1. ヘルスチェックエンドポイントをテスト中...", flush=True)
        health_result = self.test_health_endpoint()
        self.results.append(health_result)
        print(f"   - ステータス: {health_result['status']}", flush=True)
        print(f"   - レスポンス時間: {health_result['duration']:.3f}秒", flush=True)
        
        # 詳細ヘルスチェックテスト
        print("2. 詳細ヘルスチェックエンドポイントをテスト中...", flush=True)
        detailed_health_result = self.test_detailed_health_endpoint()
        self.results.append(detailed_health_result)
        print(f"   - ステータス: {detailed_health_result['status']}", flush=True)
        print(f"   - レスポンス時間: {detailed_health_result['duration']:.3f}秒", flush=True)
        
        # RAGエンドポイントテスト（サーバーが起動している場合のみ）
        if health_result['success']:
            print("3. RAGエンドポイントをテスト中...", flush=True)
            test_questions = [
                "ゲームの基本的な遊び方を教えて",
                "最新のアップデート情報は？",
                "初心者向けのアドバイスをください"
            ]
            
            for i, question in enumerate(test_questions):
                print(f"   - テスト質問 {i+1}: {question[:30]}...", flush=True)
                rag_result = self.test_rag_endpoint(question)
                self.results.append(rag_result)
                print(f"     ステータス: {rag_result['status']}, 時間: {rag_result['duration']:.3f}秒", flush=True)
        else:
            print("3. サーバーが利用できないため、RAGテストをスキップします", flush=True)
        
        return self.results
    
    def run_load_test(self, iterations: int = 5) -> Dict[str, Any]:
        """簡単な負荷テストを実行"""
        print(f"\n⚡ 負荷テスト ({iterations}回) を開始します...")
        
        durations = []
        successes = 0
        
        for i in range(iterations):
            print(f"   テスト {i+1}/{iterations}...", flush=True)
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
        
        print(f"   - 成功率: {success_rate:.1f}%", flush=True)
        print(f"   - 平均レスポンス時間: {avg_duration:.3f}秒", flush=True)
        print(f"   - 最短レスポンス時間: {min_duration:.3f}秒", flush=True)
        print(f"   - 最長レスポンス時間: {max_duration:.3f}秒", flush=True)
        
        return load_test_result
    
    def print_summary(self):
        """テスト結果のサマリーを表示"""
        print("\n📊 テスト結果サマリー:", flush=True)
        print("=" * 50, flush=True)
        
        successful_tests = [r for r in self.results if r.get('success', False)]
        failed_tests = [r for r in self.results if not r.get('success', False)]
        
        print(f"総テスト数: {len(self.results)}", flush=True)
        print(f"成功: {len(successful_tests)}", flush=True)
        print(f"失敗: {len(failed_tests)}", flush=True)
        
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
    
    def run_timeout_analysis(self) -> Dict[str, Any]:
        """30秒タイムアウト問題の詳細分析"""
        print("⏰ タイムアウト問題の詳細分析を開始...")
        
        test_questions = [
            "ゲームの基本的な遊び方を教えて",
            "最新のアップデート情報は？", 
            "初心者向けのアドバイスをください",
            "上級者向けの戦略を教えて",
            "ゲーム内のアイテムについて詳しく説明して",
            "コミュニティ機能の使い方は？",
            "トラブルシューティング方法を教えて",
            "ゲームの歴史について教えて"
        ]
        
        timeout_results = []
        target_achieved_count = 0
        timeout_exceeded_count = 0
        
        for i, question in enumerate(test_questions):
            print(f"   - テスト {i+1}/{len(test_questions)}: {question[:40]}...")
            
            result = self.test_rag_endpoint_with_profiling(question, timeout=35)
            timeout_results.append(result)
            
            if result['success']:
                if not result['exceeds_target']:
                    target_achieved_count += 1
                if result['exceeds_timeout']:
                    timeout_exceeded_count += 1
                    
                print(f"     時間: {result['duration']:.3f}秒, グレード: {result['performance_grade']}")
            else:
                timeout_exceeded_count += 1
                print(f"     エラー: {result.get('error', 'Unknown')}")
        
        # 統計計算
        successful_tests = [r for r in timeout_results if r['success']]
        total_tests = len(test_questions)
        success_rate = (len(successful_tests) / total_tests) * 100
        target_achievement_rate = (target_achieved_count / total_tests) * 100
        timeout_rate = (timeout_exceeded_count / total_tests) * 100
        
        durations = [r['duration'] for r in successful_tests]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        analysis_result = {
            "test_type": "timeout_analysis",
            "total_tests": total_tests,
            "successful_tests": len(successful_tests),
            "success_rate": success_rate,
            "target_achievement_rate": target_achievement_rate,
            "timeout_rate": timeout_rate,
            "average_duration": avg_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
            "performance_grades": {
                "EXCELLENT": len([r for r in successful_tests if r['performance_grade'] == 'EXCELLENT']),
                "GOOD": len([r for r in successful_tests if r['performance_grade'] == 'GOOD']),
                "ACCEPTABLE": len([r for r in successful_tests if r['performance_grade'] == 'ACCEPTABLE']),
                "POOR": len([r for r in successful_tests if r['performance_grade'] == 'POOR']),
                "CRITICAL": len([r for r in successful_tests if r['performance_grade'] == 'CRITICAL']),
                "TIMEOUT": len([r for r in timeout_results if r['performance_grade'] == 'TIMEOUT'])
            },
            "detailed_results": timeout_results
        }
        
        print("\n📊 タイムアウト分析結果:")
        print(f"   - 成功率: {success_rate:.1f}%")
        print(f"   - 5秒以内達成率: {target_achievement_rate:.1f}%")
        print(f"   - タイムアウト率: {timeout_rate:.1f}%")
        print(f"   - 平均レスポンス時間: {avg_duration:.3f}秒")
        print(f"   - 最長レスポンス時間: {max_duration:.3f}秒")
        
        return analysis_result
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """パフォーマンス改善問題の達成率レポート生成"""
        print("\n📋 パフォーマンス改善問題の達成率を評価中...")
        
        # タイムアウト分析実行
        timeout_analysis = self.run_timeout_analysis()
        
        # キャッシュ効果テスト
        cache_analysis = self.test_cache_effectiveness()
        
        # 問題解決状況の評価
        issues_status = {
            "レスポンス時間問題の根本解決": {
                "目標": "全クエリ5秒以内",
                "現状": f"{timeout_analysis['target_achievement_rate']:.1f}%達成",
                "達成率": timeout_analysis['target_achievement_rate'],
                "status": "RESOLVED" if timeout_analysis['target_achievement_rate'] >= 90 else 
                         "IN_PROGRESS" if timeout_analysis['target_achievement_rate'] >= 50 else "NOT_RESOLVED"
            },
            "30秒タイムアウト問題": {
                "目標": "30秒以上のタイムアウト0%",
                "現状": f"タイムアウト率 {timeout_analysis['timeout_rate']:.1f}%",
                "達成率": 100 - timeout_analysis['timeout_rate'],
                "status": "RESOLVED" if timeout_analysis['timeout_rate'] == 0 else 
                         "IN_PROGRESS" if timeout_analysis['timeout_rate'] < 20 else "NOT_RESOLVED"
            },
            "キャッシュ機構の導入": {
                "目標": "キャッシュによる高速化",
                "現状": f"キャッシュ改善 {cache_analysis['cache_improvement_percent']:.1f}%",
                "達成率": min(100, cache_analysis['cache_improvement_percent'] * 2),  # 50%改善で100%達成とする
                "status": "RESOLVED" if cache_analysis['cache_working'] else "NOT_RESOLVED"
            }
        }
        
        # 全体的な達成率計算
        total_achievement = sum(issue['達成率'] for issue in issues_status.values()) / len(issues_status)
        
        report = {
            "timestamp": time.time(),
            "overall_achievement_rate": total_achievement,
            "individual_issues": issues_status,
            "timeout_analysis": timeout_analysis,
            "cache_analysis": cache_analysis,
            "recommendations": self._generate_recommendations(timeout_analysis, cache_analysis)
        }
        
        print(f"\n🎯 全体達成率: {total_achievement:.1f}%")
        print("\n📋 個別問題の状況:")
        for issue_name, issue_data in issues_status.items():
            status_emoji = "✅" if issue_data['status'] == "RESOLVED" else "🔄" if issue_data['status'] == "IN_PROGRESS" else "❌"
            print(f"   {status_emoji} {issue_name}")
            print(f"      目標: {issue_data['目標']}")
            print(f"      現状: {issue_data['現状']}")
            print(f"      達成率: {issue_data['達成率']:.1f}%")
        
        return report
    
    def _generate_recommendations(self, timeout_analysis: Dict[str, Any], cache_analysis: Dict[str, Any]) -> List[str]:
        """改善提案を生成"""
        recommendations = []
        
        if timeout_analysis['target_achievement_rate'] < 90:
            recommendations.append("RAGクエリの応答時間が目標を下回っています。Vector検索の最適化が必要です。")
        
        if timeout_analysis['timeout_rate'] > 0:
            recommendations.append("30秒以上のタイムアウトが発生しています。クエリタイムアウトの設定と処理の非同期化が必要です。")
        
        if not cache_analysis['cache_working']:
            recommendations.append("キャッシュ機構が効果的に動作していません。Redis設定とキャッシュ戦略の見直しが必要です。")
        
        if timeout_analysis['average_duration'] > 3.0:
            recommendations.append("平均応答時間が3秒を超えています。データベースクエリとインデックスの最適化を検討してください。")
        
        if recommendations:
            recommendations.append("Cloud Runのインスタンス設定（CPU/メモリ）の見直しも検討してください。")
        
        return recommendations

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
    
    print("🚀 パフォーマンス最適化問題解決テストツール")
    print("=" * 60)
    print(f"テスト対象: {base_url}")
    print("目標: 30秒タイムアウト問題の解決と5秒以内レスポンス達成")
    
    # サーバーの可用性をチェック
    if not check_server_availability(base_url):
        print(f"❌ サーバー {base_url} にアクセスできません")
        print("サーバーが起動していることを確認してください:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    print("✅ サーバーが利用可能です\n")
    
    # テストを実行
    tester = PerformanceOptimizationTest(base_url)
    
    # パフォーマンス改善問題の達成率レポート生成
    print("🎯 パフォーマンス改善問題の達成率を評価します...")
    report = tester.generate_performance_report()
    
    # 改善提案の表示
    if report["recommendations"]:
        print("\n💡 改善提案:")
        for i, recommendation in enumerate(report["recommendations"], 1):
            print(f"   {i}. {recommendation}")
    
    # 詳細分析結果の保存（オプション）
    try:
        with open("performance_analysis_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("\n📄 詳細レポートが performance_analysis_report.json に保存されました")
    except Exception as e:
        print(f"\n⚠️ レポート保存に失敗: {e}")
    
    # 基本テストも実行（オプション）
    print("\n" + "="*60)
    print("🔍 基本的なテストも実行します...")
    tester.run_basic_tests()
    
    # 負荷テスト
    tester.run_load_test(iterations=3)
    
    # 最終サマリー
    print("\n" + "="*60)
    print("📊 最終評価:")
    print(f"   🎯 全体達成率: {report['overall_achievement_rate']:.1f}%")
    
    if report['overall_achievement_rate'] >= 80:
        print("   ✅ パフォーマンス問題の大部分が解決されています！")
    elif report['overall_achievement_rate'] >= 50:
        print("   🔄 パフォーマンス改善が進んでいますが、さらなる最適化が必要です。")
    else:
        print("   ❌ パフォーマンス問題が深刻です。緊急の対応が必要です。")
    
    print("\n🎉 テスト完了!")

if __name__ == "__main__":
    main()

class PerformanceUser(HttpUser):
    host = "http://127.0.0.1:8000"

    @task
    def rag_query(self):
        data = {
            "question": "ゲームの基本的な遊び方を教えて",
            "top_k": 5,
            "with_context": True,
            "recaptchaToken": "test_token"
        }
        self.client.post("/api/rag/query", json=data, headers={"X-API-Key": "dev-key-12345"})
