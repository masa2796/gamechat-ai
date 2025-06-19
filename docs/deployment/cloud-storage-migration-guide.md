# Cloud Storage移行ガイド

## 概要

GameChat AIのデータ管理をローカルファイルシステムからGoogle Cloud Storageへ移行する手順です。これにより、Cloud Run本番環境でのデータ管理が柔軟になり、CI/CDパイプラインが簡素化されます。

## 🎯 実装内容

### 新機能
- **StorageService**: GCSとローカルファイルシステムの統合管理
- **自動フォールバック**: GCS → ローカルファイル → エラーハンドリング
- **キャッシュ機能**: Cloud Run環境で`/tmp`にキャッシュ
- **環境別対応**: ローカル開発とCloud本番での自動切り替え

### アーキテクチャ変更
```
従来: アプリ → ローカルファイル
新方式: アプリ → StorageService → GCS（本番）/ ローカル（開発）
```

## 🚀 移行手順

### 1. Google Cloud Storage設定

#### 1.1 バケット作成
```bash
# 環境変数設定（オプション）
export GCS_BUCKET_NAME="gamechat-ai-data"
export GCS_REGION="asia-northeast1"
export GCS_PROJECT_ID="your-project-id"

# バケット作成スクリプト実行
./scripts/deployment/create_gcs_bucket.sh
```

#### 1.2 手動でバケット作成する場合
```bash
# バケット作成
gsutil mb -l asia-northeast1 gs://gamechat-ai-data

# セキュリティ設定
gsutil uniformbucketlevelaccess set on gs://gamechat-ai-data
```

### 2. データファイルのアップロード

#### 2.1 自動アップロード（推奨）
```bash
# データアップロードスクリプト実行
python scripts/deployment/upload_data_to_gcs.py
```

#### 2.2 手動アップロード
```bash
# 個別ファイルアップロード
gsutil cp data/data.json gs://gamechat-ai-data/data/
gsutil cp data/convert_data.json gs://gamechat-ai-data/data/
gsutil cp data/embedding_list.jsonl gs://gamechat-ai-data/data/
gsutil cp data/query_data.json gs://gamechat-ai-data/data/

# 一括アップロード
gsutil -m cp -r data/* gs://gamechat-ai-data/data/
```

### 3. Cloud Run権限設定

#### 3.1 サービスアカウント確認
```bash
# Cloud Runサービスのサービスアカウントを確認
gcloud run services describe gamechat-ai-backend \
  --region=asia-northeast1 \
  --format="value(spec.template.spec.serviceAccountName)"
```

#### 3.2 権限付与
```bash
# Cloud Runサービスアカウントに権限付与
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:your-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

### 4. Cloud Run環境変数設定

#### 4.1 環境変数追加
```bash
# Cloud Runサービス更新
gcloud run services update gamechat-ai-backend \
  --region=asia-northeast1 \
  --set-env-vars="GCS_BUCKET_NAME=gamechat-ai-data,GCS_PROJECT_ID=your-project-id"
```

#### 4.2 cloudbuild.yamlでの設定
```yaml
# cloud-run-env.yamlに追加済み
GCS_BUCKET_NAME: "gamechat-ai-data"
GCS_PROJECT_ID: "your-project-id"
```

## 🔧 ローカル開発環境

### 従来通りの開発
ローカル環境では従来通り`data/`ディレクトリからファイルを読み込みます。

```bash
# ローカル開発時は変更なし
cd /path/to/gamechat-ai
python -m backend.app.main
```

### GCSテスト（オプション）
```bash
# ローカルでGCSを使用したい場合
export ENVIRONMENT="production"
export GCS_BUCKET_NAME="gamechat-ai-data"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

python -m backend.app.main
```

## 📊 動作確認

### 1. ログ確認
```bash
# Cloud Runログの確認
gcloud logs read --service=gamechat-ai-backend --region=asia-northeast1

# StorageService関連ログをフィルタ
gcloud logs read --service=gamechat-ai-backend \
  --filter="jsonPayload.component=\"storage_service\""
```

### 2. ヘルスチェック
```bash
# アプリケーションヘルスチェック
curl https://your-cloud-run-url/health

# ストレージ状態確認（デバッグエンドポイント追加推奨）
curl https://your-cloud-run-url/debug/storage-status
```

### 3. データ確認
```bash
# GCS内のデータ確認
gsutil ls -la gs://gamechat-ai-data/data/

# ファイル内容確認
gsutil cat gs://gamechat-ai-data/data/data.json | head -20
```

## 🛠️ トラブルシューティング

### よくある問題

#### 1. GCS接続エラー
```
エラー: Cloud Storage初期化に失敗
```

**解決方法:**
```bash
# 1. 認証確認
gcloud auth list

# 2. プロジェクト設定確認
gcloud config get-value project

# 3. API有効化確認
gcloud services list --enabled | grep storage
```

#### 2. 権限エラー
```
エラー: GCSファイルが見つかりません
```

**解決方法:**
```bash
# サービスアカウント権限確認
gcloud projects get-iam-policy your-project-id \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:your-service-account@your-project-id.iam.gserviceaccount.com"
```

#### 3. ファイルアップロードエラー
```
エラー: アップロード失敗
```

**解決方法:**
```bash
# 1. ファイル存在確認
ls -la data/

# 2. バケット書き込み権限確認（アップロード時）
gsutil iam get gs://gamechat-ai-data

# 3. 手動アップロードテスト
gsutil cp data/data.json gs://gamechat-ai-data/test/
```

## 📈 パフォーマンス考慮事項

### Cloud Run制限
- **メモリ制限**: 最大2GB（`/tmp` キャッシュ含む）
- **一時ストレージ**: `/tmp` は最大512MB
- **起動時間**: 初回データダウンロードで数秒の遅延

### 最適化
```python
# キャッシュクリア（必要時）
storage_service.clear_cache()

# キャッシュ情報確認
cache_info = storage_service.get_cache_info()
```

## 🔄 CI/CD更新内容

### cloudbuild.yaml変更点
1. **データファイル不要**: CIビルド時にdata/は不要
2. **プレースホルダー**: 最小限のプレースホルダーファイルで対応
3. **環境変数追加**: GCS関連設定追加

### Dockerfile変更点
1. **COPYコマンド削除**: `data/`ディレクトリのコピー不要
2. **キャッシュディレクトリ**: `/tmp/gamechat-data`作成
3. **プレースホルダー**: CI/CD用の最小ファイル

## 🔒 セキュリティ考慮事項

### アクセス制御
- **サービスアカウント**: 最小権限の原則
- **バケットアクセス**: ユニフォームバケットレベルアクセス
- **ネットワーク**: VPCオプション（高セキュリティ要件時）

### データ保護
- **暗号化**: Google Cloud標準暗号化
- **バックアップ**: バージョニング有効化
- **監査ログ**: Cloud Audit Logs有効化

## 📋 チェックリスト

### 事前準備
- [ ] Google Cloud SDK インストール・認証済み
- [ ] プロジェクトID確認済み
- [ ] データファイル準備済み（`data/`ディレクトリ）

### 移行作業
- [ ] GCSバケット作成
- [ ] データファイルアップロード
- [ ] サービスアカウント権限設定
- [ ] Cloud Run環境変数設定
- [ ] アプリケーションデプロイ

### 動作確認
- [ ] ローカル開発環境動作確認
- [ ] Cloud Run本番環境動作確認
- [ ] ログ出力確認
- [ ] エラーハンドリング確認

## 📚 参考資料

- [Google Cloud Storage公式ドキュメント](https://cloud.google.com/storage/docs)
- [Cloud Run環境での認証](https://cloud.google.com/run/docs/securing/service-identity)
- [IAMとアクセス制御](https://cloud.google.com/storage/docs/access-control)
