# Docker Compose 使い分けガイド

GameChat AIでは目的別に複数のDocker Composeファイルを使い分けています。

## 📁 ファイル構成

### 基本ファイル
- **`docker-compose.yml`** - 開発環境の基本設定
- **`docker-compose.prod.yml`** - 本番環境用拡張設定
- **`docker-compose.monitoring.yml`** - 監視システム（オプショナル）

## 🚀 使用方法

### 1. 開発環境（基本）
```bash
# バックエンドのみ起動
docker-compose up --build -d backend

# 全サービス起動
docker-compose up --build -d
```

**含まれるサービス**:
- Backend API (FastAPI)
- 基本的なヘルスチェック
- ログローテーション

### 2. 本番環境（Redis + 最適化）
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

**追加サービス**:
- Redis (キャッシュ・セッション管理)
- PostgreSQL (永続化データベース)
- Nginx (リバースプロキシ)
- リソース制限・最適化設定

### 3. 監視システム付き（開発・デバッグ用）
```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up --build -d
```

**追加サービス**:
- Fluentd (ログ集約)
- Elasticsearch (ログ検索)
- Kibana (ログ可視化)
- Prometheus (メトリクス収集)
- Grafana (監視ダッシュボード)

## 🎯 用途別推奨設定

### 開発中
```bash
# 軽量・高速起動
docker-compose up backend
```

### ローカルテスト
```bash
# 本番環境に近い構成でテスト
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### 問題調査・デバッグ
```bash
# 詳細ログ・監視付き
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up
```

### 本番デプロイ
```bash
# 本番最適化設定
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔧 サービス詳細

### Backend Service
- **開発**: ホットリロード、デバッグログ
- **本番**: 最適化、リソース制限、セキュリティ強化

### Redis Service (prod.yml)
- キャッシュ・セッション管理
- レート制限
- 一時データ保存

### 監視サービス (monitoring.yml)
- **Fluentd**: アプリケーションログ収集
- **ELK Stack**: ログ検索・可視化
- **Prometheus + Grafana**: パフォーマンス監視

## 🛠️ カスタマイズ

### 環境変数オーバーライド
```bash
# .env.localで開発固有設定
cp .env.template .env.local

# 特定サービスのみ起動
docker-compose up backend redis
```

### ポート変更
```bash
# カスタムポートで起動
BACKEND_PORT=8001 docker-compose up
```

## 🚨 注意事項

1. **リソース使用量**: 
   - 基本: ~512MB RAM
   - 本番: ~2GB RAM  
   - 監視付き: ~4GB RAM

2. **ネットワーク**:
   - 全構成で共通ネットワーク使用
   - ポート競合に注意

3. **データ永続化**:
   - 開発: 一時データ
   - 本番: Volumeマウントで永続化

## 📊 パフォーマンス比較

| 構成 | 起動時間 | メモリ使用量 | 機能 |
|------|----------|-------------|------|
| 基本 | ~30秒 | ~512MB | API開発 |
| 本番 | ~60秒 | ~2GB | 本番環境テスト |
| 監視付き | ~120秒 | ~4GB | デバッグ・調査 |

---

**最終更新**: 2025年6月24日  
**関連ドキュメント**: [デプロイガイド](docs/deployment/deployment-guide.md)
