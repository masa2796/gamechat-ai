#!/usr/bin/env python3
"""
GameChat AI 設定診断ツール

環境変数の設定状況を確認し、問題があれば修正方法を提案します。
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートに移動
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# .envファイルを読み込み
load_dotenv()

def check_api_keys():
    """APIキーの設定状況をチェック"""
    print("🔑 APIキー設定チェック")
    print("=" * 50)
    
    issues = []
    
    # OpenAI APIキー
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY: 未設定")
        issues.append("OPENAI_API_KEY が設定されていません")
    elif openai_key in ["your_openai_api_key", "your_actual_openai_api_key_here"]:
        print("❌ OPENAI_API_KEY: プレースホルダ値")
        issues.append("OPENAI_API_KEY がプレースホルダ値のままです")
    elif not openai_key.startswith("sk-"):
        print("❌ OPENAI_API_KEY: 無効な形式")
        issues.append("OPENAI_API_KEY の形式が正しくありません（sk-で始まる必要があります）")
    else:
        print(f"✅ OPENAI_API_KEY: 設定済み ({openai_key[:10]}...)")
    
    # Upstash Vector URL
    upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
    if not upstash_url:
        print("❌ UPSTASH_VECTOR_REST_URL: 未設定")
        issues.append("UPSTASH_VECTOR_REST_URL が設定されていません")
    elif upstash_url in ["your_upstash_vector_url", "your_actual_upstash_vector_url_here"]:
        print("❌ UPSTASH_VECTOR_REST_URL: プレースホルダ値")
        issues.append("UPSTASH_VECTOR_REST_URL がプレースホルダ値のままです")
    else:
        print(f"✅ UPSTASH_VECTOR_REST_URL: 設定済み")
    
    # Upstash Vector Token
    upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    if not upstash_token:
        print("❌ UPSTASH_VECTOR_REST_TOKEN: 未設定")
        issues.append("UPSTASH_VECTOR_REST_TOKEN が設定されていません")
    elif upstash_token in ["your_upstash_vector_token", "your_actual_upstash_vector_token_here"]:
        print("❌ UPSTASH_VECTOR_REST_TOKEN: プレースホルダ値")
        issues.append("UPSTASH_VECTOR_REST_TOKEN がプレースホルダ値のままです")
    else:
        print(f"✅ UPSTASH_VECTOR_REST_TOKEN: 設定済み")
    
    return issues

def check_files():
    """必要なファイルの存在をチェック"""
    print("\n📁 ファイル存在チェック")
    print("=" * 50)
    
    issues = []
    
    # .envファイル
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env: 存在")
    else:
        print("❌ .env: 不存在")
        issues.append(".env ファイルが存在しません")
    
    # データファイル
    data_files = [
        "data/data.json",
        "data/convert_data.json", 
        "data/embedding_list.jsonl"
    ]
    
    for file_path in data_files:
        file = Path(file_path)
        if file.exists():
            print(f"✅ {file_path}: 存在")
        else:
            print(f"⚠️  {file_path}: 不存在（オプション）")
    
    return issues

def provide_solutions(issues):
    """問題の解決方法を提案"""
    if not issues:
        print("\n🎉 設定に問題はありません！")
        return
    
    print(f"\n🔧 修正が必要な項目: {len(issues)}件")
    print("=" * 50)
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    
    print("\n💡 解決方法:")
    print("=" * 50)
    
    if any("OPENAI_API_KEY" in issue for issue in issues):
        print("【OpenAI APIキー】")
        print("1. https://platform.openai.com/account/api-keys にアクセス")
        print("2. 新しいAPIキーを生成")
        print("3. .envファイルのOPENAI_API_KEY=の後に実際のキーを設定")
        print("   例: OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx")
        print()
    
    if any("UPSTASH" in issue for issue in issues):
        print("【Upstash Vector】")
        print("1. https://console.upstash.com/vector にアクセス")
        print("2. 新しいVector Databaseを作成")
        print("3. REST URLとトークンを取得")
        print("4. .envファイルに設定:")
        print("   UPSTASH_VECTOR_REST_URL=https://xxxxx.upstash.io")
        print("   UPSTASH_VECTOR_REST_TOKEN=xxxxxxxxxxxxxxxx")
        print()
    
    if any(".env ファイル" in issue for issue in issues):
        print("【.envファイル作成】")
        print("1. cp .env.example .env")
        print("2. .envファイルを編集して実際の値を設定")
        print()

def test_api_connection():
    """API接続テスト"""
    print("\n🌐 API接続テスト")
    print("=" * 50)
    
    # OpenAI APIテスト
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("your_"):
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            # 簡単なテストリクエスト
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print("✅ OpenAI API: 接続成功")
        except Exception as e:
            print(f"❌ OpenAI API: 接続失敗 - {str(e)}")
    else:
        print("⏭️  OpenAI API: スキップ（キー未設定）")
    
    # Upstash接続テスト（簡易）
    upstash_url = os.getenv("UPSTASH_VECTOR_REST_URL")
    upstash_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    if upstash_url and upstash_token and not upstash_url.startswith("your_"):
        try:
            import requests
            headers = {"Authorization": f"Bearer {upstash_token}"}
            response = requests.get(f"{upstash_url}/stats", headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ Upstash Vector: 接続成功")
            else:
                print(f"❌ Upstash Vector: 接続失敗 (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Upstash Vector: 接続失敗 - {str(e)}")
    else:
        print("⏭️  Upstash Vector: スキップ（設定未完了）")

def main():
    """メイン関数"""
    print("🏥 GameChat AI 設定診断ツール")
    print("=" * 50)
    print(f"プロジェクトディレクトリ: {project_root}")
    print()
    
    # 各種チェック実行
    api_issues = check_api_keys()
    file_issues = check_files()
    
    all_issues = api_issues + file_issues
    
    # 解決方法の提案
    provide_solutions(all_issues)
    
    # API接続テスト
    if not all_issues:
        test_api_connection()
    
    # 終了コード
    sys.exit(len(all_issues))

if __name__ == "__main__":
    main()
