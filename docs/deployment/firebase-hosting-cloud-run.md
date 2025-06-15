# Firebase Hosting + Cloud Run デプロイガイド

## 概要

GameChat AI を Firebase Hosting（フロントエンド）+ Google Cloud Run（バックエンド）にデプロイするためのガイドです。

**🎉 デプロイ完了済み**
- **バックエンドURL**: `https://gamechat-ai-backend-507618950161.asia-northeast1.run.app`
- **プロジェクトID**: `gamechat-ai-production`
- **リージョン**: `asia-northeast1`（東京）
- **デプロイ日**: 2025年6月15日

## 前提条件

### 必要なツール
- Firebase CLI: `npm install -g firebase-tools`
- Google Cloud CLI: [インストールガイド](https://cloud.google.com/sdk/docs/install)
- Docker Desktop
- Node.js 20+

### Google Cloud プロジェクト設定
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. 以下のAPIを有効化（✅ 完了済み）：
   - Cloud Run API
   - Container Registry API
   - Cloud Build API

## 🚀 自動デプロイ（推奨）

### 1. 環境変数設定

```bash
# Google Cloud プロジェクトID を設定
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### 2. 自動デプロイ実行

```bash
# 全体デプロイ
./scripts/firebase-deploy.sh

# バックエンドのみ
./scripts/firebase-deploy.sh backend

# フロントエンドのみ
./scripts/firebase-deploy.sh frontend
```

## 🔧 手動デプロイ

### Step 1: Firebase プロジェクト初期化

```bash
# Firebase ログイン
firebase login

# Firebase プロジェクト設定
firebase use --add your-project-id
```

### Step 2: バックエンドデプロイ（Cloud Run）✅ 完了

```bash
# Google Cloud プロジェクト設定
gcloud config set project gamechat-ai-production

# APIを有効化（完了済み）
gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com

# Docker 認証設定（完了済み）
gcloud auth configure-docker

# Docker イメージビルド（Cloud Run対応）
docker build --platform linux/amd64 -f backend/Dockerfile -t gcr.io/gamechat-ai-production/gamechat-ai-backend .

# Container Registry にプッシュ（完了済み）
docker push gcr.io/gamechat-ai-production/gamechat-ai-backend:latest

# Cloud Run デプロイ（完了済み）
gcloud run deploy gamechat-ai-backend \
  --image gcr.io/gamechat-ai-production/gamechat-ai-backend:latest \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,OPENAI_API_KEY=dummy"
```

**デプロイ結果**:
- ✅ サービス URL: `https://gamechat-ai-backend-507618950161.asia-northeast1.run.app`
- ✅ ヘルスチェック: `/health` - 正常応答
- ✅ API ドキュメント: `/docs` - アクセス可能

### Step 3: フロントエンドビルド

```bash
cd frontend

# 依存関係インストール
npm ci

# 環境変数設定（Cloud Run URLを指定）
echo "NEXT_PUBLIC_API_URL=https://your-cloud-run-url" > .env.production

# Next.js ビルド（export モード）
npm run build
```

### Step 4: Firebase Hosting デプロイ

```bash
# ルートディレクトリに戻る
cd ..

# Firebase Hosting デプロイ
firebase deploy --only hosting
```

## 📋 設定ファイル

### firebase.json
```json
{
  "hosting": {
    "public": "frontend/out",
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "gamechat-ai-backend",
          "region": "asia-northeast1"
        }
      }
    ]
  }
}
```

### next.config.js
```javascript
const nextConfig = {
  output: 'export',  // 静的サイト生成
  // その他の設定...
}
```

## 🔄 Cloud Build（自動化）

### cloudbuild.yaml を使用した自動デプロイ

```bash
# Cloud Build トリガー作成
gcloud builds submit --config cloudbuild.yaml
```

## 🌐 URL構成

デプロイ後のURL構成：

- **フロントエンド**: `https://your-project-id.web.app`
- **バックエンドAPI**: `https://your-project-id.web.app/api/*` (Firebase Hosting経由)
- **直接バックエンド**: `https://gamechat-ai-backend-xxx-an.a.run.app`

## 🔐 セキュリティ設定

### 環境変数（Cloud Run）

Google Cloud Secret Manager で管理：

```bash
# シークレット作成
gcloud secrets create OPENAI_API_KEY --data-file=-
gcloud secrets create UPSTASH_VECTOR_REST_URL --data-file=-
gcloud secrets create UPSTASH_VECTOR_REST_TOKEN --data-file=-

# Cloud Run サービスにシークレット設定
gcloud run services update gamechat-ai-backend \
  --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest \
  --update-secrets=UPSTASH_VECTOR_REST_URL=UPSTASH_VECTOR_REST_URL:latest \
  --update-secrets=UPSTASH_VECTOR_REST_TOKEN=UPSTASH_VECTOR_REST_TOKEN:latest \
  --region=asia-northeast1
```

### CORS設定

バックエンドで Firebase Hosting ドメインを許可：

```python
# backend/app/main.py
CORS_ORIGINS = [
    "https://your-project-id.web.app",
    "https://your-project-id.firebaseapp.com"
]
```

## 📊 監視・ログ

### Cloud Run ログ

```bash
# ログ確認
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend" --limit=50
```

### Firebase Hosting ログ

Firebase Console から確認可能

## 🔄 アップデート手順

```bash
# 1. コード変更後
git add .
git commit -m "Update application"

# 2. 再デプロイ
./scripts/firebase-deploy.sh

# 3. ヘルスチェック
./scripts/firebase-deploy.sh health
```

## ❗ トラブルシューティング

### よくある問題

1. **Cloud Run デプロイエラー**
   - IAM 権限確認: Cloud Run Developer ロール
   - API有効化確認

2. **Firebase Hosting ビルドエラー**
   - `next.config.js` の `output: 'export'` 設定確認
   - 環境変数設定確認

3. **CORS エラー**
   - バックエンドのCORS設定確認
   - Firebase Hosting ドメイン許可確認

### デバッグコマンド

```bash
# Cloud Run サービス詳細確認
gcloud run services describe gamechat-ai-backend --region=asia-northeast1

# Firebase プロジェクト確認
firebase projects:list

# Docker イメージ確認
docker images | grep gamechat-ai
```
