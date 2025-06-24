#!/bin/bash

# ローカルでGitHub Actionsパイプラインをテストするスクリプト
# 実際のワークフローの動作を模擬

set -e

echo "=========================================="
echo "🚀 GitHub Actions パイプライン ローカルテスト"
echo "=========================================="

# 1. 型チェック（Type Check workflow）
echo ""
echo "📋 Step 1: Python型チェック"
echo "------------------------------------------"
python3 -m mypy backend/app --config-file mypy.ini --exclude 'backend/app/tests' || {
    echo "❌ 型チェックに失敗しました"
    exit 1
}
echo "✅ 型チェック完了"

# 2. バックエンドビルド（Build Optimization workflow）
echo ""
echo "🔨 Step 2: バックエンドDockerビルド"
echo "------------------------------------------"
docker build -f backend/Dockerfile -t gamechat-ai-backend:pipeline-test . || {
    echo "❌ バックエンドビルドに失敗しました"
    exit 1
}
echo "✅ バックエンドビルド完了"

# 3. フロントエンドビルド（Build Optimization workflow）
echo ""
echo "🔨 Step 3: フロントエンドDockerビルド"
echo "------------------------------------------"
docker build -f frontend/Dockerfile -t gamechat-ai-frontend:pipeline-test frontend/ || {
    echo "❌ フロントエンドビルドに失敗しました"
    exit 1
}
echo "✅ フロントエンドビルド完了"

# 4. イメージサイズ分析（Build Optimization workflow）
echo ""
echo "📊 Step 4: イメージサイズ分析"
echo "------------------------------------------"
echo "Backend image size:"
docker images gamechat-ai-backend:pipeline-test --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
echo "Frontend image size:"
docker images gamechat-ai-frontend:pipeline-test --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 5. Docker Compose検証
echo ""
echo "🔧 Step 5: Docker Compose設定検証"
echo "------------------------------------------"
docker-compose config > /dev/null || {
    echo "❌ Docker Compose設定に問題があります"
    exit 1
}
echo "✅ Docker Compose設定OK"

# 6. 依存関係チェック（Dependency Analysis workflow）
echo ""
echo "📦 Step 6: 依存関係分析"
echo "------------------------------------------"
echo "Python dependencies:"
if [ -f "backend/requirements.txt" ]; then
    echo "  Total packages: $(wc -l < backend/requirements.txt)"
    echo "  Python version check:"
    python3 --version
fi

echo "Node.js dependencies:"
if [ -f "frontend/package.json" ]; then
    cd frontend
    echo "  Dependencies count: $(npm list --depth=0 --json 2>/dev/null | jq -r '.dependencies | keys | length' 2>/dev/null || echo "Cannot determine")"
    echo "  Node.js version:"
    node --version
    echo "  npm version:"
    npm --version
    cd ..
fi

# 7. セキュリティチェック
echo ""
echo "🔒 Step 7: セキュリティチェック"
echo "------------------------------------------"
echo "Dockerfile security analysis:"
if command -v hadolint &> /dev/null; then
    hadolint backend/Dockerfile frontend/Dockerfile
else
    echo "  hadolint not installed - skipping Dockerfile security check"
fi

# 8. クリーンアップ
echo ""
echo "🧹 Step 8: クリーンアップ"
echo "------------------------------------------"
docker rmi gamechat-ai-backend:pipeline-test gamechat-ai-frontend:pipeline-test || true
echo "✅ クリーンアップ完了"

echo ""
echo "=========================================="
echo "🎉 全てのパイプラインテストが完了しました！"
echo "=========================================="
echo ""
echo "📊 テスト結果サマリー:"
echo "  ✅ Python型チェック: PASSED"
echo "  ✅ バックエンドビルド: PASSED"
echo "  ✅ フロントエンドビルド: PASSED"
echo "  ✅ Docker Compose検証: PASSED"
echo "  ✅ 依存関係分析: PASSED"
echo ""
echo "🚀 GitHub Actionsパイプラインは正常に動作する準備ができています！"
