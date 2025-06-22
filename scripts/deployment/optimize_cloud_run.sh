#!/bin/bash

# Cloud Run パフォーマンス最適化設定スクリプト
# 30秒タイムアウト問題解決のための設定調整

set -e

PROJECT_ID="${PROJECT_ID:-gamechat-ai}"
SERVICE_NAME="${SERVICE_NAME:-gamechat-ai-backend}"
REGION="${REGION:-asia-northeast1}"

echo "🚀 Cloud Run パフォーマンス最適化開始"
echo "=================================="
echo "プロジェクト: $PROJECT_ID"
echo "サービス: $SERVICE_NAME"
echo "リージョン: $REGION"
echo ""

# 1. 現在の設定確認
echo "📊 現在の設定確認..."
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="table(metadata.name,spec.template.spec.containers[0].resources.limits,spec.template.spec.containerConcurrency,spec.template.spec.timeoutSeconds)"

echo ""

# 2. 最適化設定の適用
echo "⚡ パフォーマンス最適化設定を適用中..."

gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --max-instances=15 \
  --min-instances=1 \
  --concurrency=50 \
  --cpu-boost \
  --execution-environment=gen2 \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,CACHE_SIZE_MB=200,MAX_CONCURRENT_TASKS=5"

echo ""

# 3. Cloud Run プロキシのタイムアウト設定
echo "🔧 プロキシタイムアウト設定..."
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --add-cloudsql-instances="" \
  --clear-cloudsql-instances

# 4. VPC コネクタ設定（必要に応じて）
if [ ! -z "$VPC_CONNECTOR" ]; then
  echo "🌐 VPC コネクタ設定..."
  gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --vpc-connector=$VPC_CONNECTOR \
    --vpc-egress=private-ranges-only
fi

# 5. カナリアデプロイメント設定
echo "🚦 カナリアデプロイメント設定..."
gcloud run services update-traffic $SERVICE_NAME \
  --region=$REGION \
  --to-latest

# 6. 設定後の確認
echo "✅ 設定完了後の確認..."
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="table(metadata.name,spec.template.spec.containers[0].resources.limits,spec.template.spec.containerConcurrency,spec.template.spec.timeoutSeconds)"

echo ""

# 7. ヘルスチェック
echo "🏥 ヘルスチェック実行..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

if [ ! -z "$SERVICE_URL" ]; then
  echo "サービスURL: $SERVICE_URL"
  
  # ヘルスチェック
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $SERVICE_URL/health || echo "000")
  
  if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ ヘルスチェック成功 (HTTP $HTTP_STATUS)"
  else
    echo "⚠️ ヘルスチェック失敗 (HTTP $HTTP_STATUS)"
  fi
  
  # パフォーマンステスト
  echo "⚡ パフォーマンステスト実行..."
  RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" $SERVICE_URL/health)
  echo "応答時間: ${RESPONSE_TIME}s"
  
  if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo "✅ 応答時間良好"
  else
    echo "⚠️ 応答時間が遅い可能性があります"
  fi
fi

echo ""
echo "🎉 Cloud Run 最適化完了!"
echo ""
echo "📋 推奨監視項目:"
echo "- 応答時間: target < 5秒"
echo "- エラー率: target < 1%"
echo "- CPU使用率: target < 70%"
echo "- メモリ使用率: target < 80%"
echo "- 同時接続数: target < 40"
echo ""
echo "📊 監視コマンド:"
echo "gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit=50"
echo ""
echo "💡 追加最適化のために以下を検討してください:"
echo "1. アプリケーションレベルでのキャッシュ強化"
echo "2. データベースクエリの最適化"
echo "3. 非同期処理の活用"
echo "4. ストリーミングレスポンスの実装"
