# GameChat AI - デプロイメント統合ガイド

**最終更新**: 2025年6月17日

## 📋 概要

GameChat AIプロジェクトのデプロイメントガイドです。開発環境でのローカル実行手順を示します。

## 🎯 クイックスタート

### 前提条件
- Python 3.8以上
- Node.js 14以上
- 必要なAPIキー取得済み（OpenAI、Upstash Vector、reCAPTCHA）

### 1分でデプロイ
```bash
# 1. プロジェクトルートに移動
cd /Users/masaki/Documents/gamechat-ai

# 2. 開発サーバー起動
uvicorn app.main:app --reload --port 8000
```

## 🔧 開発環境

### ローカル開発環境
```bash
# 1. 依存関係インストール
pip install -r requirements.txt
npm install

# 2. 環境変数設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# 3. 開発サーバー起動
# バックエンド
cd backend && uvicorn app.main:app --reload --port 8000

# フロントエンド  
cd frontend && npm run dev
```

### Docker開発環境
```bash
# 開発環境起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

## 🛠️ デプロイ後の確認

### ヘルスチェック
```bash
# サービス状態確認
curl https://gamechat-ai-backend-905497046775.asia-northeast1.run.app/health

# API動作確認
curl -X POST https://gamechat-ai-backend-905497046775.asia-northeast1.run.app/api/rag/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"question": "ポケモンについて教えて", "recaptchaToken": "test"}'
```

### ログ確認
```bash
# Cloud Runサービスログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend" --limit=50

# エラーログのみ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend AND severity>=ERROR" --limit=20
```

## 🔍 トラブルシューティング

### よくある問題

#### 1. APIキー認証エラー
```bash
# Secret Manager確認
gcloud secrets versions access latest --secret="API_KEY_DEVELOPMENT"

# Cloud Runサービス設定確認  
gcloud run services describe gamechat-ai-backend --region=asia-northeast1
```

#### 2. OpenAI API接続エラー
```bash
# APIキーの改行チェック・修正
gcloud secrets versions access latest --secret="OPENAI_API_KEY" | wc -c
gcloud secrets versions access latest --secret="OPENAI_API_KEY" | tr -d '\n' | gcloud secrets versions add OPENAI_API_KEY --data-file=-
```

#### 3. reCAPTCHA認証エラー
- 開発環境: `ENVIRONMENT=development`でテストバイパス利用
- 本番環境: 実際のreCAPTCHAトークンが必要

### ログ分析
```bash
# 認証関連ログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend AND textPayload:authentication" --limit=10

# パフォーマンス関連ログ  
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend AND textPayload:timeout" --limit=10
```

## 📊 監視・メトリクス

### パフォーマンス指標
- **応答時間**: 目標 < 10秒 (現在: 調整中)
- **可用性**: > 99.9%
- **エラー率**: < 1%

### アラート設定
```bash
# Cloud Monitoringでアラート設定
# - 応答時間 > 30秒
# - エラー率 > 5%
# - メモリ使用率 > 80%
```

## 🔄 CI/CD パイプライン

### GitHub Actions設定例
```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/setup-gcloud@v0
      - run: ./scripts/cloud-run-deploy.sh
```

## 📚 関連ドキュメント

- [現在の問題点サマリー](../current-issues-summary.md)
- [API仕様書](../api/rag_api_spec.md)
- [開発ロードマップ](../development-roadmap.md)
- [パフォーマンス最適化](../performance/README.md)

---

**担当者**: 開発チーム  
**次回更新予定**: 2025年6月18日
