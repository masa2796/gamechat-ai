#!/bin/bash

# GameChat AI Backend - Cloud Run Deployment Script
# Artifact Registry を使用したCloud Runデプロイメント

set -e  # エラー時に停止

# 設定変数
PROJECT_ID="gamechat-ai"
REGION="asia-northeast1"
SERVICE_NAME="gamechat-ai-backend"
REPOSITORY_NAME="gamechat-ai-backend"
IMAGE_NAME="backend"
DOCKERFILE_PATH="backend/Dockerfile"

# Artifact Registry のフルイメージパス
ARTIFACT_REGISTRY_URL="asia-northeast1-docker.pkg.dev"
FULL_IMAGE_PATH="${ARTIFACT_REGISTRY_URL}/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME}"

# 色付きログ用の関数
log_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # gcloudコマンドの確認
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI がインストールされていません"
        exit 1
    fi
    
    # Dockerコマンドの確認
    if ! command -v docker &> /dev/null; then
        log_error "Docker がインストールされていません"
        exit 1
    fi
    
    # Google Cloud認証確認
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Google Cloud認証が必要です: gcloud auth login"
        exit 1
    fi
    
    # プロジェクト設定確認
    CURRENT_PROJECT=$(gcloud config get-value project)
    if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
        log_warning "現在のプロジェクト: $CURRENT_PROJECT"
        log_info "プロジェクトを $PROJECT_ID に切り替えます"
        gcloud config set project $PROJECT_ID
    fi
    
    # Docker認証確認
    if ! gcloud auth configure-docker $ARTIFACT_REGISTRY_URL --quiet; then
        log_error "Docker認証に失敗しました"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# Dockerイメージのビルド
build_image() {
    log_info "Dockerイメージをビルド中..."
    
    # タイムスタンプベースのタグを生成
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    BUILD_TAG="${FULL_IMAGE_PATH}:${TIMESTAMP}"
    LATEST_TAG="${FULL_IMAGE_PATH}:latest"
    
    # Linux/amd64プラットフォーム用にビルド
    docker build \
        --platform linux/amd64 \
        -f $DOCKERFILE_PATH \
        -t $BUILD_TAG \
        -t $LATEST_TAG \
        .
    
    log_success "イメージビルド完了: $BUILD_TAG"
    
    # グローバル変数として保存
    export BUILD_TAG
    export LATEST_TAG
}

# Artifact Registryにプッシュ
push_image() {
    log_info "Artifact Registryにイメージをプッシュ中..."
    
    # Build tagged image
    docker push $BUILD_TAG
    
    # Latest image
    docker push $LATEST_TAG
    
    log_success "イメージプッシュ完了"
}

# Cloud Runにデプロイ
deploy_to_cloud_run() {
    log_info "Cloud Runにデプロイ中..."
    
    gcloud run deploy $SERVICE_NAME \
        --image=$BUILD_TAG \
        --region=$REGION \
        --platform=managed \
        --set-env-vars=ENVIRONMENT=production \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --max-instances=10 \
        --port=8000 \
        --timeout=300 \
        --quiet
    
    # サービスURLを取得
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --format="value(status.url)")
    
    log_success "デプロイ完了!"
    log_info "サービスURL: $SERVICE_URL"
    
    # グローバル変数として保存
    export SERVICE_URL
}

# ヘルスチェック
health_check() {
    log_info "ヘルスチェック実行中..."
    
    # サービスの起動を待つ
    sleep 30
    
    # ヘルスチェックエンドポイントを確認
    HEALTH_URL="${SERVICE_URL}/health"
    
    # 最大5回リトライ
    for i in {1..5}; do
        log_info "ヘルスチェック試行 $i/5..."
        
        if curl -f -s "$HEALTH_URL" > /dev/null; then
            log_success "ヘルスチェック通過"
            return 0
        fi
        
        if [ $i -lt 5 ]; then
            log_warning "ヘルスチェック失敗、10秒後に再試行..."
            sleep 10
        fi
    done
    
    log_error "ヘルスチェック失敗"
    return 1
}

# ロールバック機能
rollback() {
    log_warning "ロールバックを実行中..."
    
    # 前回のリビジョンを取得
    PREVIOUS_REVISION=$(gcloud run revisions list \
        --service=$SERVICE_NAME \
        --region=$REGION \
        --limit=2 \
        --format="value(metadata.name)" | tail -n 1)
    
    if [ -z "$PREVIOUS_REVISION" ]; then
        log_error "ロールバック可能なリビジョンが見つかりません"
        return 1
    fi
    
    # トラフィックを前回のリビジョンに向ける
    gcloud run services update-traffic $SERVICE_NAME \
        --to-revisions=$PREVIOUS_REVISION=100 \
        --region=$REGION \
        --quiet
    
    log_success "ロールバック完了: $PREVIOUS_REVISION"
}

# クリーンアップ
cleanup() {
    log_info "古いイメージをクリーンアップ中..."
    
    # 古いイメージを削除（最新の5つを保持）
    OLD_IMAGES=$(gcloud artifacts docker images list $FULL_IMAGE_PATH \
        --format="value(IMAGE)" \
        --limit=100 | tail -n +6)
    
    if [ -n "$OLD_IMAGES" ]; then
        echo "$OLD_IMAGES" | while read -r image; do
            gcloud artifacts docker images delete "$image" --quiet || true
        done
        log_success "古いイメージを削除しました"
    else
        log_info "削除対象の古いイメージはありません"
    fi
}

# メイン実行部分
main() {
    log_info "GameChat AI Backend デプロイメント開始"
    
    # 前提条件チェック
    check_prerequisites
    
    # イメージビルド
    build_image
    
    # イメージプッシュ
    push_image
    
    # Cloud Runデプロイ
    deploy_to_cloud_run
    
    # ヘルスチェック
    if ! health_check; then
        log_error "ヘルスチェックに失敗しました"
        read -p "ロールバックしますか？ (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        fi
        exit 1
    fi
    
    # クリーンアップ
    cleanup
    
    log_success "デプロイメント完了!"
    log_info "サービスURL: $SERVICE_URL"
}

# エラーハンドリング
trap 'log_error "デプロイメント中にエラーが発生しました"' ERR

# スクリプトが直接実行された場合
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
