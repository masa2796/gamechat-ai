#!/bin/bash
# Google Cloud Storageバケット作成スクリプト

set -e

# 設定
BUCKET_NAME="${GCS_BUCKET_NAME:-gamechat-ai-data}"
REGION="${GCS_REGION:-asia-northeast1}"
PROJECT_ID="${GCS_PROJECT_ID:-gamechat-ai}"

echo "🚀 Google Cloud Storageバケット作成スクリプト"
echo "=============================================="
echo "バケット名: $BUCKET_NAME"
echo "リージョン: $REGION"
echo "プロジェクトID: $PROJECT_ID"
echo ""

# プロジェクトの設定
echo "📋 プロジェクトの設定..."
gcloud config set project "$PROJECT_ID"

# API有効化
echo "🔧 Cloud Storage APIを有効化..."
gcloud services enable storage-api.googleapis.com

# バケットの存在確認
if gsutil ls -b "gs://$BUCKET_NAME" > /dev/null 2>&1; then
    echo "✅ バケット gs://$BUCKET_NAME は既に存在します"
else
    echo "📦 バケットを作成中..."
    gsutil mb -l "$REGION" "gs://$BUCKET_NAME"
    echo "✅ バケット gs://$BUCKET_NAME を作成しました"
fi

# バケットの設定（本番環境推奨設定）
echo "⚙️  バケット設定を適用中..."

# オブジェクトのライフサイクル設定（オプション）
cat > /tmp/lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 365,
          "matchesPrefix": ["logs/", "temp/"]
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/lifecycle.json "gs://$BUCKET_NAME"
rm /tmp/lifecycle.json

# バケットの公開アクセス無効化（セキュリティ）
echo "🔒 セキュリティ設定を適用中..."
gsutil iam ch allUsers:objectViewer "gs://$BUCKET_NAME" 2>/dev/null || true
gsutil iam ch allAuthenticatedUsers:objectViewer "gs://$BUCKET_NAME" 2>/dev/null || true

# ユニフォームバケットレベルアクセス有効化
gsutil uniformbucketlevelaccess set on "gs://$BUCKET_NAME"

echo ""
echo "🎉 バケット作成・設定が完了しました!"
echo ""
echo "次のステップ:"
echo "1. データファイルをアップロード:"
echo "   python scripts/deployment/upload_data_to_gcs.py"
echo ""
echo "2. Cloud Runサービスアカウントに権限を付与:"
echo "   gcloud projects add-iam-policy-binding $PROJECT_ID \\"
echo "     --member=\"serviceAccount:SERVICE_ACCOUNT_EMAIL\" \\"
echo "     --role=\"roles/storage.objectViewer\""
echo ""
echo "3. Cloud Run環境変数を設定:"
echo "   GCS_BUCKET_NAME=$BUCKET_NAME"
echo "   GCS_PROJECT_ID=$PROJECT_ID"
echo ""

# バケット情報の表示
echo "📋 バケット情報:"
gsutil ls -L "gs://$BUCKET_NAME"
