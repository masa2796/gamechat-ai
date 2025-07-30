デプロイガイド
==============

GameChat AIの本番環境デプロイに関する詳細ガイドです。

デプロイ戦略
------------

**Blue-Green デプロイメント**

リスクを最小化するための段階的デプロイ戦略：

1. **Green環境構築**: 新バージョンを別環境に構築
2. **テスト実行**: Green環境での包括的テスト
3. **トラフィック切り替え**: ロードバランサーでトラフィック移行
4. **監視・ロールバック**: 問題発生時の即座の復旧

**CI/CDパイプライン**

.. code-block:: yaml

   # .github/workflows/deploy.yml
   name: Deploy to Production
   
   on:
     push:
       branches: [main]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Run tests
           run: |
             # テスト実行
             docker-compose -f docker-compose.test.yml up --abort-on-container-exit
         
         - name: Build and deploy
           run: |
             # 本番環境デプロイ
             docker-compose -f docker-compose.prod.yml up -d --build

インフラストラクチャ
--------------------

**Docker構成**

本番環境では以下のコンテナ構成を使用：

- **nginx**: リバースプロキシ・ロードバランサー
- **frontend**: Next.js フロントエンドアプリケーション
- **backend**: FastAPI バックエンドサービス

**監視・ログ**

- **Prometheus + Grafana**: メトリクス監視
- **ELK Stack**: ログ集約・分析
- **Sentry**: エラー追跡・アラート

セキュリティ
------------

**HTTPS/SSL**

.. code-block:: nginx

   server {
       listen 443 ssl http2;
       ssl_certificate /etc/ssl/certs/certificate.pem;
       ssl_certificate_key /etc/ssl/private/private-key.pem;
       
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
       ssl_prefer_server_ciphers off;
   }

**ファイアウォール設定**

.. code-block:: bash

   # UFW設定例
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable

バックアップ・復旧
------------------

**データバックアップ**

.. code-block:: bash

   # データバックアップスクリプト
   #!/bin/bash
   
   BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
   mkdir -p $BACKUP_DIR
   
   # アプリケーションデータのバックアップ
   cp -r /app/data $BACKUP_DIR/
   
   # 設定ファイルのバックアップ
   cp /app/.env.production $BACKUP_DIR/

**災害復旧手順**

1. **インフラ復旧**: 新しいサーバーでの環境構築
2. **データ復元**: バックアップからのデータ復旧
3. **サービス再開**: アプリケーションの段階的再開
4. **動作確認**: 全機能の動作テスト
