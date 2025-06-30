#!/bin/bash

# GameChat AI APIキー設定確認スクリプト
# 使用方法: ./scripts/verify-api-keys.sh

echo "🔍 GameChat AI APIキー設定確認"
echo "===================================="

# 環境変数の読み込み
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ .envファイルを読み込みました"
else
    echo "❌ .envファイルが見つかりません"
    exit 1
fi

# OpenAI APIキーの確認
echo ""
echo "📡 OpenAI API接続テスト"
echo "------------------------"
if [ -z "$BACKEND_OPENAI_API_KEY" ] || [ "$BACKEND_OPENAI_API_KEY" = "your_openai_api_key" ]; then
    echo "❌ BACKEND_OPENAI_API_KEYが設定されていません"
    echo "   設定方法: https://platform.openai.com/account/api-keys でAPIキーを取得"
else
    # OpenAI API接続テスト
    response=$(curl -s -w "%{http_code}" -o /tmp/openai_test.json \
        -H "Authorization: Bearer $BACKEND_OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
        https://api.openai.com/v1/chat/completions)
    
    http_code="${response: -3}"
    if [ "$http_code" = "200" ]; then
        echo "✅ OpenAI API接続成功"
    else
        echo "❌ OpenAI API接続失敗 (HTTP $http_code)"
        if [ -f /tmp/openai_test.json ]; then
            echo "   エラー詳細:"
            cat /tmp/openai_test.json | jq -r '.error.message // "詳細不明"' 2>/dev/null || cat /tmp/openai_test.json
        fi
    fi
fi

# Upstash Vector接続テスト
echo ""
echo "🗃️  Upstash Vector接続テスト"
echo "----------------------------"
if [ -z "$UPSTASH_VECTOR_REST_URL" ] || [ "$UPSTASH_VECTOR_REST_URL" = "your_upstash_vector_url" ]; then
    echo "❌ UPSTASH_VECTOR_REST_URLが設定されていません"
    echo "   設定方法: https://console.upstash.com/vector でVector Databaseを作成"
elif [ -z "$UPSTASH_VECTOR_REST_TOKEN" ] || [ "$UPSTASH_VECTOR_REST_TOKEN" = "your_upstash_vector_token" ]; then
    echo "❌ UPSTASH_VECTOR_REST_TOKENが設定されていません"
else
    # Upstash Vector接続テスト
    response=$(curl -s -w "%{http_code}" -o /tmp/upstash_test.json \
        -H "Authorization: Bearer $UPSTASH_VECTOR_REST_TOKEN" \
        "$UPSTASH_VECTOR_REST_URL/info")
    
    http_code="${response: -3}"
    if [ "$http_code" = "200" ]; then
        echo "✅ Upstash Vector接続成功"
        if command -v jq &> /dev/null; then
            dimension=$(cat /tmp/upstash_test.json | jq -r '.dimension // "不明"')
            echo "   Vector次元数: $dimension"
        fi
    else
        echo "❌ Upstash Vector接続失敗 (HTTP $http_code)"
        if [ -f /tmp/upstash_test.json ]; then
            echo "   エラー詳細:"
            cat /tmp/upstash_test.json
        fi
    fi
fi

# バックエンドAPI動作テスト
echo ""
echo "🚀 バックエンドAPI動作テスト"
echo "---------------------------"
echo "バックエンドサーバーを起動してから以下のコマンドでテストできます:"
echo "curl -X POST http://localhost:8000/rag/search \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\":\"ゲームについて教えて\"}'"

# クリーンアップ
rm -f /tmp/openai_test.json /tmp/upstash_test.json

echo ""
echo "🎯 次のステップ"
echo "================"
echo "1. APIキーが未設定の場合は、上記の設定方法に従って取得・設定"
echo "2. 設定後、このスクリプトを再実行して接続確認"
echo "3. バックエンドサーバー起動: docker-compose up -d"
echo "4. フロントエンド確認: http://localhost:3000"
