本番環境デプロイ
================

**現在のデプロイメント環境**

.. note::
   **現在のプロジェクト環境**
   
   * プロジェクトID: ``gamechat-ai``
   * デプロイ方法: Artifact Registry使用
   * サービスURL: ``https://gamechat-ai-backend-905497046775.asia-northeast1.run.app``

Google Cloud Run を使用した本番環境へのデプロイ手順と設定について説明します。

**現在のArtifact Registry用デプロイ**

.. code-block:: bash

   # 現在のArtifact Registry用コマンド
   docker build --platform linux/amd64 -f backend/Dockerfile -t "asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend" .
   docker push asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:latest

**Cloud Run デプロイ（現在の環境）**

.. code-block:: bash

   # 現在のデプロイコマンド
   gcloud run deploy gamechat-ai-backend \
     --image asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:latest \
     --platform managed \
     --region asia-northeast1 \
     --allow-unauthenticated \
     --port 8000 \
     --memory 1Gi \
     --cpu 1 \
     --max-instances 10 \
     --timeout 300

現在のデプロイ環境：

   * **プロジェクトID**: ``gamechat-ai``
   * **サービスURL**: ``https://gamechat-ai-backend-905497046775.asia-northeast1.run.app``

   最新のデプロイガイドは以下を参照してください：

   * :doc:`../deployment/cloud-run-artifact-registry`

現在のデプロイ情報
--------------------------

基本情報
~~~~~~~~

* **プロジェクトID**: ``gamechat-ai``
* **サービス名**: ``gamechat-ai-backend`` 
* **リージョン**: ``asia-northeast1`` (東京)
* **サービスURL**: ``https://gamechat-ai-backend-905497046775.asia-northeast1.run.app``
* **稼働状況**: 稼働中

スペック構成
~~~~~~~~~~~~

* **CPU**: 1コア
* **メモリ**: 1GB
* **最小インスタンス**: 0
* **最大インスタンス**: 10
* **タイムアウト**: 300秒
* **同時実行数**: 80リクエスト/インスタンス

稼働状況
~~~~~~~~

.. code-block:: bash

   # ヘルスチェック確認（正常稼働中）
   curl https://gamechat-ai-backend-507618950161.asia-northeast1.run.app/health
   
   # レスポンス例
   {
     "status": "healthy",
     "service": "gamechat-ai-backend", 
     "timestamp": "2025-06-15T12:33:43.185442",
     "uptime_seconds": 63.93,
     "version": "1.0.0",
     "environment": "production"
   }

* **最大インスタンス**: 10
* **タイムアウト**: 300秒
* **ポート**: 8000

エンドポイント
~~~~~~~~~~~~~~

* **ヘルスチェック**: ``/health``
* **API ドキュメント**: ``/docs``
* **RAG チャット**: ``/api/v1/rag/chat``

環境変数
~~~~~~~~

.. code-block:: bash

   ENVIRONMENT=production
   LOG_LEVEL=INFO
   OPENAI_API_KEY=***（設定済み）

デプロイ手順
------------

前提条件
~~~~~~~~

必要なツールのインストール:

.. code-block:: bash

   # Google Cloud CLI
   # https://cloud.google.com/sdk/docs/install
   
   # Docker Desktop
   # https://www.docker.com/products/docker-desktop

API有効化
~~~~~~~~~

必要なGoogle Cloud APIの有効化:

.. code-block:: bash

   gcloud services enable cloudbuild.googleapis.com containerregistry.googleapis.com run.googleapis.com

Docker認証設定
~~~~~~~~~~~~~~

Google Container Registryへの認証設定:

.. code-block:: bash

   gcloud auth configure-docker

イメージビルド・プッシュ
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Cloud Run対応のイメージをビルド
   docker build --platform linux/amd64 -f backend/Dockerfile -t "asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend" .
   
   # Artifact Registry にプッシュ
   docker push asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:latest

Cloud Run デプロイ
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   gcloud run deploy gamechat-ai-backend \
     --image asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:latest \
     --platform managed \
     --region asia-northeast1 \
     --allow-unauthenticated \
     --port 8000 \
     --memory 1Gi \
     --cpu 1 \
     --min-instances 0 \
     --max-instances 10 \
     --timeout 300 \
     --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,OPENAI_API_KEY=your_api_key"

運用・保守
----------

環境変数更新
~~~~~~~~~~~~

本番用API キーの更新:

.. code-block:: bash

   gcloud run services update gamechat-ai-backend \
     --region asia-northeast1 \
     --update-env-vars OPENAI_API_KEY=your_production_api_key

ログ確認
~~~~~~~~

サービスログの確認:

.. code-block:: bash

   gcloud run services logs read gamechat-ai-backend --region=asia-northeast1 --limit=20

サービス監視
~~~~~~~~~~~~

ヘルスチェック:

.. code-block:: bash

   curl https://gamechat-ai-backend-507618950161.asia-northeast1.run.app/health

セキュリティ設定
----------------

HTTPS通信
~~~~~~~~~

* ✅ Cloud Run による自動HTTPS化
* ✅ SSL/TLS証明書の自動管理

環境変数管理
~~~~~~~~~~~~

* ✅ 機密情報の環境変数化
* ✅ Google Secret Manager 連携可能

CORS設定
~~~~~~~~

* ✅ FastAPI による適切なCORS設定
* ✅ 必要なオリジンのみ許可

パフォーマンス最適化
--------------------

自動スケーリング
~~~~~~~~~~~~~~~~

* ✅ リクエスト数に応じた自動スケーリング（0-10インスタンス）
* ✅ コールドスタート最小化

リソース最適化
~~~~~~~~~~~~~~

* ✅ マルチステージDockerビルド
* ✅ Alpine Linuxベース軽量イメージ
* ✅ 必要最小限のパッケージのみインストール

監視・ログ
~~~~~~~~~~

* ✅ Google Cloud Monitoring 連携
* ✅ 構造化ログ出力
* ✅ ヘルスチェックエンドポイント

トラブルシューティング
----------------------

よくある問題と解決方法:

イメージプッシュエラー
~~~~~~~~~~~~~~~~~~~~~~

Docker認証の再設定:

.. code-block:: bash

   gcloud auth configure-docker

コンテナ起動エラー
~~~~~~~~~~~~~~~~~~

環境変数の確認とログ確認:

.. code-block:: bash

   gcloud run services describe gamechat-ai-backend --region=asia-northeast1
   gcloud run services logs read gamechat-ai-backend --region=asia-northeast1
