# Cloud Run デプロイメント チェックリスト

このチェックリストは、Cloud Runへのデプロイメント前に確認すべき項目をまとめています。

## 事前準備チェックリスト

### 1. Google Cloud プロジェクト設定

- [ ] **APIの有効化**
  ```bash
  gcloud services enable secretmanager.googleapis.com
  gcloud services enable cloudbuild.googleapis.com
  gcloud services enable run.googleapis.com
  gcloud services enable containerregistry.googleapis.com
  ```

- [ ] **プロジェクトIDの確認**
  ```bash
  gcloud config get-value project
  ```

### 2. Secret Manager設定

- [ ] **シークレットの作成**
  ```bash
  echo "your_openai_api_key" | gcloud secrets create OPENAI_API_KEY --data-file=-
  echo "your_upstash_url" | gcloud secrets create UPSTASH_VECTOR_REST_URL --data-file=-
  echo "your_upstash_token" | gcloud secrets create UPSTASH_VECTOR_REST_TOKEN --data-file=-
  ```

- [ ] **権限の設定**
  ```bash
  PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
  
  gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.admin"
  
  gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
  ```

### 3. ファイル準備

- [ ] **`.gcloudignore`ファイルの作成**
  - 不要なファイル（node_modules、.git等）を除外
  - テンプレートは`docs/deployment/cloud-run-troubleshooting.md`を参照

- [ ] **`cloudbuild.yaml`の確認**
  - 環境変数が適切なYAML形式で定義されている
  - シークレットの参照が正しい
  - 特殊文字を含む値が引用符で囲まれている

### 4. デプロイメント前テスト

- [ ] **ローカルでのDockerビルドテスト**
  ```bash
  docker build -f backend/Dockerfile -t test-backend .
  ```

- [ ] **環境変数ファイルの構文チェック**
  ```bash
  # YAMLファイルの構文確認
  python -c "import yaml; yaml.safe_load(open('cloud-run-env.yaml'))"
  ```

## デプロイメント実行

### 1. Cloud Buildの実行

```bash
gcloud builds submit --config cloudbuild.yaml . --project=$(gcloud config get-value project)
```

### 2. デプロイメント確認

- [ ] **ビルド状況の確認**
  ```bash
  gcloud builds list --limit=1
  ```

- [ ] **Cloud Runサービスの確認**
  ```bash
  gcloud run services describe gamechat-ai-backend --region=asia-northeast1
  ```

- [ ] **ヘルスチェック**
  ```bash
  SERVICE_URL=$(gcloud run services describe gamechat-ai-backend --region=asia-northeast1 --format="value(status.url)")
  curl -f "${SERVICE_URL}/health"
  ```

## トラブルシューティング

### よくあるエラーと対処法

| エラータイプ | 対処法 |
|------------|--------|
| API未有効化エラー | `gcloud services enable [API_NAME]` |
| 権限不足エラー | IAMポリシーの確認・修正 |
| 環境変数構文エラー | YAML形式の確認、引用符の追加 |
| ビルドサイズ過大 | `.gcloudignore`でファイル除外 |

### 詳細なトラブルシューティング

詳細については`docs/deployment/cloud-run-troubleshooting.md`を参照してください。

## 成功確認項目

デプロイメントが成功したら、以下を確認：

- [ ] Cloud Runサービスが稼働中
- [ ] 環境変数が正しく設定されている
- [ ] シークレットが正しくマウントされている
- [ ] ヘルスチェックエンドポイントが応答する
- [ ] CORS設定が適切に動作する

## 関連ドキュメント

- [Cloud Run OpenAI API Key 設定ガイド](./cloud-run-openai-setup.md)
- [Cloud Run トラブルシューティングガイド](./cloud-run-troubleshooting.md)
- [Firebase Hosting との連携](./firebase-hosting-cloud-run.md)
