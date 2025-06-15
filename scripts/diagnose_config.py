#!/usr/bin/env python3
"""
設定診断ツール - backend/.envファイルからAPIキーが正しく読み込まれているかを確認
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def diagnose_config():
    """設定の診断を実行"""
    print("🔍 設定診断開始...")
    print(f"📁 プロジェクトルート: {project_root}")
    
    # backend/.envファイルの存在確認
    backend_env_path = project_root / "backend" / ".env"
    print(f"\n📄 backend/.envファイル:")
    print(f"   パス: {backend_env_path}")
    print(f"   存在: {'✅' if backend_env_path.exists() else '❌'}")
    
    if backend_env_path.exists():
        print(f"   ファイルサイズ: {backend_env_path.stat().st_size} bytes")
        
        # ファイル内容の確認（機密情報をマスク）
        with open(backend_env_path, 'r') as f:
            lines = f.readlines()
        
        print(f"   行数: {len(lines)}")
        print("   内容:")
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                
                # APIキーの値をマスク
                if 'KEY' in key.upper() or 'TOKEN' in key.upper() or 'SECRET' in key.upper():
                    if value and value != 'your_openai_api_key':
                        masked_value = value[:8] + '*' * (len(value) - 12) + value[-4:] if len(value) > 12 else '***masked***'
                        print(f"     {key} = {masked_value}")
                    else:
                        print(f"     {key} = ❌ プレースホルダー値")
                else:
                    print(f"     {key} = {value}")
    
    print("\n🔧 設定クラスからの読み込み確認:")
    try:
        # 設定クラスをインポート
        from app.core.config import settings
        
        # 重要な設定項目をチェック
        config_items = [
            ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
            ("UPSTASH_VECTOR_REST_URL", settings.UPSTASH_VECTOR_REST_URL),
            ("UPSTASH_VECTOR_REST_TOKEN", settings.UPSTASH_VECTOR_REST_TOKEN),
            ("RECAPTCHA_SECRET", settings.RECAPTCHA_SECRET),
            ("ENVIRONMENT", settings.ENVIRONMENT),
            ("DEBUG", settings.DEBUG),
            ("LOG_LEVEL", settings.LOG_LEVEL),
        ]
        
        all_good = True
        for key, value in config_items:
            if value is None:
                print(f"   ❌ {key}: 未設定")
                all_good = False
            elif isinstance(value, str) and (value.startswith('your_') or 'placeholder' in value.lower() or value == ''):
                print(f"   ❌ {key}: プレースホルダー値")
                all_good = False
            else:
                # デバッグ用：実際の値の一部を表示
                debug_info = f" (長さ: {len(str(value))})"
                
                # APIキーの値をマスク
                if 'KEY' in key.upper() or 'TOKEN' in key.upper() or 'SECRET' in key.upper():
                    if len(str(value)) > 12:
                        masked_value = str(value)[:8] + '*' * (len(str(value)) - 12) + str(value)[-4:]
                        print(f"   ✅ {key}: {masked_value}{debug_info}")
                    else:
                        print(f"   ✅ {key}: ***masked***{debug_info}")
                else:
                    print(f"   ✅ {key}: {value}{debug_info}")
        
        if all_good:
            print("\n🎉 すべての必須設定が正しく読み込まれています！")
            return True
        else:
            print("\n⚠️  一部の設定に問題があります。")
            return False
            
    except Exception as e:
        print(f"   ❌ 設定読み込みエラー: {e}")
        return False

def test_api_connection():
    """APIへの接続テスト"""
    print("\n🌐 API接続テスト:")
    
    try:
        from app.core.config import settings
        
        # OpenAI APIキーのテスト
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith('your_'):
            print("   OpenAI API: 設定済み ✅")
            # 実際のAPI接続テストは省略（課金を避けるため）
        else:
            print("   OpenAI API: 未設定 ❌")
        
        # Upstash Vector APIのテスト
        if (settings.UPSTASH_VECTOR_REST_URL and settings.UPSTASH_VECTOR_REST_TOKEN and 
            not settings.UPSTASH_VECTOR_REST_URL.startswith('your_')):
            print("   Upstash Vector: 設定済み ✅")
        else:
            print("   Upstash Vector: 未設定 ❌")
            
    except Exception as e:
        print(f"   ❌ API接続テストエラー: {e}")

if __name__ == "__main__":
    success = diagnose_config()
    test_api_connection()
    
    if success:
        print("\n✅ 診断完了: 設定に問題はありません")
        sys.exit(0)
    else:
        print("\n❌ 診断完了: 設定に問題があります")
        sys.exit(1)
