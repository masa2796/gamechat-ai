#!/bin/bash

# Firebase Hosting 移行スクリプト
# Cloud Run から Firebase Hosting への移行を自動化

set -e

echo "🔥 Firebase Hosting 移行開始"
echo "==============================="

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

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # Firebase CLI チェック
    if ! command -v firebase &> /dev/null; then
        log_error "Firebase CLI がインストールされていません"
        log_info "インストール: npm install -g firebase-tools"
        exit 1
    fi
    
    # Node.js & npm チェック
    if ! command -v npm &> /dev/null; then
        log_error "npm がインストールされていません"
        exit 1
    fi
    
    # プロジェクトディレクトリチェック
    if [ ! -f "firebase.json" ]; then
        log_error "firebase.json が見つかりません"
        log_info "プロジェクトルートで実行してください"
        exit 1
    fi
    
    if [ ! -d "frontend" ]; then
        log_error "frontend ディレクトリが見つかりません"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# Firebase認証チェック
check_firebase_auth() {
    log_info "Firebase認証をチェック中..."
    
    if ! firebase projects:list &> /dev/null; then
        log_warning "Firebase認証が必要です"
        log_info "Firebase にログインしてください"
        firebase login
    fi
    
    log_success "Firebase認証確認完了"
}

# Next.js設定確認
check_nextjs_config() {
    log_info "Next.js設定を確認中..."
    
    if ! grep -q "output.*export" frontend/next.config.js; then
        log_error "Next.js設定が Firebase Hosting 用に設定されていません"
        log_info "next.config.js で output: 'export' を設定してください"
        exit 1
    fi
    
    log_success "Next.js設定確認完了"
}

# 環境変数ファイル作成
setup_environment() {
    log_info "環境変数ファイルを設定中..."
    
    if [ ! -f "frontend/.env.firebase" ]; then
        log_warning "frontend/.env.firebase が見つかりません"
        log_info "Firebase Hosting用環境変数ファイルを作成します"
        
        cp frontend/.env.firebase.example frontend/.env.firebase
        
        log_warning "frontend/.env.firebase を編集して、実際の値を設定してください"
        log_info "特に NEXT_PUBLIC_SITE_URL をFirebaseプロジェクトのURLに変更してください"
        read -p "設定が完了したらEnterを押してください..."
    fi
    
    log_success "環境変数ファイル設定完了"
}

# フロントエンドビルド
build_frontend() {
    log_info "フロントエンドをビルド中..."
    
    cd frontend
    
    # 依存関係インストール
    log_info "依存関係をインストール中..."
    npm ci
    
    # 環境変数設定
    if [ -f ".env.firebase" ]; then
        cp .env.firebase .env.production
    fi
    
    # ビルド実行
    log_info "静的サイト生成中..."
    npm run build:firebase
    
    # 出力確認
    if [ ! -d "out" ]; then
        log_error "静的エクスポートが失敗しました"
        exit 1
    fi
    
    log_info "生成ファイル数: $(find out -type f | wc -l)"
    cd ..
    
    log_success "フロントエンドビルド完了"
}

# Firebase Hosting デプロイ
deploy_to_firebase() {
    log_info "Firebase Hosting にデプロイ中..."
    
    # Firebase プロジェクト確認
    CURRENT_PROJECT=$(firebase use --json 2>/dev/null | jq -r '.result.id' 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_PROJECT" ]; then
        log_warning "Firebase プロジェクトが設定されていません"
        log_info "利用可能なプロジェクト:"
        firebase projects:list
        echo
        read -p "プロジェクトIDを入力してください: " PROJECT_ID
        firebase use "$PROJECT_ID"
    fi
    
    # デプロイ実行
    firebase deploy --only hosting
    
    log_success "Firebase Hosting デプロイ完了"
}

# 動作確認
verify_deployment() {
    log_info "デプロイ済みサイトを確認中..."
    
    # サイトURLを取得
    SITE_URL=$(firebase hosting:sites:list --json 2>/dev/null | jq -r '.[0].defaultUrl' 2>/dev/null || echo "")
    
    if [ -n "$SITE_URL" ]; then
        log_success "デプロイ完了: $SITE_URL"
        log_info "ブラウザで動作確認してください"
        
        # macOS の場合、ブラウザで開く
        if command -v open &> /dev/null; then
            read -p "ブラウザで開きますか？ (y/N): " OPEN_BROWSER
            if [ "$OPEN_BROWSER" = "y" ] || [ "$OPEN_BROWSER" = "Y" ]; then
                open "$SITE_URL"
            fi
        fi
    else
        log_warning "サイトURLの取得に失敗しました"
        log_info "Firebase Console で確認してください"
    fi
}

# メイン処理
main() {
    check_prerequisites
    check_firebase_auth
    check_nextjs_config
    setup_environment
    build_frontend
    deploy_to_firebase
    verify_deployment
    
    echo
    log_success "🎉 Firebase Hosting 移行完了!"
    echo
    echo "次のステップ:"
    echo "1. ブラウザでサイトの動作確認"
    echo "2. API 連携の動作確認"
    echo "3. カスタムドメインの設定（必要に応じて）"
    echo "4. 継続的デプロイの設定"
}

# スクリプト実行
main "$@"
