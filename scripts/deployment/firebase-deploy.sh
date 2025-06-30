#!/bin/bash

# GameChat AI Firebase Hosting デプロイスクリプト
# Firebase Hosting + Cloud Run デプロイ自動化

set -e

echo "🚀 GameChat AI デプロイ開始"
echo "=============================="

# 色付きログ関数
log_info() {
    echo -e "\033[36m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

log_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

# プロジェクト設定
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"gamechat-ai"}
REGION="asia-northeast1"
SERVICE_NAME="gamechat-ai-backend"

# 本番環境用環境変数を明示的に設定
export ENVIRONMENT=production

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # Firebase CLI チェック
    if ! command -v firebase &> /dev/null; then
        log_error "Firebase CLI がインストールされていません"
        log_info "インストール: npm install -g firebase-tools"
        exit 1
    fi
    
    # gcloud CLI チェック
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI がインストールされていません"
        log_info "インストール: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Docker チェック
    if ! command -v docker &> /dev/null; then
        log_error "Docker がインストールされていません"
        exit 1
    fi
    
    # Node.js チェック
    if ! command -v node &> /dev/null; then
        log_error "Node.js がインストールされていません"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# Firebase プロジェクト初期化
init_firebase() {
    log_info "Firebase プロジェクトを初期化中..."
    
    # Firebase ログイン確認
    if ! firebase projects:list &> /dev/null; then
        log_info "Firebase にログイン中..."
        firebase login
    fi
    
    # Firebase プロジェクト設定
    if [ ! -f ".firebaserc" ]; then
        log_info "Firebase プロジェクトを設定中..."
        firebase use --add "$PROJECT_ID"
    fi
    
    log_success "Firebase プロジェクト初期化完了"
}

# バックエンド（Cloud Run）デプロイ
deploy_backend() {
    log_info "バックエンドを Cloud Run にデプロイ中..."
    
    # Google Cloud プロジェクト設定
    gcloud config set project "$PROJECT_ID"
    
    # Container Registry API 有効化
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    
    # Docker イメージビルド & プッシュ
    log_info "Docker イメージをビルド中..."
    docker build --platform linux/amd64 --build-arg BUILD_ENV=production -f backend/Dockerfile -t "gcr.io/$PROJECT_ID/$SERVICE_NAME" .
    
    log_info "Container Registry にプッシュ中..."
    docker push "gcr.io/$PROJECT_ID/$SERVICE_NAME"
    
    # Cloud Run デプロイ
    log_info "Cloud Run サービスをデプロイ中..."
    gcloud beta run deploy "$SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --update-secrets BACKEND_OPENAI_API_KEY=BACKEND_OPENAI_API_KEY:latest,UPSTASH_VECTOR_REST_TOKEN=BACKEND_UPSTASH_VECTOR_REST_TOKEN:latest,BACKEND_API_KEY_PRODUCTION=BACKEND_API_KEY_PRODUCTION:latest,API_KEY_DEVELOPMENT=BACKEND_API_KEY_DEVELOPMENT:latest,API_KEY_FRONTEND=BACKEND_API_KEY_FRONTEND:latest,BACKEND_JWT_SECRET_KEY=BACKEND_JWT_SECRET_KEY:latest,BACKEND_RECAPTCHA_SECRET=BACKEND_RECAPTCHA_SECRET:latest \
    --set-env-vars ENVIRONMENT=production,BACKEND_ENVIRONMENT=production,BACKEND_LOG_LEVEL=INFO,BACKEND_BCRYPT_ROUNDS=12,BACKEND_CORS_ORIGINS=https://gamechat-ai.web.app,GCS_BUCKET_NAME=gamechat-ai-data,GCS_PROJECT_ID=$PROJECT_ID \
    --quiet
    
    # Cloud Run URL 取得
    BACKEND_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    log_success "バックエンドデプロイ完了: $BACKEND_URL"
    
    # firebase.json の rewrite URL 更新
    log_info "Firebase設定を更新中..."
    sed -i.bak "s|\"serviceId\": \".*\"|\"serviceId\": \"$SERVICE_NAME\"|g" firebase.json
    
    echo "$BACKEND_URL" > .backend_url
}

# フロントエンド（Firebase Hosting）ビルド & デプロイ
deploy_frontend() {
    log_info "フロントエンドをFirebase Hosting用にビルド中..."
    
    cd frontend
    
    # 依存関係インストール
    npm ci
    
    # Firebase Hosting用環境変数を読み込む
    if [ -f ".env.firebase" ]; then
        log_info "Firebase Hosting用環境変数を読み込み中..."
        
        # .env.firebase のすべての環境変数を export（安全な方法）
        set -o allexport
        source .env.firebase
        set +o allexport

        FIREBASE_API_KEY=$NEXT_PUBLIC_API_KEY
    fi


    # バックエンドURLを動的に設定
    if [ -f "../.backend_url" ]; then
        BACKEND_URL=$(cat ../.backend_url)
        # .env.production ではなく .env.firebase を直接編集
        sed -i.bak '/^NEXT_PUBLIC_API_URL=/d' .env.firebase
        echo "NEXT_PUBLIC_API_URL=$BACKEND_URL" >> .env.firebase
        sed -i.bak '/^NEXT_PUBLIC_API_KEY=/d' .env.firebase
        echo "NEXT_PUBLIC_API_KEY=$FIREBASE_API_KEY" >> .env.firebase
    fi
        
    # Next.js Firebase Hosting用ビルド
    log_info "静的サイト生成を実行中..."
    npm run build:firebase
    
    # Firebase Hosting用の静的エクスポート確認
    if [ ! -d "out" ]; then
        log_error "静的エクスポート（out）ディレクトリが見つかりません"
        log_error "Next.js設定を確認してください: output: 'export'"
        exit 1
    fi
    
    cd ..
    
    # Firebase Hosting デプロイ
    log_info "Firebase Hosting にデプロイ中..."
    firebase deploy --only hosting
    
    log_success "フロントエンドデプロイ完了"
}

# ヘルスチェック
health_check() {
    log_info "デプロイ後ヘルスチェック実行中..."
    
    # バックエンドヘルスチェック
    if [ -f ".backend_url" ]; then
        BACKEND_URL=$(cat .backend_url)
        if curl -f "$BACKEND_URL/health" &> /dev/null; then
            log_success "バックエンド正常稼働中"
        else
            log_warning "バックエンドヘルスチェック失敗"
        fi
    fi
    
    # フロントエンドURL取得
    FRONTEND_URL=$(firebase hosting:channel:list | grep "live" | awk '{print $4}' | head -1)
    if [ -n "$FRONTEND_URL" ]; then
        log_success "フロントエンド URL: $FRONTEND_URL"
        
        # フロントエンドヘルスチェック
        if curl -f "$FRONTEND_URL" &> /dev/null; then
            log_success "フロントエンド正常稼働中"
        else
            log_warning "フロントエンドヘルスチェック失敗"
        fi
    fi
}

# クリーンアップ
cleanup() {
    log_info "一時ファイルをクリーンアップ中..."
    rm -f .backend_url
    # .env.production の削除は不要
    log_success "クリーンアップ完了"
}

# メイン実行
main() {
    case "${1:-all}" in
        "backend")
            check_prerequisites
            init_firebase
            deploy_backend
            ;;
        "frontend")
            check_prerequisites
            init_firebase
            deploy_frontend
            ;;
        "health")
            health_check
            ;;
        "all")
            check_prerequisites
            init_firebase
            deploy_backend
            deploy_frontend
            health_check
            cleanup
            ;;
        *)
            echo "使用方法: $0 [backend|frontend|health|all]"
            echo "  backend  - バックエンドのみデプロイ"
            echo "  frontend - フロントエンドのみデプロイ"
            echo "  health   - ヘルスチェックのみ実行"
            echo "  all      - 全体デプロイ（デフォルト）"
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"

echo ""
echo "🎉 GameChat AI デプロイ完了！"
echo "=============================="
