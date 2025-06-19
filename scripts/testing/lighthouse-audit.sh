#!/bin/bash

# Lighthouse CI用のスクリプト
echo "🔍 Lighthouseパフォーマンス分析を開始します..."

# 本番ビルドの確認
if [ ! -d ".next" ]; then
  echo "❌ 本番ビルドが見つかりません。まずnpm run buildを実行してください。"
  exit 1
fi

# Lighthouseがインストールされているか確認
if ! command -v lighthouse &> /dev/null; then
  echo "🔧 Lighthouseをインストールしています..."
  npm install -g lighthouse
fi

# 開発サーバーをバックグラウンドで起動
echo "🚀 開発サーバーを起動しています..."
npm run start &
SERVER_PID=$!

# サーバーが起動するまで待機
echo "⏳ サーバーの起動を待機しています..."
sleep 10

# LighthouseでWebサイトを分析
echo "🔍 Lighthouse分析を実行しています..."
lighthouse http://localhost:3000 \
  --chrome-flags="--headless" \
  --output=html \
  --output=json \
  --output-path=./lighthouse-report \
  --quiet

echo "📊 分析結果:"
echo "  - HTML レポート: ./lighthouse-report.report.html"
echo "  - JSON データ: ./lighthouse-report.report.json"

# バックグラウンドサーバーを終了
echo "🛑 サーバーを終了しています..."
kill $SERVER_PID

echo "✅ パフォーマンス分析が完了しました！"
echo "📖 HTMLレポートをブラウザで開いて結果を確認してください。"
