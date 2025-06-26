#!/bin/bash

# ディレクトリ存在確認スクリプト
# GitHub Actions での一貫したディレクトリチェック用

echo "=== Directory Structure Check ==="
echo "Current working directory: $(pwd)"
echo "Available directories and files:"
ls -la

# フロントエンドディレクトリチェック
if [ -d "frontend" ]; then
    echo "✅ Frontend directory found"
    ls -la frontend/
    if [ -f "frontend/package.json" ]; then
        echo "✅ Frontend package.json found"
    else
        echo "❌ Frontend package.json not found"
        exit 1
    fi
else
    echo "❌ Frontend directory not found"
    exit 1
fi

# バックエンドディレクトリチェック
if [ -d "backend" ]; then
    echo "✅ Backend directory found"
    ls -la backend/
    if [ -f "backend/app/main.py" ]; then
        echo "✅ Backend main.py found"
    else
        echo "❌ Backend main.py not found"
        exit 1
    fi
else
    echo "❌ Backend directory not found"
    exit 1
fi

echo "✅ All required directories found"
