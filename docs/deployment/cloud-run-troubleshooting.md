# Cloud Run バックエンドデプロイメント トラブルシューティングガイド

## 概要

本ドキュメントでは、GameChat AIプロジェクトのバックエンドをGoogle Cloud Runにデプロイする際に発生した問題とその解決策をまとめています。

## 発生した問題一覧

### 1. Secret Manager API未有効化

#### 🚨 問題
```
API [secretmanager.googleapis.com] not enabled on project [gamechat-ai-production]. 
Would you like to enable and retry (this will take a few minutes)? (y/N)?
```

#### 💡 原因
- プロジェクトでSecret Manager APIが有効化されていなかった
- Cloud Build、Cloud Run APIも未有効化

#### ✅ 解決策
```bash
# 必要なAPIを有効化
gcloud services enable secretmanager.googleapis.com --project=gamechat-ai-production
gcloud services enable cloudbuild.googleapis.com --project=gamechat-ai-production
gcloud services enable run.googleapis.com --project=gamechat-ai-production
gcloud services enable containerregistry.googleapis.com --project=gamechat-ai-production
```

### 2. Secret Manager権限不足

#### 🚨 問題
```
ERROR: build step 0 "gcr.io/cloud-builders/docker" failed: failed to access secret version for secret projects/gamechat-ai-production/secrets/OPENAI_API_KEY/versions/latest: rpc error: code = PermissionDenied desc = Permission 'secretmanager.versions.access' denied
```

#### 💡 原因
- Cloud BuildサービスアカウントがSecret Managerへのアクセス権限を持っていなかった
- 単一のシークレットレベルの権限設定だけでは不十分

#### ✅ 解決策
```bash
# プロジェクトレベルでSecret Manager Admin権限を付与
gcloud projects add-iam-policy-binding gamechat-ai-production \
  --member="serviceAccount:507618950161@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.admin" \
  --project=gamechat-ai-production

# Cloud Runサービスアカウントにも権限付与
gcloud projects add-iam-policy-binding gamechat-ai-production \
  --member="serviceAccount:507618950161-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gamechat-ai-production
```

### 3. Cloud Run環境変数の特殊文字エラー

#### 🚨 問題
```
ERROR: (gcloud.run.deploy) argument --set-env-vars: Bad syntax for dict arg: [https://gamechat-ai.firebaseapp.com]. Please see `gcloud topic flags-file` or `gcloud topic escaping` for information on providing list or dictionary flag values with special characters.
```

#### 💡 原因
- `--set-env-vars`でURL（コロン、ピリオド、スラッシュ等の特殊文字）を含む値を直接指定
- 複数の環境変数をカンマ区切りで指定した際に、値に含まれるカンマがパーサーを混乱させた

#### ❌ 問題のあった設定
```yaml
'--set-env-vars', 'ENVIRONMENT=production,LOG_LEVEL=INFO,CORS_ORIGINS=https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com'
```

#### ✅ 解決策（方法1: 個別指定）
```yaml
'--set-env-vars', 'ENVIRONMENT=production',
'--set-env-vars', 'LOG_LEVEL=INFO',
'--set-env-vars', 'CORS_ORIGINS=https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com'
```

### 4. 環境変数ファイル形式エラー

#### 🚨 問題
```
ERROR: (gcloud.run.deploy) argument --env-vars-file: Invalid YAML/JSON data in [cloud-run-env.yaml], expected map-like data.
```

#### 💡 原因
- `--env-vars-file`に渡すファイルが適切なYAML/JSON形式になっていなかった
- 単純なkey=value形式のテキストファイルを渡していた

#### ❌ 問題のあった形式
```
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com
```

#### ✅ 解決策（最終形式）
```yaml
# cloudbuild.yaml内でのYAMLファイル作成
cat > cloud-run-env.yaml << EOF
ENVIRONMENT: production
LOG_LEVEL: INFO
CORS_ORIGINS: "https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com"
EOF
```

### 5. ビルドアーカイブサイズ過大

#### 🚨 問題
```
Creating temporary archive of 23034 file(s) totalling 335.3 MiB before compression.
```

#### 💡 原因
- `.gcloudignore`ファイルが存在せず、不要なファイル（node_modules、.git等）がアーカイブに含まれていた

#### ✅ 解決策
`.gcloudignore`ファイルを作成：
```gitignore
# Git-related files
.git/
.gitignore

# Node.js
frontend/node_modules/
frontend/.next/
frontend/dist/
frontend/build/

# Python
backend/__pycache__/
backend/**/__pycache__/
**/*.pyc
**/*.pyo
**/*.pyd
.Python
backend/env/
backend/venv/
backend/.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Environment files (except templates)
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
backend/.env
backend/.env.local

# Testing
coverage/
.pytest_cache/

# Documentation build
docs/_build/
docs/sphinx/_build/

# Backup files
backups/

# Build artifacts
*.tar.gz
*.zip
```

## 最終的な正しい設定

### cloudbuild.yaml（最終版）
```yaml
steps:
  # 環境変数の設定
  - name: 'gcr.io/cloud-builders/docker'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        # backend用の環境変数ファイル作成
        echo "ENVIRONMENT=production" > backend/.env.production
        echo "OPENAI_API_KEY=$$OPENAI_API_KEY" >> backend/.env.production
        echo "UPSTASH_VECTOR_REST_URL=$$UPSTASH_VECTOR_REST_URL" >> backend/.env.production
        echo "UPSTASH_VECTOR_REST_TOKEN=$$UPSTASH_VECTOR_REST_TOKEN" >> backend/.env.production
        echo "CORS_ORIGINS=https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com" >> backend/.env.production
        
        # Cloud Run用の環境変数ファイル作成（YAML形式）
        cat > cloud-run-env.yaml << EOF
        ENVIRONMENT: production
        LOG_LEVEL: INFO
        CORS_ORIGINS: "https://gamechat-ai.web.app,https://gamechat-ai.firebaseapp.com"
        EOF
    secretEnv: ['OPENAI_API_KEY', 'UPSTASH_VECTOR_REST_URL', 'UPSTASH_VECTOR_REST_TOKEN']

  # バックエンドDockerイメージのビルド
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-f', 'backend/Dockerfile',
      '-t', 'gcr.io/$PROJECT_ID/gamechat-ai-backend:$BUILD_ID',
      '-t', 'gcr.io/$PROJECT_ID/gamechat-ai-backend:latest',
      '.'
    ]

  # Container Registryにプッシュ
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/gamechat-ai-backend:$BUILD_ID']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/gamechat-ai-backend:latest']

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
      '--env-vars-file', 'cloud-run-env.yaml',
      '--update-secrets', 'OPENAI_API_KEY=OPENAI_API_KEY:latest',
      '--update-secrets', 'UPSTASH_VECTOR_REST_URL=UPSTASH_VECTOR_REST_URL:latest',
      '--update-secrets', 'UPSTASH_VECTOR_REST_TOKEN=UPSTASH_VECTOR_REST_TOKEN:latest'
    ]
    env:
      - 'CLOUDSDK_RUN_REGION=asia-northeast1'

# シークレットの設定
availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/OPENAI_API_KEY/versions/latest
      env: OPENAI_API_KEY
    - versionName: projects/$PROJECT_ID/secrets/UPSTASH_VECTOR_REST_URL/versions/latest
      env: UPSTASH_VECTOR_REST_URL
    - versionName: projects/$PROJECT_ID/secrets/UPSTASH_VECTOR_REST_TOKEN/versions/latest
      env: UPSTASH_VECTOR_REST_TOKEN

# ビルドオプション
options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY

timeout: 1200s
```

## 学んだ教訓とベストプラクティス

### 1. API有効化の事前確認
```bash
# デプロイ前に必要なAPIが有効化されているか確認
gcloud services list --enabled --project=PROJECT_ID
```

### 2. 権限設定の段階的確認
```bash
# IAMポリシーの確認
gcloud projects get-iam-policy PROJECT_ID

# 特定のサービスアカウントの権限確認
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:SERVICE_ACCOUNT_EMAIL"
```

### 3. 環境変数設定のガイドライン
- 特殊文字を含む値は引用符で囲む
- URLを含む環境変数は`--env-vars-file`を使用
- 複数の環境変数は個別に指定するか、適切なYAML形式で指定

### 4. Secret Managerのベストプラクティス
- シークレット作成時に適切なIAM権限を同時に設定
- 本番環境では最小権限の原則を適用
- シークレットのバージョン管理を活用

### 5. ビルド最適化
- `.gcloudignore`ファイルを作成して不要なファイルを除外
- マルチステージDockerビルドでイメージサイズを最適化
- 適切なマシンタイプを選択してビルド時間を短縮

## 診断コマンド集

### Cloud Buildの診断
```bash
# 最新のビルド状況確認
gcloud builds list --limit=5 --project=PROJECT_ID

# 特定のビルドのログ確認
gcloud builds log BUILD_ID --project=PROJECT_ID

# Cloud Buildサービスアカウントの権限確認
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:*@cloudbuild.gserviceaccount.com"
```

### Cloud Runの診断
```bash
# サービス詳細確認
gcloud run services describe SERVICE_NAME --region=REGION --project=PROJECT_ID

# サービスのログ確認
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" \
  --limit=50 --project=PROJECT_ID

# ヘルスチェック
curl -f "SERVICE_URL/health"
```

### Secret Managerの診断
```bash
# シークレット一覧確認
gcloud secrets list --project=PROJECT_ID

# 特定のシークレットのIAMポリシー確認
gcloud secrets get-iam-policy SECRET_NAME --project=PROJECT_ID

# シークレットのバージョン確認
gcloud secrets versions list SECRET_NAME --project=PROJECT_ID
```

## まとめ

今回のデプロイメントで発生した問題は、主に以下のカテゴリに分類できます：

1. **インフラストラクチャの設定不備**（API未有効化、権限不足）
2. **設定ファイルの形式問題**（YAML形式、特殊文字エスケープ）
3. **ビルド最適化の不備**（アーカイブサイズ、除外ファイル設定）

これらの問題を体系的に解決することで、安定したCloud Runデプロイメントパイプラインを構築できました。

今後同様のプロジェクトでは、このガイドを参考に事前チェックリストを作成し、段階的な検証を行うことを推奨します。
