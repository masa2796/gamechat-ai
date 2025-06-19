Google Cloud Run デプロイガイド
===============================

Google Cloud Run を使用したGameChat AI バックエンドのデプロイ手順について説明します。

概要
----

Google Cloud Run は、コンテナ化されたアプリケーションを実行するフルマネージドサーバレスプラットフォームです。
GameChat AI バックエンドは、FastAPI + Python で構築されており、Cloud Run での実行に最適化されています。

.. note::
   **現在のデプロイ環境**

   * **プロジェクトID**: ``gamechat-ai``
   * **サービスURL**: ``https://gamechat-ai-backend-905497046775.asia-northeast1.run.app``

   最新のデプロイガイドは :doc:`../deployment/cloud-run-artifact-registry` を参照してください。

現在のデプロイ環境
-------------------------

.. list-table:: 
   :header-rows: 1

   * - 項目
     - 値
   * - プロジェクトID
     - ``gamechat-ai``
   * - サービス名
     - ``gamechat-ai-backend``
   * - リージョン
     - ``asia-northeast1`` (東京)
   * - サービスURL
     - ``https://gamechat-ai-backend-905497046775.asia-northeast1.run.app``
   * - 稼働状況
     - 稼働中

システム構成
------------

リソース仕様
~~~~~~~~~~~~

.. code-block:: yaml

   cpu: 1コア
   memory: 1GB
   min_instances: 0
   max_instances: 10
   timeout: 300秒
   port: 8000
   platform: linux/amd64

環境変数
~~~~~~~~

.. code-block:: bash

   ENVIRONMENT=production
   LOG_LEVEL=INFO
   OPENAI_API_KEY=***（機密情報）

エンドポイント
~~~~~~~~~~~~~~

.. list-table:: 
   :header-rows: 1

   * - エンドポイント
     - 用途
     - レスポンス
   * - ``/health``
     - ヘルスチェック
     - JSON（サービス状態）
   * - ``/docs``
     - API ドキュメント
     - Swagger UI
   * - ``/api/v1/rag/chat``
     - RAG チャット
     - JSON（AI応答）

デプロイ手順
------------

Step 1: 前提条件確認
~~~~~~~~~~~~~~~~~~~~~~

必要なツールとサービス:

.. code-block:: bash

   # Google Cloud CLI（認証済み）
   gcloud auth list
   
   # Docker Desktop（動作確認）
   docker --version
   
   # プロジェクト設定確認
   gcloud config get-value project

Step 2: APIサービス有効化
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 必要なGoogle Cloud APIを有効化
   gcloud services enable \
     cloudbuild.googleapis.com \
     containerregistry.googleapis.com \
     run.googleapis.com

Step 3: Docker設定
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Google Container Registry への認証設定
   gcloud auth configure-docker

**旧環境でのイメージビルド（参考用）**

Cloud Run 対応のDockerイメージをビルド:

.. code-block:: bash

   # 現在のArtifact Registry用コマンド
   docker build \
     --platform linux/amd64 \
     -f backend/Dockerfile \
     -t "asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend" \
     .

.. note::
   ``--platform linux/amd64`` フラグは Cloud Run での互換性確保のために必要です。

**現在の推奨コマンド**

.. code-block:: bash

   # 現在のArtifact Registry用コマンド
   docker build \
     --platform linux/amd64 \
     -f backend/Dockerfile \
     -t "asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend" \
     .

Step 5: イメージプッシュ
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 現在のArtifact Registry用プッシュ
   docker push asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:latest

Step 6: Cloud Run デプロイ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 現在の推奨デプロイコマンド
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

Step 7: デプロイ確認
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # ヘルスチェック
   curl https://gamechat-ai-backend-507618950161.asia-northeast1.run.app/health
   
   # API ドキュメント確認
   curl -I https://gamechat-ai-backend-507618950161.asia-northeast1.run.app/docs

運用管理
--------

環境変数更新
~~~~~~~~~~~~

.. code-block:: bash

   # 本番用APIキーの更新
   gcloud run services update gamechat-ai-backend \
     --region asia-northeast1 \
     --update-env-vars OPENAI_API_KEY=new_production_api_key

ログ監視
~~~~~~~~

.. code-block:: bash

   # リアルタイムログ確認
   gcloud run services logs read gamechat-ai-backend \
     --region=asia-northeast1 \
     --limit=50 \
     --follow

サービス情報確認
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # サービス詳細情報
   gcloud run services describe gamechat-ai-backend \
     --region=asia-northeast1

   # リビジョン一覧
   gcloud run revisions list \
     --service=gamechat-ai-backend \
     --region=asia-northeast1

パフォーマンス最適化
====================

設定とチューニング
------------------

自動スケーリング
~~~~~~~~~~~~~~~~

Cloud Run の自動スケーリング特性:

* **コールドスタート**: 初回リクエスト時の起動時間（約2-3秒）
* **ウォームアップ**: 継続リクエストでのパフォーマンス向上
* **スケールゼロ**: 無使用時の自動停止（コスト最適化）

リソース調整
~~~~~~~~~~~~

必要に応じてリソースを調整:

.. code-block:: bash

   # メモリ増量（2GB）
   gcloud run services update gamechat-ai-backend \
     --region asia-northeast1 \
     --memory 2Gi

   # CPU増強（2コア）
   gcloud run services update gamechat-ai-backend \
     --region asia-northeast1 \
     --cpu 2

トラブルシューティング
======================

問題解決
--------

よくある問題と解決策
~~~~~~~~~~~~~~~~~~~~

**問題**: イメージプッシュ失敗

.. code-block:: bash

   # 解決策: Docker認証の再設定
   gcloud auth configure-docker asia-northeast1-docker.pkg.dev
   docker push asia-northeast1-docker.pkg.dev/gamechat-ai/gamechat-ai-backend/backend:latest

**問題**: コンテナ起動失敗

.. code-block:: bash

   # 解決策: ログ確認とデバッグ
   gcloud run services logs read gamechat-ai-backend --region=asia-northeast1

**問題**: 環境変数設定エラー

.. code-block:: bash

   # 解決策: 現在の環境変数確認
   gcloud run services describe gamechat-ai-backend \
     --region=asia-northeast1 \
     --format="export" | grep ENVIRONMENT

セキュリティ考慮事項
====================

.. warning::
   本番環境では以下のセキュリティ対策を実装してください:

   * 認証が必要なエンドポイントでの ``--no-allow-unauthenticated`` 設定
   * Google Secret Manager による機密情報管理
   * VPC ネットワーク制限（必要に応じて）
   * Cloud Armor による DDoS 保護

コスト最適化
------------

Cloud Run の課金モデル:

* **リクエスト数**: 月間200万リクエストまで無料
* **CPU時間**: 使用時間に基づく課金
* **メモリ使用量**: 割り当てメモリに基づく課金
* **ネットワーク**: 送信データ量に基づく課金

コスト削減のベストプラクティス:

1. **最小リソース設定**: 必要最小限のCPU・メモリ設定
2. **効率的なコード**: レスポンス時間の最適化
3. **適切なタイムアウト**: 不要な長時間実行の回避
4. **リージョン選択**: 最適なリージョンでのレイテンシ削減
