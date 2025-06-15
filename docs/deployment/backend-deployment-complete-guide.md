# バックエンドデプロイメント完全ガイド

## 🚀 成功したデプロイメント設定

### 概要
このドキュメントは、GameChat AIバックエンドをCloud Runに正常にデプロイするまでに発生した問題とその解決方法、および今後のデプロイメントを成功させるための完全なガイドです。

### デプロイメント成功要因
- Secret Manager経由での環境変数管理
- 適切な権限設定
- YAML形式の環境変数ファイル使用
- 不要ファイルの除外設定

---

## ❌ デプロイ失敗の主な原因と解決方法

### 1. 環境変数・シークレット管理エラー

#### 問題1-1: `--set-env-vars`での特殊文字エラー
```bash
# ❌ 失敗例
--set-env-vars CORS_ORIGINS=http://localhost:3000,https://example.com
```
**原因**: カンマやURLが含まれる値でシェルエスケープエラー

**解決方法**: `--env-vars-file`方式に変更
```yaml
# cloud-run-env.yaml
ENVIRONMENT: production
DEBUG: 'false'
LOG_LEVEL: INFO
CORS_ORIGINS: 'https://gamechat-ai.web.app,https://your-domain.com'
```

#### 問題1-2: シークレット参照エラー
```bash
# ❌ 失敗例
--set-secrets OPENAI_API_KEY=openai-api-key:latest
```
**原因**: シークレットが存在しない、またはアクセス権限がない

**解決方法**: 
1. Secret Managerでシークレット作成
2. サービスアカウントに`secretmanager.secretAccessor`権限付与
```bash
gcloud secrets create openai-api-key --data-file=-
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:your-project@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. API・権限エラー

#### 問題2-1: 必要なAPIが有効化されていない
**症状**: `API [xxx.googleapis.com] not enabled`

**解決方法**: 必要なAPIを有効化
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 問題2-2: サービスアカウント権限不足
**症状**: `Permission denied`エラー

**解決方法**: Cloud Buildサービスアカウントに必要な権限を付与
```bash
# Cloud Run Admin権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"

# サービスアカウントユーザー権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

### 3. ビルド設定エラー

#### 問題3-1: 不要ファイルによるビルド遅延・エラー
**原因**: `node_modules`、`.env`ファイル等がビルドコンテキストに含まれる

**解決方法**: `.gcloudignore`ファイル作成
```gitignore
node_modules/
.env*
!.env.example
!.env.*.template
__pycache__/
.git/
logs/
*.pyc
.DS_Store
```

#### 問題3-2: Docker設定エラー
**症状**: Dockerfileが見つからない、ビルドコンテキストエラー

**解決方法**: cloudbuild.yamlでDockerfile位置を明示
```yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'backend/Dockerfile', '-t', '$_SERVICE_NAME', './backend']
  dir: '.'
```

### 4. ネットワーク・アクセスエラー

#### 問題4-1: ヘルスチェック失敗
**症状**: サービスがデプロイされるが、アクセスできない

**解決方法**: 
1. ヘルスチェックエンドポイントの実装確認
2. ポート設定確認（Cloud Runは$PORTを使用）
3. CORS設定確認

```python
# backend/app/main.py
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

---

## ✅ 成功するデプロイメントの設定

### 必要なファイル構成
```
project-root/
├── cloudbuild.yaml          # ビルド設定
├── cloud-run-env.yaml       # 環境変数
├── .gcloudignore           # 除外ファイル指定
├── backend/
│   ├── Dockerfile
│   ├── app/
│   └── requirements.txt
└── scripts/
    └── prod-deploy.sh      # デプロイスクリプト
```

### 1. cloudbuild.yaml（最終版）
```yaml
steps:
  # Docker Build
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build', 
      '-f', 'backend/Dockerfile', 
      '-t', 'gcr.io/$PROJECT_ID/gamechat-ai-backend', 
      './backend'
    ]
    dir: '.'

  # Docker Push
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/gamechat-ai-backend']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [
      'run', 'deploy', 'gamechat-ai-backend',
      '--image', 'gcr.io/$PROJECT_ID/gamechat-ai-backend',
      '--region', 'asia-northeast1',
      '--platform', 'managed',
      '--allow-unauthenticated',
      '--memory', '1Gi',
      '--cpu', '1',
      '--port', '8000',
      '--env-vars-file', 'cloud-run-env.yaml',
      '--update-secrets', 'OPENAI_API_KEY=openai-api-key:latest',
      '--update-secrets', 'UPSTASH_VECTOR_REST_URL=upstash-vector-url:latest',
      '--update-secrets', 'UPSTASH_VECTOR_REST_TOKEN=upstash-vector-token:latest'
    ]

substitutions:
  _SERVICE_NAME: gamechat-ai-backend

options:
  logging: CLOUD_LOGGING_ONLY
```

### 2. cloud-run-env.yaml
```yaml
ENVIRONMENT: production
DEBUG: 'false'
LOG_LEVEL: INFO
CORS_ORIGINS: 'https://gamechat-ai.web.app,https://your-domain.com'
RATE_LIMIT_ENABLED: 'true'
```

### 3. デプロイ前チェックリスト

#### Secret Manager設定
- [ ] OpenAI API Key作成済み
- [ ] Upstash Vector URL/Token作成済み
- [ ] サービスアカウントにSecretAccessor権限付与済み

#### API有効化
- [ ] Cloud Build API
- [ ] Cloud Run API
- [ ] Secret Manager API
- [ ] Container Registry API

#### 権限設定
- [ ] Cloud Build Service Account: Cloud Run Admin
- [ ] Cloud Build Service Account: Service Account User
- [ ] Cloud Build Service Account: Secret Manager Secret Accessor

#### ファイル設定
- [ ] .gcloudignore作成済み
- [ ] cloud-run-env.yaml作成済み
- [ ] Dockerfileが正しい場所に存在

---

## 🔧 トラブルシューティング

### よくあるエラーメッセージと対処法

#### 1. "API [xxx] not enabled"
```bash
gcloud services enable [API名]
```

#### 2. "Permission denied"
```bash
# プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# 権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"
```

#### 3. "Secret not found"
```bash
# シークレット作成
echo "your_api_key_here" | gcloud secrets create openai-api-key --data-file=-

# アクセス権限付与
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### 4. "Service not ready"
```bash
# サービス状態確認
gcloud run services describe gamechat-ai-backend --region=asia-northeast1

# ログ確認
gcloud logs read --filter="resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend" --limit=50
```

### デバッグ用コマンド
```bash
# ビルドログ確認
gcloud builds list --limit=5

# サービス詳細確認
gcloud run services describe gamechat-ai-backend --region=asia-northeast1

# ヘルスチェック
curl -f https://your-service-url/health
```

---

## 📈 パフォーマンス最適化

### リソース設定推奨値
- **Memory**: 1Gi（基本）〜 2Gi（高負荷時）
- **CPU**: 1（基本）〜 2（高負荷時）
- **Max instances**: 10（コスト考慮）
- **Min instances**: 0（コスト最適化）

### 環境変数最適化
```yaml
# 本番環境推奨設定
LOG_LEVEL: INFO          # DEBUGはログが多すぎる
DEBUG: 'false'           # 本番では必ずfalse
RATE_LIMIT_ENABLED: 'true'  # セキュリティのため有効化
```

---

## 🔐 セキュリティ考慮事項

### 環境変数管理
- ✅ Secret Manager使用
- ✅ 環境変数は最小限に限定
- ✅ .envファイルはgitignore設定済み

### アクセス制御
- ✅ 必要最小限の権限付与
- ✅ 認証なしアクセス（必要に応じて変更）
- ✅ CORS設定適切

### 監視・ログ
- ✅ Cloud Logging有効
- ✅ エラーログ収集設定
- ✅ ヘルスチェック実装

このガイドに従うことで、バックエンドの安定したデプロイメントが可能になります。
