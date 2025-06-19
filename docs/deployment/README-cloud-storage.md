# Cloud Storage移行後のデプロイメント手順

GameChat AIはGoogle Cloud Storageを使用してデータを管理します。以下の手順で環境を構築してください。

## 🚀 クイックスタート

### 1. Google Cloud Storage準備
```bash
# バケット作成
./scripts/deployment/create_gcs_bucket.sh

# データアップロード
python scripts/deployment/upload_data_to_gcs.py
```

### 2. Cloud Run設定
```bash
# サービスアカウント権限付与
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# 環境変数設定
gcloud run services update gamechat-ai-backend \
  --region=asia-northeast1 \
  --set-env-vars="GCS_BUCKET_NAME=gamechat-ai-data,GCS_PROJECT_ID=YOUR_PROJECT_ID"
```

### 3. デプロイ
```bash
# 従来通りのデプロイ
gcloud builds submit --config cloudbuild.yaml
```

## 📁 ファイル構成変更

### Cloud Storage (本番環境)
```
gs://gamechat-ai-data/
├── data/
│   ├── data.json              # メインデータ
│   ├── convert_data.json      # 変換データ
│   ├── embedding_list.jsonl   # 埋め込みデータ
│   └── query_data.json        # クエリデータ
```

### ローカル開発環境
```
project-root/
├── data/                      # 従来通り
│   ├── data.json
│   ├── convert_data.json
│   ├── embedding_list.jsonl
│   └── query_data.json
```

## 🔧 トラブルシューティング

詳細な移行手順とトラブルシューティングは以下を参照:
- [Cloud Storage移行ガイド](./docs/deployment/cloud-storage-migration-guide.md)

## 💡 開発者向け情報

### 新しいStorageService
- GCSとローカルファイルの自動切り替え
- 自動フォールバック機能
- キャッシュ管理

### 環境変数
```bash
# 必須（本番環境）
GCS_BUCKET_NAME=gamechat-ai-data
GCS_PROJECT_ID=your-project-id

# オプション
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```
