# 環境設定統合ガイド

このファイルは、GameChat AIプロジェクトの環境変数・設定・API設定を統合したガイドです。

## 📋 概要

GameChat AIプロジェクトの環境設定を開発環境から本番環境まで、すべて統合して管理します。

---

## 🔧 環境ファイル構成

### ルートディレクトリ

| ファイル名         | 用途                           | 使用場所 |
|--------------------|--------------------------------|----------|
| .env.ci            | CI/CD用ダミー値                | CIテスト用 |
| .env.local         | ローカル開発用                 | backend, scripts/data-processing/ |
| .env.template      | テンプレート（サンプル値）     | 新規環境構築時の雛形 |

### backend ディレクトリ

| ファイル名         | 用途                           | 使用場所 |
|--------------------|--------------------------------|----------|
| .env               | backend開発用                  | backend/app/core/config.py |
| .env.production    | backend本番用                  | backend/app/core/config.py |
| .env.test          | backendテスト用                | テスト・CI用 |

### frontend ディレクトリ

| ファイル名             | 用途                           | 使用場所 |
|------------------------|--------------------------------|----------|
| .env.ci                | フロントCI/CD用                | CIビルド用 |
| .env.development       | フロント開発用                 | npm run dev |
| .env.firebase          | Firebase Hosting用             | firebase-deploy.sh |
| .env.local             | フロントローカル開発用         | npm run dev |
| .env.production.bak    | フロント本番用バックアップ     | firebase-deploy.sh |
| .env.template          | フロント用テンプレート         | 新規環境構築時の雛形 |
| .env.test              | フロントE2Eテスト用            | tests/e2e/global-setup.ts |

---

## 🔑 Cloud Run OpenAI API 設定ガイド

### 前提条件
- Google Cloud Projectが作成済み
- Cloud BuildとCloud Runが有効化済み
- OpenAI APIキーを取得済み

### 1. Secret Manager にAPIキーを保存

#### OpenAI APIキーの保存
```bash
# OpenAI APIキーをSecret Managerに保存
gcloud secrets create BACKEND_OPENAI_API_KEY --data-file=-
# 実際のAPIキーを入力してEnterを押す

# または、ファイルから読み込み
echo "your_openai_api_key_here" | gcloud secrets create BACKEND_OPENAI_API_KEY --data-file=-
```

#### Upstash関連のシークレット（使用している場合）
```bash
# Upstash Vector DB URLを保存
echo "your_upstash_url_here" | gcloud secrets create UPSTASH_VECTOR_REST_URL --data-file=-

# Upstash Vector DB Tokenを保存  
echo "your_upstash_token_here" | gcloud secrets create UPSTASH_VECTOR_REST_TOKEN --data-file=-
```

### 2. Cloud Run サービスアカウント権限設定

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-project-id"
export SERVICE_ACCOUNT_EMAIL="your-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

# Secret Manager へのアクセス権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. Cloud Run デプロイ時の環境変数設定

#### cloudbuild.yaml での設定
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/gamechat-ai-backend', './backend']
  
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'gamechat-ai-backend'
      - '--image=gcr.io/$PROJECT_ID/gamechat-ai-backend'
      - '--region=asia-northeast1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--set-env-vars=ENVIRONMENT=production'
      - '--update-secrets=BACKEND_OPENAI_API_KEY=BACKEND_OPENAI_API_KEY:latest'
      - '--update-secrets=UPSTASH_VECTOR_REST_URL=UPSTASH_VECTOR_REST_URL:latest'
      - '--update-secrets=UPSTASH_VECTOR_REST_TOKEN=UPSTASH_VECTOR_REST_TOKEN:latest'
```

#### gcloud CLI での直接設定
```bash
gcloud run services update gamechat-ai-backend \
  --region=asia-northeast1 \
  --update-secrets=BACKEND_OPENAI_API_KEY=BACKEND_OPENAI_API_KEY:latest \
  --update-secrets=UPSTASH_VECTOR_REST_URL=UPSTASH_VECTOR_REST_URL:latest \
  --update-secrets=UPSTASH_VECTOR_REST_TOKEN=UPSTASH_VECTOR_REST_TOKEN:latest
```

### 4. ローカル開発環境での設定

#### .env.local ファイル例
```bash
# OpenAI
BACKEND_OPENAI_API_KEY=sk-your-openai-api-key-here

# Upstash Vector DB
UPSTASH_VECTOR_REST_URL=https://your-vector-db.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your-upstash-token

# その他の設定
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

---

## 🚀 Cloud Storage 設定

### 環境変数
```bash
# 必須（本番環境）
GCS_BUCKET_NAME=gamechat-ai-data
GCS_PROJECT_ID=your-project-id

# オプション（認証）
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### バケット作成
```bash
# GCSバケット作成
gsutil mb -c standard -l asia-northeast1 gs://gamechat-ai-data

# 権限設定
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:your-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

---

## 🔐 認証設定

### APIキー設定
```bash
# 開発用APIキー
API_KEY_DEVELOPMENT=gc_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 本番用APIキー  
API_KEY_PRODUCTION=gc_prod_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 読み取り専用APIキー
API_KEY_READONLY=gc_readonly_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# フロントエンド用APIキー
API_KEY_FRONTEND=gc_frontend_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### reCAPTCHA設定
```bash
# reCAPTCHA v3 秘密鍵
RECAPTCHA_SECRET_TEST=your-recaptcha-secret-key

# reCAPTCHA v3 サイトキー（フロントエンド用）
NEXT_PUBLIC_RECAPTCHA_SITE_KEY=your-recaptcha-site-key
```

---

## 🌍 CORS・ドメイン設定

### 許可ドメイン
```bash
CORS_ORIGINS=https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com,http://localhost:3000
```

---

## 🔍 トラブルシューティング

### 環境変数が読み込まれない場合
1. ファイルパスの確認
2. ファイル権限の確認（600推奨）
3. .gitignore に追加されているか確認

### Secret Manager アクセスエラー
1. サービスアカウント権限の確認
2. Secret Manager API の有効化確認
3. シークレット名の確認

### Cloud Run デプロイエラー
1. 環境変数の形式確認
2. シークレット参照の確認
3. サービスアカウント設定確認

---

## 📝 設定チェックリスト

### 開発環境
- [ ] .env.local ファイル作成
- [ ] OpenAI APIキー設定
- [ ] ローカルデータベース設定

### 本番環境
- [ ] Secret Manager設定
- [ ] Cloud Run環境変数設定
- [ ] CORS設定確認
- [ ] 認証システム動作確認

---

**統合元ファイル**:
- environment-configuration.md
- cloud-run-openai-setup.md  
**統合日**: 2025年7月27日
# 環境変数一覧（2025/06/29時点・命名規則統一済み）

## 命名ルール
- **BACKEND_**: バックエンド（FastAPI/Python）専用
- **NEXT_PUBLIC_**: フロントエンド（Next.js）で公開される環境変数（Next.js仕様）
- **_TEST, _CI**: テスト・CI専用
- Google/Firebase/Recaptcha等は公式推奨名を優先

---

## バックエンド（backend/）
| 環境変数名 | 用途 | 使用ファイル | 環境 |
|---|---|---|---|
| BACKEND_SECRET_KEY | FastAPIセッション用シークレット | backend/app/core/config.py | 全環境 |
| BACKEND_JWT_SECRET_KEY | JWT認証用シークレット | backend/app/core/auth.py, config.py | 全環境 |
| BACKEND_BCRYPT_ROUNDS | パスワードハッシュラウンド数 | backend/app/core/config.py | 全環境 |
| BACKEND_ENVIRONMENT | バックエンド実行環境（production/development/test） | backend/app/core/config.py, services/ | 全環境 |
| BACKEND_LOG_LEVEL | ログ出力レベル | backend/app/core/config.py, logging.py | 全環境 |
| BACKEND_TESTING | テストモード有効化 | backend/app/tests/conftest.py, services/ | テスト |
| BACKEND_MOCK_EXTERNAL_SERVICES | 外部APIモック有効化 | backend/app/services/ | テスト/CI |
| BACKEND_OPENAI_API_KEY | OpenAI APIキー | backend/app/services/, config.py | 全環境 |
| BACKEND_UPSTASH_VECTOR_REST_URL | Upstash Vector DB URL | backend/app/services/, config.py | 全環境 |
| BACKEND_UPSTASH_VECTOR_REST_TOKEN | Upstash Vector DBトークン | backend/app/services/, config.py | 全環境 |
| BACKEND_CORS_ORIGINS | CORS許可リスト | backend/app/core/config.py, security_audit_manager.py | 全環境 |
| BACKEND_RATE_LIMIT_ENABLED | レートリミット有効化 | backend/app/core/config.py | 全環境 |
| BACKEND_JWT_EXPIRE_MINUTES | JWT有効期限（分） | backend/app/core/config.py | 全環境 |
| BACKEND_REDIS_URL, ... | Redis接続設定 | backend/app/core/config.py | 全環境 |
| BACKEND_DB_HOST, ... | DB接続設定 | backend/app/core/config.py | 全環境 |
| BACKEND_SENTRY_DSN | Sentry DSN | backend/app/core/config.py, main.py | 全環境 |
| MONITORING_ENABLED | 監視機能有効化 | backend/app/core/config.py | 全環境 |
| GCS_PROJECT_ID | GCPプロジェクトID | backend/app/core/config.py | 全環境 |
| GCS_BUCKET_NAME | Cloud Storageバケット名 | backend/app/core/config.py | 全環境 |
| GOOGLE_APPLICATION_CREDENTIALS | GCP認証JSONパス | backend/app/core/config.py | 全環境 |
| RECAPTCHA_SECRET_KEY | Recaptcha本番用シークレット | backend/app/services/auth_service.py, config.py | 本番 |
| RECAPTCHA_SECRET_KEY_TEST | Recaptchaテスト用シークレット | backend/app/services/auth_service.py, config.py | テスト/開発 |

## フロントエンド（frontend/）
| 環境変数名 | 用途 | 使用ファイル | 環境 |
|---|---|---|---|
| NEXT_PUBLIC_FIREBASE_API_KEY | Firebase APIキー | frontend/.env*, src/lib/firebase.ts | 全環境 |
| NEXT_PUBLIC_FIREBASE_PROJECT_ID | FirebaseプロジェクトID | frontend/.env*, src/lib/firebase.ts | 全環境 |
| NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN | Firebase Authドメイン | frontend/.env*, src/lib/firebase.ts | 全環境 |
| NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET | Firebase Storageバケット | frontend/.env*, src/lib/firebase.ts | 全環境 |
| NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID | Firebaseメッセージ送信ID | frontend/.env*, src/lib/firebase.ts | 全環境 |
| NEXT_PUBLIC_FIREBASE_APP_ID | Firebase App ID | frontend/.env*, src/lib/firebase.ts | 全環境 |
| NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID | Firebase計測ID | frontend/.env*, src/lib/firebase.ts | 全環境 |
| NEXT_PUBLIC_RECAPTCHA_SECRET_KEY | Recaptcha本番用シークレット | frontend/.env*, src/ | 本番 |
| NEXT_PUBLIC_RECAPTCHA_SECRET_KEY_TEST | Recaptchaテスト用シークレット | frontend/.env*, src/ | テスト/開発 |
| NEXT_PUBLIC_API_URL | バックエンドAPIエンドポイント | frontend/.env*, src/ | 全環境 |
| NEXT_PUBLIC_API_KEY | バックエンドAPIキー | frontend/.env*, src/ | 全環境 |
| NEXT_PUBLIC_ENVIRONMENT | フロントエンド実行環境 | frontend/.env*, src/ | 全環境 |
| NEXT_PUBLIC_SENTRY_DSN | Sentry DSN | frontend/.env*, src/lib/sentry.ts | 全環境 |

## ルート・共通
| 環境変数名 | 用途 | 使用ファイル | 環境 |
|---|---|---|---|
| MONITORING_ENABLED | 監視機能有効化 | backend/app/core/config.py, docker-compose.yml など | 全環境 |
| GOOGLE_APPLICATION_CREDENTIALS | GCP認証JSONパス | backend/app/core/config.py, cloudbuild.yaml など | 全環境 |

---

- **備考**: Next.jsでは `NEXT_PUBLIC_` が必須。FRONTEND_ で始まる変数は将来的な統一用としてドキュメント補足。
- **テスト/CI用**: `_TEST`, `_CI` サフィックスで明示。
- **Google/Firebase/Recaptcha**: 公式推奨名を優先。
- **.envファイル例**: backend/.env.example, frontend/.env.example 参照。