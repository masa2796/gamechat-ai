#!/bin/bash

# Pipeline Test Script
# ビルド・デプロイパイプラインの動作確認用スクリプト

set -e

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

# テスト実行
test_docker_builds() {
    log_info "Docker ビルドテストを実行中..."
    
    # バックエンドのビルドテスト
    log_info "バックエンドイメージをビルド中..."
    if docker build -t gamechat-ai-backend:test -f backend/Dockerfile .; then
        log_success "バックエンドビルド成功"
    else
        log_error "バックエンドビルド失敗"
        return 1
    fi
    
    # フロントエンドのビルドテスト
    log_info "フロントエンドイメージをビルド中..."
    if docker build -t gamechat-ai-frontend:test frontend/; then
        log_success "フロントエンドビルド成功"
    else
        log_error "フロントエンドビルド失敗"
        return 1
    fi
}

test_health_endpoints() {
    log_info "ヘルスチェックエンドポイントのテストを実行中..."
    
    # 開発環境を起動
    log_info "開発環境を起動中..."
    docker-compose up -d
    
    # サービスの起動を待つ
    log_info "サービスの起動を待機中..."
    sleep 30
    
    # バックエンドのヘルスチェック
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log_success "バックエンドヘルスチェック成功"
        curl -s http://localhost:8000/health | jq '.' || echo "JSON parse error"
    else
        log_error "バックエンドヘルスチェック失敗"
    fi
    
    # 詳細ヘルスチェック
    if curl -f -s http://localhost:8000/health/detailed > /dev/null; then
        log_success "詳細ヘルスチェック成功"
        curl -s http://localhost:8000/health/detailed | jq '.' || echo "JSON parse error"
    else
        log_error "詳細ヘルスチェック失敗"
    fi
    
    # フロントエンドのヘルスチェック
    if curl -f -s http://localhost:3000/api/health > /dev/null; then
        log_success "フロントエンドヘルスチェック成功"
        curl -s http://localhost:3000/api/health | jq '.' || echo "JSON parse error"
    else
        log_error "フロントエンドヘルスチェック失敗"
    fi
    
    # 開発環境を停止
    docker-compose down
}

test_production_compose() {
    log_info "本番環境Composeファイルのテストを実行中..."
    
    # ネットワークを作成
    docker network create gamechat-network || true
    
    # 本番環境を起動（バックグラウンド）
    log_info "本番環境を起動中..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # サービスの起動を待つ
    log_info "サービスの起動を待機中..."
    sleep 45
    
    # ヘルスチェック
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log_success "本番環境バックエンド正常"
    else
        log_error "本番環境バックエンド異常"
    fi
    
    if curl -f -s http://localhost:3000/api/health > /dev/null; then
        log_success "本番環境フロントエンド正常"
    else
        log_error "本番環境フロントエンド異常"
    fi
    
    # Nginxプロキシ経由のテスト
    if curl -f -s http://localhost/ > /dev/null; then
        log_success "Nginxプロキシ正常"
    else
        log_error "Nginxプロキシ異常"
    fi
    
    # 本番環境を停止
    docker-compose -f docker-compose.prod.yml down
}

test_monitoring_stack() {
    log_info "監視スタックのテストを実行中..."
    
    # ネットワークを作成
    docker network create gamechat-network || true
    
    # 監視スタックを起動
    log_info "監視サービスを起動中..."
    docker-compose -f docker-compose.monitoring.yml up -d prometheus grafana node-exporter
    
    # サービスの起動を待つ
    log_info "監視サービスの起動を待機中..."
    sleep 30
    
    # Prometheusのテスト
    if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
        log_success "Prometheus正常"
    else
        log_error "Prometheus異常"
    fi
    
    # Grafanaのテスト
    if curl -f -s http://localhost:3001/api/health > /dev/null; then
        log_success "Grafana正常"
    else
        log_error "Grafana異常"
    fi
    
    # Node Exporterのテスト
    if curl -f -s http://localhost:9100/metrics > /dev/null; then
        log_success "Node Exporter正常"
    else
        log_error "Node Exporter異常"
    fi
    
    # 監視スタックを停止
    docker-compose -f docker-compose.monitoring.yml down
}

run_unit_tests() {
    log_info "ユニットテストを実行中..."
    
    # Pythonテスト
    if [ -f "backend/requirements.txt" ]; then
        log_info "Pythonテストを実行中..."
        python -m venv test_venv
        source test_venv/bin/activate
        pip install -r backend/requirements.txt
        cd backend && python -m pytest app/tests/ -v || log_warning "Pythonテスト失敗"
        deactivate
        rm -rf test_venv
        cd ..
    fi
    
    # Node.jsテスト
    if [ -f "frontend/package.json" ]; then
        log_info "Node.jsテストを実行中..."
        cd frontend
        npm install
        npm run lint || log_warning "Lintエラー"
        npm test || log_warning "Node.jsテスト失敗"
        cd ..
    fi
}

cleanup() {
    log_info "クリーンアップを実行中..."
    
    # コンテナとイメージの削除
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    docker-compose -f docker-compose.monitoring.yml down 2>/dev/null || true
    
    # テスト用イメージの削除
    docker rmi gamechat-ai-backend:test 2>/dev/null || true
    docker rmi gamechat-ai-frontend:test 2>/dev/null || true
    
    # ネットワークの削除
    docker network rm gamechat-network 2>/dev/null || true
    
    log_success "クリーンアップ完了"
}

# メイン実行部分
main() {
    log_info "=== GameChat AI Pipeline Test Starting ==="
    log_info "現在時刻: $(date)"
    
    case "${1:-all}" in
        "build")
            test_docker_builds
            ;;
        "health")
            test_health_endpoints
            ;;
        "production")
            test_production_compose
            ;;
        "monitoring")
            test_monitoring_stack
            ;;
        "unit")
            run_unit_tests
            ;;
        "cleanup")
            cleanup
            ;;
        "all")
            test_docker_builds
            test_health_endpoints
            test_production_compose
            test_monitoring_stack
            run_unit_tests
            cleanup
            log_success "=== 全テスト完了 ==="
            ;;
        *)
            echo "使用方法: $0 [build|health|production|monitoring|unit|cleanup|all]"
            echo "  build      - Dockerビルドテスト"
            echo "  health     - ヘルスチェックテスト"
            echo "  production - 本番環境テスト"
            echo "  monitoring - 監視スタックテスト"
            echo "  unit       - ユニットテスト"
            echo "  cleanup    - クリーンアップ"
            echo "  all        - 全テスト実行 (デフォルト)"
            exit 1
            ;;
    esac
}

# トラップでクリーンアップを確実に実行
trap cleanup EXIT

# スクリプトの実行
main "$@"
