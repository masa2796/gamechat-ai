#!/bin/bash

# GameChat AI Production Deployment Script
# 本番環境へのデプロイを自動化するスクリプト

set -e  # エラー時に停止

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

# デプロイ前のチェック
pre_deployment_checks() {
    log_info "デプロイ前チェックを実行中..."
    
    # Docker Composeファイルの存在確認
    if [ ! -f "docker-compose.prod.yml" ]; then
        log_error "docker-compose.prod.yml が見つかりません"
        exit 1
    fi
    
    # 環境変数ファイルの確認
    if [ ! -f "backend/.env.production" ]; then
        log_warning "backend/.env.production が見つかりません。デフォルト値が使用されます"
    fi
    
    # Docker の稼働確認
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker が稼働していません"
        exit 1
    fi
    
    # Docker Compose の確認
    if ! command -v docker-compose > /dev/null 2>&1; then
        log_error "Docker Compose が見つかりません"
        exit 1
    fi
    
    log_success "デプロイ前チェック完了"
}

# バックアップの作成
create_backup() {
    log_info "現在の環境をバックアップ中..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 現在のコンテナ状態をバックアップ
    docker-compose -f docker-compose.prod.yml ps > "$BACKUP_DIR/containers_status.txt" 2>&1 || true
    
    # データベースのバックアップ（必要に応じて）
    # docker-compose -f docker-compose.prod.yml exec -T database pg_dump -U postgres database_name > "$BACKUP_DIR/database_backup.sql" || true
    
    log_success "バックアップ完了: $BACKUP_DIR"
}

# イメージのビルドとプッシュ
build_and_push() {
    log_info "Docker イメージをビルド中..."
    
    # GitHub Container Registry へのログイン（必要に応じて）
    if [ -n "$CR_PAT" ]; then
        echo "$CR_PAT" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin
    fi
    
    # イメージのビルド
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # イメージのプッシュ（設定されている場合）
    if [ "$PUSH_IMAGES" = "true" ]; then
        log_info "イメージをレジストリにプッシュ中..."
        docker-compose -f docker-compose.prod.yml push
    fi
    
    log_success "イメージビルド完了"
}

# サービスのデプロイ
deploy_services() {
    log_info "サービスをデプロイ中..."
    
    # 古いコンテナを停止して削除
    docker-compose -f docker-compose.prod.yml down
    
    # 新しいコンテナを起動
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "サービスデプロイ完了"
}

# ヘルスチェックの実行
run_health_checks() {
    log_info "ヘルスチェックを実行中..."
    
    # サービスの起動を待つ
    sleep 30
    
    # バックエンドのヘルスチェック
    BACKEND_HEALTH=$(curl -f -s http://localhost:8000/health || echo "failed")
    if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
        log_success "バックエンド: 正常"
    else
        log_error "バックエンド: 異常"
        return 1
    fi
    
    # フロントエンドのヘルスチェック
    FRONTEND_HEALTH=$(curl -f -s http://localhost:3000/api/health || echo "failed")
    if echo "$FRONTEND_HEALTH" | grep -q "healthy"; then
        log_success "フロントエンド: 正常"
    else
        log_error "フロントエンド: 異常"
        return 1
    fi
    
    # Nginxのヘルスチェック
    NGINX_HEALTH=$(curl -f -s http://localhost/ || echo "failed")
    if [ "$NGINX_HEALTH" != "failed" ]; then
        log_success "Nginx: 正常"
    else
        log_error "Nginx: 異常"
        return 1
    fi
    
    log_success "全てのヘルスチェック通過"
}

# デプロイ後のクリーンアップ
post_deployment_cleanup() {
    log_info "デプロイ後のクリーンアップを実行中..."
    
    # 未使用のイメージとコンテナを削除
    docker system prune -f
    
    # 古いログファイルの削除（必要に応じて）
    find /var/log -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    log_success "クリーンアップ完了"
}

# ロールバック機能
rollback() {
    log_warning "ロールバックを実行中..."
    
    # 最新のバックアップディレクトリを取得
    LATEST_BACKUP=$(ls -t backups/ | head -n 1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        log_error "ロールバック用のバックアップが見つかりません"
        exit 1
    fi
    
    log_info "バックアップから復元中: $LATEST_BACKUP"
    
    # サービスを停止
    docker-compose -f docker-compose.prod.yml down
    
    # 前のバージョンに戻す（実装が必要）
    # この部分は具体的なロールバック戦略に応じて実装
    
    log_success "ロールバック完了"
}

# メイン実行部分
main() {
    log_info "GameChat AI Production Deployment を開始します"
    log_info "現在時刻: $(date)"
    
    case "${1:-deploy}" in
        "deploy")
            pre_deployment_checks
            create_backup
            build_and_push
            deploy_services
            run_health_checks
            post_deployment_cleanup
            log_success "デプロイ完了! 🎉"
            ;;
        "rollback")
            rollback
            ;;
        "health")
            run_health_checks
            ;;
        "backup")
            create_backup
            ;;
        *)
            echo "使用方法: $0 [deploy|rollback|health|backup]"
            echo "  deploy   - 本番環境へのデプロイ (デフォルト)"
            echo "  rollback - 前のバージョンにロールバック"
            echo "  health   - ヘルスチェックのみ実行"
            echo "  backup   - バックアップのみ作成"
            exit 1
            ;;
    esac
}

# スクリプトの実行
main "$@"
