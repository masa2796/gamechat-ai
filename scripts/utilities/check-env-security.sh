#!/bin/bash

# =============================================================================
# 環境変数セキュリティチェックスクリプト
# =============================================================================

echo "🔍 環境変数ファイルのセキュリティチェックを開始します..."
echo "=========================================="

# 現在のディレクトリを確認
echo "📁 現在のディレクトリ: $(pwd)"
echo ""

# 1. .envファイルの存在確認
# backend/.env* および frontend/.env* を確認
if ls backend/.env* 1> /dev/null 2>&1 || ls frontend/.env* 1> /dev/null 2>&1; then
    echo "発見された.envファイル:"
    ls -la backend/.env* 2>/dev/null
    ls -la frontend/.env* 2>/dev/null
    echo ""
    # 各ファイルの状態を確認
    for file in backend/.env* frontend/.env*; do
        if [ -f "$file" ]; then
            echo "📄 $file:"
            if git check-ignore "$file" >/dev/null 2>&1; then
                echo "  ✅ 正しくgitignoreされています"
            else
                echo "  ❌ gitignoreされていません！"
                echo "  ⚠️  このファイルがGitにコミットされる可能性があります"
            fi
            size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
            echo "  📊 ファイルサイズ: $size bytes"
            echo ""
        fi
    done
else
    echo "✅ backend/ および frontend/ に .envファイルはありません"
    echo ""
fi

# 2. Gitステータスの確認
echo "📋 2. Gitステータスの確認"
echo "------------------------------------------"
untracked=$(git status --porcelain | grep -E "\.env" | grep "^??")
if [ -n "$untracked" ]; then
    echo "⚠️  未トラックの.envファイル:"
    echo "$untracked"
    echo ""
else
    echo "✅ 未トラックの.envファイルはありません"
    echo ""
fi

# 3. コミット済み.envファイルの確認
echo "📋 3. コミット済み.envファイルの確認"
echo "------------------------------------------"
committed=$(git ls-files | grep -E "\.env" | grep -v "\.example$")
if [ -n "$committed" ]; then
    echo "⚠️  既にコミットされている.envファイル:"
    echo "$committed"
    echo "  💡 これらのファイルにはAPIキーなどの機密情報が含まれている可能性があります"
    echo ""
else
    echo "✅ 機密情報を含む.envファイルはコミットされていません"
    echo ""
fi

# 4. .gitignoreの確認
echo "📋 4. .gitignoreの確認"
echo "------------------------------------------"
if [ -f ".gitignore" ]; then
    echo ".gitignoreに含まれる.env関連のパターン:"
    grep -n "\.env" .gitignore || echo "  ❌ .env関連のパターンが見つかりません"
    echo ""
else
    echo "❌ .gitignoreファイルが存在しません"
    echo ""
fi

# 5. backend/ と frontend/ の確認
echo "📋 5. サブディレクトリの.envファイル確認"
echo "------------------------------------------"
for dir in backend frontend; do
    if [ -d "$dir" ]; then
        echo "📁 $dir/ の確認:"
        if ls "$dir"/.env* 1> /dev/null 2>&1; then
            ls -la "$dir"/.env*
            for file in "$dir"/.env*; do
                if [ -f "$file" ]; then
                    if git check-ignore "$file" >/dev/null 2>&1; then
                        echo "  ✅ $file は正しくgitignoreされています"
                    else
                        echo "  ❌ $file はgitignoreされていません！"
                    fi
                fi
            done
        else
            echo "  ✅ $dir/ に.envファイルはありません"
        fi
        echo ""
    fi
done

# 6. 推奨事項の表示
echo "📋 6. 推奨事項"
echo "------------------------------------------"
echo "✅ 適切な.envファイル管理のために:"
echo "   • .env.example, .env.production.example のみをコミット"
echo "   • 実際のAPIキーを含む.envファイルは絶対にコミットしない"
echo "   • 開発時は .env.example を backend/.env にコピーして使用"
echo "   • 本番時は .env.production.example を backend/.env.production にコピー"
echo ""

echo "🎉 セキュリティチェック完了！"
echo "=========================================="
