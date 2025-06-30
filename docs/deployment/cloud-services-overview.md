# GameChat AI - Google Cloud サービス利用ガイド

**最終更新**: 2025年6月17日

## 📋 概要

GameChat AIプロジェクで使用しているGoogle Cloud Platform（GCP）およびFirebaseサービスの包括的なガイドです。プロジェクトのクラウドアーキテクチャ、各サービスの役割、設定方法をまとめています。

## 🏗️ アーキテクチャ概要

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│ Firebase        │    │ Google Cloud     │    │ External APIs   │
│ Hosting         │───▶│ Run              │───▶│ OpenAI API      │
│ (Frontend)      │    │ (Backend)        │    │ Upstash Vector  │
│                 │    │                  │    │ reCAPTCHA       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Firebase        │    │ Secret Manager   │    │ Cloud Build     │
│ Authentication  │    │ (API Keys)       │    │ (CI/CD)         │
│ (将来実装予定)   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Artifact         │
                       │ Registry         │
                       │ (Container)      │
                       └──────────────────┘
```

## 📦 使用サービス一覧

### Google Cloud Platform

#### 1. **Cloud Run** 🚀
- **役割**: バックエンドAPIのホスティング
- **プロジェクト**: `gamechat-ai`
- **リージョン**: `asia-northeast1` (東京)
- **サービス名**: `gamechat-ai-backend`
- **URL**: `https://gamechat-ai-backend-905497046775.asia-northeast1.run.app`

**設定詳細**:
```yaml
Memory: 1Gi
CPU: 1 vCPU
Max Instances: 10
Port: 8000
Platform: managed
```

#### 2. **Secret Manager** 🔐
- **役割**: APIキーと機密情報の安全な管理
- **管理するSecret**:
  - `BACKEND_OPENAI_API_KEY`: OpenAI APIキー
  - `UPSTASH_VECTOR_REST_URL`: Upstash Vector DB URL
  - `UPSTASH_VECTOR_REST_TOKEN`: Upstash Vector DB Token
  - `RECAPTCHA_SECRET`: reCAPTCHA秘密キー
  - `API_KEY_DEVELOPMENT`: 開発用APIキー

#### 3. **Artifact Registry** 📦
- **役割**: Dockerコンテナイメージの保存
- **リポジトリ**: `gamechat-ai-backend`
- **場所**: `asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend`

#### 4. **Cloud Build** 🔧
- **役割**: CI/CDパイプライン
- **設定ファイル**: `cloudbuild.yaml`
- **トリガー**: 手動実行またはGitHubトリガー（設定可能）

#### 5. **Cloud Logging** 📊
- **役割**: アプリケーションログの収集・監視
- **ログソース**: Cloud Run サービス

### Firebase

#### 1. **Firebase Hosting** 🌐
- **役割**: フロントエンド（Next.js）のホスティング
- **プロジェクト**: `gamechat-ai`
- **URL**: `https://gamechat-ai.web.app`
- **設定ファイル**: `firebase.json`

**主要設定**:
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

### 外部サービス

#### 1. **OpenAI API** 🤖
- **役割**: AI応答生成
- **モデル**: GPT-4 Turbo
- **使用エンドポイント**: Chat Completions API

#### 2. **Upstash Vector Database** 🗄️
- **役割**: ベクトル検索・RAG機能
- **接続方式**: REST API

#### 3. **Google reCAPTCHA** 🛡️
- **役割**: スパム・ボット対策
- **バージョン**: v2 Checkbox

## 🚀 サービス設定手順

### 1. Google Cloud Project初期設定

```bash
# プロジェクト設定
export PROJECT_ID="gamechat-ai"
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable logging.googleapis.com
```

### 2. Artifact Registry設定

```bash
# リポジトリ作成
gcloud artifacts repositories create gamechat-ai-backend \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="GameChat AI Backend Container Repository"

# Docker認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

### 3. Secret Manager設定

```bash
# OpenAI APIキー
echo "your_openai_api_key" | gcloud secrets create BACKEND_OPENAI_API_KEY --data-file=-

# Upstash設定
echo "your_upstash_url" | gcloud secrets create UPSTASH_VECTOR_REST_URL --data-file=-
echo "your_upstash_token" | gcloud secrets create UPSTASH_VECTOR_REST_TOKEN --data-file=-

# reCAPTCHA設定
echo "your_recaptcha_secret" | gcloud secrets create RECAPTCHA_SECRET --data-file=-

# 開発用APIキー
echo "your_dev_api_key" | gcloud secrets create API_KEY_DEVELOPMENT --data-file=-
```

### 4. Cloud Run設定

```bash
# サービスデプロイ
gcloud run deploy gamechat-ai-backend \
  --image asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,CORS_ORIGINS="https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com" \
  --update-secrets BACKEND_OPENAI_API_KEY=BACKEND_OPENAI_API_KEY:latest \
  --update-secrets UPSTASH_VECTOR_REST_URL=UPSTASH_VECTOR_REST_URL:latest \
  --update-secrets UPSTASH_VECTOR_REST_TOKEN=UPSTASH_VECTOR_REST_TOKEN:latest \
  --update-secrets RECAPTCHA_SECRET=RECAPTCHA_SECRET:latest \
  --update-secrets API_KEY_DEVELOPMENT=API_KEY_DEVELOPMENT:latest
```

### 5. Firebase設定

```bash
# Firebase CLI インストール（未インストールの場合）
npm install -g firebase-tools

# Firebase ログイン
firebase login

# プロジェクト初期化
firebase init hosting

# フロントエンドビルド＆デプロイ
cd frontend
npm run build
cd ..
firebase deploy --only hosting
```

## 🔧 運用・管理

### 監視・ログ確認

#### Cloud Runサービス監視
```bash
# サービス状態確認
gcloud run services describe gamechat-ai-backend --region=asia-northeast1

# ログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend" --limit=50

# エラーログのみ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend AND severity>=ERROR" --limit=20
```

#### リソース使用状況
```bash
# Cloud Runメトリクス確認
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"
```

### Secret Management

#### Secretの更新
```bash
# APIキー更新
echo "new_api_key" | gcloud secrets versions add BACKEND_OPENAI_API_KEY --data-file=-

# Cloud Runサービス再起動（新しいSecretを反映）
gcloud run services update gamechat-ai-backend --region=asia-northeast1
```

#### Secret確認（安全な方法）
```bash
# Secret一覧
gcloud secrets list

# Secretバージョン確認
gcloud secrets versions list BACKEND_OPENAI_API_KEY

# Secret値の確認（注意：ログに残る可能性があります）
gcloud secrets versions access latest --secret="BACKEND_OPENAI_API_KEY"
```

### コンテナイメージ管理

#### イメージ一覧・削除
```bash
# イメージ一覧
gcloud artifacts repositories list

# 特定リポジトリのイメージ一覧
gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend

# 古いイメージ削除
gcloud artifacts docker images delete asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:OLD_TAG
```

## 💰 費用管理

### 現在の構成での推定費用

#### Cloud Run
- **リクエスト**: 月間100万リクエスト想定
- **CPU時間**: 応答時間平均10秒
- **メモリ**: 1GB固定
- **推定費用**: 月額 $50-100

#### Firebase Hosting
- **転送量**: 月間10GB想定
- **推定費用**: 月額 $1-5

#### Secret Manager
- **Secret数**: 5個
- **アクセス回数**: 月間10万回
- **推定費用**: 月額 $1-3

#### Artifact Registry
- **ストレージ**: 5GB想定
- **推定費用**: 月額 $1-2

**合計推定費用**: 月額 **$53-110**

### 費用最適化

#### Cloud Run最適化
```bash
# メモリ使用量監視
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend AND textPayload:memory" --limit=10

# 必要に応じてメモリ調整
gcloud run services update gamechat-ai-backend --region=asia-northeast1 --memory=512Mi
```

#### 不要リソース削除
```bash
# 古いCloud Runリビジョン削除
gcloud run revisions list --service=gamechat-ai-backend --region=asia-northeast1
gcloud run revisions delete REVISION_NAME --region=asia-northeast1

# 古いコンテナイメージ削除
gcloud artifacts docker images delete asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:OLD_TAG
```

## 🔒 セキュリティ

### IAM設定

#### Cloud Buildサービスアカウント権限
```bash
# Secret Manager アクセス権限
gcloud secrets add-iam-policy-binding BACKEND_OPENAI_API_KEY \
  --member="serviceAccount:${PROJECT_ID}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Run 開発者権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_ID}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.developer"
```

### ネットワークセキュリティ

#### CORS設定
```bash
# Cloud Runサービスの環境変数でCORS設定
gcloud run services update gamechat-ai-backend \
  --region=asia-northeast1 \
  --set-env-vars CORS_ORIGINS="https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com"
```

#### API認証
- 開発環境: `API_KEY_DEVELOPMENT` による簡易認証
- 本番環境: Firebase Authentication（将来実装予定）

## 🚨 災害復旧・バックアップ

### コンテナイメージ
- Artifact Registryに自動的に複数バージョンが保存
- `latest`タグと`BUILD_ID`タグの併用

### Secretデータ
- Secret Managerが自動的にバージョン管理
- 複数リージョンでの自動レプリケーション

### 設定ファイル
- GitHubリポジトリでバージョン管理
- `cloudbuild.yaml`, `firebase.json`など

### 復旧手順
```bash
# 1. 前のバージョンにロールバック
gcloud run services update gamechat-ai-backend \
  --region=asia-northeast1 \
  --image asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:PREVIOUS_BUILD_ID

# 2. Secretを前のバージョンに戻す
gcloud run services update gamechat-ai-backend \
  --region=asia-northeast1 \
  --update-secrets BACKEND_OPENAI_API_KEY=BACKEND_OPENAI_API_KEY:PREVIOUS_VERSION

# 3. Firebase Hostingのロールバック
firebase hosting:clone SOURCE_SITE_ID:SOURCE_VERSION_ID TARGET_SITE_ID
```

## 📚 関連ドキュメント

- [デプロイメントガイド](./deployment-guide.md) - 包括的なデプロイ手順
- [Cloud Run OpenAI設定](./cloud-run-openai-setup.md) - APIキー設定詳細
- [API認証実装レポート](./api-key-authentication-implementation-report.md) - 認証システム詳細

## 🔗 公式ドキュメント

- [Google Cloud Run](https://cloud.google.com/run/docs)
- [Firebase Hosting](https://firebase.google.com/docs/hosting)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)
- [Cloud Build](https://cloud.google.com/build/docs)

---

**作成者**: 開発チーム  
**最終更新**: 2025年6月17日  
**次回見直し予定**: 2025年7月17日
