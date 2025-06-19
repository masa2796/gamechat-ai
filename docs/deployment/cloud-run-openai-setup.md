# Cloud Run OpenAI API Key 設定ガイド

## 概要

このドキュメントでは、Google Cloud RunでGameChat AIバックエンドをデプロイする際のOpenAI APIキーの設定方法について説明します。

## 前提条件

- Google Cloud Projectが作成済み
- Cloud BuildとCloud Runが有効化済み
- OpenAI APIキーを取得済み

## 1. Secret Manager にAPIキーを保存

### OpenAI APIキーの保存

```bash
# OpenAI APIキーをSecret Managerに保存
gcloud secrets create OPENAI_API_KEY --data-file=-
# 実際のAPIキーを入力してEnterを押す

# または、ファイルから読み込み
echo "your_openai_api_key_here" | gcloud secrets create OPENAI_API_KEY --data-file=-
```

### Upstash関連のシークレット（使用している場合）

```bash
# Upstash Vector DB URLを保存
echo "your_upstash_url_here" | gcloud secrets create UPSTASH_VECTOR_REST_URL --data-file=-

# Upstash Vector DB Tokenを保存
echo "your_upstash_token_here" | gcloud secrets create UPSTASH_VECTOR_REST_TOKEN --data-file=-
```

## 2. Secret Managerの権限設定

Cloud Buildサービスアカウントにシークレットへのアクセス権限を付与：

```bash
# プロジェクトIDを設定
PROJECT_ID="your-project-id"

# Cloud Buildサービスアカウント
CLOUD_BUILD_SA="${PROJECT_ID}@cloudbuild.gserviceaccount.com"

# シークレットへのアクセス権限を付与
gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding UPSTASH_VECTOR_REST_URL \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding UPSTASH_VECTOR_REST_TOKEN \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/secretmanager.secretAccessor"
```

## 3. Cloud Buildの設定確認

`cloudbuild.yaml`ファイルで以下が設定されていることを確認：

```yaml
steps:
  # 環境変数の設定
  - name: 'gcr.io/cloud-builders/docker'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "ENVIRONMENT=production" > backend/.env.production
        echo "OPENAI_API_KEY=$$OPENAI_API_KEY" >> backend/.env.production
        echo "UPSTASH_VECTOR_REST_URL=$$UPSTASH_VECTOR_REST_URL" >> backend/.env.production
        echo "UPSTASH_VECTOR_REST_TOKEN=$$UPSTASH_VECTOR_REST_TOKEN" >> backend/.env.production
    secretEnv: ['OPENAI_API_KEY', 'UPSTASH_VECTOR_REST_URL', 'UPSTASH_VECTOR_REST_TOKEN']

  # Cloud Runにデプロイ
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [
      'run', 'deploy', 'gamechat-ai-backend',
      '--image', 'gcr.io/$PROJECT_ID/gamechat-ai-backend:$BUILD_ID',
      '--region', 'asia-northeast1',
      '--platform', 'managed',
      '--allow-unauthenticated',
      '--port', '8000',
      '--memory', '1Gi',
      '--cpu', '1',
      '--max-instances', '10',
      '--set-env-vars', 'ENVIRONMENT=production',
      '--set-env-vars', 'LOG_LEVEL=INFO',
      '--set-env-vars', 'OPENAI_API_KEY=$$OPENAI_API_KEY',
      '--set-env-vars', 'UPSTASH_VECTOR_REST_URL=$$UPSTASH_VECTOR_REST_URL',
      '--set-env-vars', 'UPSTASH_VECTOR_REST_TOKEN=$$UPSTASH_VECTOR_REST_TOKEN',
      '--set-env-vars', 'CORS_ORIGINS=https://YOUR_DOMAIN.web.app,https://YOUR_DOMAIN.firebaseapp.com'
    ]
    secretEnv: ['OPENAI_API_KEY', 'UPSTASH_VECTOR_REST_URL', 'UPSTASH_VECTOR_REST_TOKEN']

# シークレットの設定
availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/OPENAI_API_KEY/versions/latest
      env: OPENAI_API_KEY
    - versionName: projects/$PROJECT_ID/secrets/UPSTASH_VECTOR_REST_URL/versions/latest
      env: UPSTASH_VECTOR_REST_URL
    - versionName: projects/$PROJECT_ID/secrets/UPSTASH_VECTOR_REST_TOKEN/versions/latest
      env: UPSTASH_VECTOR_REST_TOKEN
```

## 4. デプロイの実行

### Cloud Buildを使用したデプロイ

```bash
# Cloud Buildトリガーを手動実行
gcloud builds submit --config cloudbuild.yaml .

# または、特定のタグでビルド
gcloud builds submit --config cloudbuild.yaml --substitutions=_TAG=v1.0.0 .
```

### 直接Cloud Runへのデプロイ（開発用）

```bash
# Dockerイメージをビルド
docker build -f backend/Dockerfile -t gcr.io/$PROJECT_ID/gamechat-ai-backend:latest .

# Container Registryにプッシュ
docker push gcr.io/$PROJECT_ID/gamechat-ai-backend:latest

# Cloud Runにデプロイ（環境変数付き）
gcloud run deploy gamechat-ai-backend \
  --image gcr.io/$PROJECT_ID/gamechat-ai-backend:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars LOG_LEVEL=INFO \
  --update-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest \
  --update-secrets UPSTASH_VECTOR_REST_URL=UPSTASH_VECTOR_REST_URL:latest \
  --update-secrets UPSTASH_VECTOR_REST_TOKEN=UPSTASH_VECTOR_REST_TOKEN:latest
```

## 5. デプロイ後の確認

### 環境変数の確認

```bash
# Cloud Runサービスの詳細を確認
gcloud run services describe gamechat-ai-backend --region=asia-northeast1

# 環境変数が正しく設定されているかログで確認
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend" --limit=50
```

### ヘルスチェック

```bash
# サービスURLを取得
SERVICE_URL=$(gcloud run services describe gamechat-ai-backend --region=asia-northeast1 --format='value(status.url)')

# ヘルスチェックエンドポイントをテスト
curl -f "${SERVICE_URL}/health"

# Chatエンドポイントのテスト（認証が必要な場合は認証情報を含める）
curl -X POST "${SERVICE_URL}/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは", "user_id": "test_user"}'
```

## 6. トラブルシューティング

### よくある問題

1. **APIキーが認識されない**
   - Secret Managerに正しく保存されているか確認
   - Cloud Buildサービスアカウントの権限を確認
   - `cloudbuild.yaml`の`secretEnv`設定を確認

2. **環境変数が設定されていない**
   - Cloud Runサービスの環境変数設定を確認
   - `--set-env-vars`または`--update-secrets`オプションの使用を確認

3. **デプロイがタイムアウトする**
   - Cloud Buildのタイムアウト設定を確認
   - Dockerイメージのサイズを最適化

### ログの確認

```bash
# Cloud Buildのログ
gcloud builds log [BUILD_ID]

# Cloud Runのログ
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend" --limit=50 --format="table(timestamp,severity,textPayload)"
```

## セキュリティ考慮事項

1. **APIキーの保護**
   - Secret Managerを使用してAPIキーを安全に保存
   - 環境変数として直接設定しない
   - GitリポジトリにAPIキーをコミットしない

2. **アクセス制御**
   - 最小権限の原則に従ってIAM権限を設定
   - 本番環境では適切な認証・認可を実装

3. **監査とモニタリング**
   - Cloud Auditログでシークレットアクセスを監視
   - Cloud Monitoringでサービスの健全性を監視

## 関連ドキュメント

- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Run環境変数](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Cloud Build設定](https://cloud.google.com/build/docs/configuring-builds/use-secrets)
