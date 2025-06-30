#!/bin/bash

# 本番環境セキュリティチェックスクリプト
# Usage: ./scripts/security-check.sh

echo "🔍 本番環境セキュリティチェック開始..."

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# チェック結果カウンター
PASS=0
FAIL=0
WARN=0

# 関数定義
check_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
    ((WARN++))
}

# 1. 環境変数ファイルの存在確認
echo -e "\n📁 環境変数ファイルチェック"
if [ -f ".env.production" ]; then
    check_pass ".env.production ファイルが存在します"
else
    check_fail ".env.production ファイルが存在しません"
fi

if [ -f "frontend/.env.production" ]; then
    check_pass "frontend/.env.production ファイルが存在します"
else
    check_fail "frontend/.env.production ファイルが存在しません"
fi

if [ -f "backend/.env.production" ]; then
    check_pass "backend/.env.production ファイルが存在します"
else
    check_fail "backend/.env.production ファイルが存在しません"
fi

# 2. 機密情報チェック
echo -e "\n🔐 機密情報チェック"
if [ -f ".env.production" ]; then
    if grep -q "your_.*_here" .env.production; then
        check_fail ".env.production にデフォルト値が残っています"
    else
        check_pass ".env.production のデフォルト値が更新されています"
    fi
fi

if [ -f "backend/.env.production" ]; then
    if grep -q "your_.*_here" backend/.env.production; then
        check_fail "backend/.env.production にデフォルト値が残っています"
    else
        check_pass "backend/.env.production のデフォルト値が更新されています"
    fi
    
    # 必須環境変数の確認
    required_vars=("BACKEND_OPENAI_API_KEY" "UPSTASH_VECTOR_REST_URL" "UPSTASH_VECTOR_REST_TOKEN")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" backend/.env.production; then
            check_pass "必須環境変数 ${var} が設定されています"
        else
            check_fail "必須環境変数 ${var} が設定されていません"
        fi
    done
fi

# 3. ファイルパーミッションチェック
echo -e "\n🔒 ファイルパーミッションチェック"
for file in ".env.production" "frontend/.env.production" "backend/.env.production"; do
    if [ -f "$file" ]; then
        perm=$(stat -f "%Lp" "$file" 2>/dev/null || stat -c "%a" "$file" 2>/dev/null)
        if [ "$perm" = "600" ] || [ "$perm" = "644" ]; then
            check_pass "$file のパーミッションが適切です ($perm)"
        else
            check_warn "$file のパーミッションを確認してください ($perm)"
        fi
    fi
done

# 4. Gitignoreチェック
echo -e "\n📝 Gitignoreチェック"
if grep -q "\.env\.production" .gitignore; then
    check_pass ".env.production ファイルがGitignoreに追加されています"
else
    check_fail ".env.production ファイルがGitignoreに追加されていません"
fi

# 5. CORS設定チェック
echo -e "\n🌐 CORS設定チェック"
if [ -f "backend/.env.production" ]; then
    if grep -q "CORS_ORIGINS=.*yourdomain.com" backend/.env.production; then
        check_warn "CORS_ORIGINS にデフォルトドメインが設定されています。本番ドメインに変更してください"
    elif grep -q "CORS_ORIGINS=" backend/.env.production; then
        check_pass "CORS_ORIGINS が設定されています"
    else
        check_fail "CORS_ORIGINS が設定されていません"
    fi
fi

# 6. SSL証明書チェック（nginx設定）
echo -e "\n🔐 SSL設定チェック"
if [ -d "nginx/ssl" ]; then
    check_pass "SSL証明書ディレクトリが存在します"
    if [ "$(ls -A nginx/ssl)" ]; then
        check_pass "SSL証明書ファイルが配置されています"
    else
        check_warn "SSL証明書ファイルが配置されていません"
    fi
else
    check_warn "SSL証明書ディレクトリが存在しません"
fi

# 7. Docker設定チェック
echo -e "\n🐳 Docker設定チェック"
if [ -f "docker-compose.prod.yml" ]; then
    check_pass "本番用Docker Composeファイルが存在します"
    
    if grep -q "env_file:" docker-compose.prod.yml; then
        check_pass "Docker Composeで環境変数ファイルが設定されています"
    else
        check_warn "Docker Composeで環境変数ファイルの設定を確認してください"
    fi
else
    check_fail "本番用Docker Composeファイルが存在しません"
fi

# 結果サマリー
echo -e "\n📊 チェック結果サマリー"
echo -e "${GREEN}PASS: $PASS${NC}"
echo -e "${YELLOW}WARN: $WARN${NC}"
echo -e "${RED}FAIL: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}🎉 セキュリティチェック完了！本番デプロイの準備ができています。${NC}"
    exit 0
else
    echo -e "\n${RED}❌ 修正が必要な項目があります。上記のFAIL項目を確認してください。${NC}"
    exit 1
fi
