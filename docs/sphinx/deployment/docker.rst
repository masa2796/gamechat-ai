Docker環境
==========

GameChat AIは、Docker環境での開発・デプロイをサポートしています。
Alpine Linuxベースの軽量イメージを使用し、セキュリティと効率性を重視した設計となっています。

コンテナ構成
------------

フロントエンド
~~~~~~~~~~~~~~

フロントエンドコンテナは以下の特徴を持ちます:

* **ベースイメージ**: ``node:20-alpine``
* **軽量化**: Alpine Linux採用により小さなイメージサイズ
* **セキュリティ**: 最小限のパッケージで攻撃面を削減
* **マルチステージビルド**: 本番環境用の最適化

Dockerfile構成
~~~~~~~~~~~~~~

本プロジェクトでは、用途に応じて以下のDockerfileを使い分けています:

.. list-table:: Dockerfile構成
   :header-rows: 1
   :widths: 30 30 40

   * - ファイル名
     - 用途
     - 特徴
   * - ``frontend/Dockerfile``
     - 本番環境
     - マルチステージビルド、Alpine Linux
   * - ``frontend/Dockerfile.dev``
     - 開発環境
     - ホットリロード対応、Alpine Linux

バックエンド
~~~~~~~~~~~~

バックエンドコンテナの構成:

* **ベースイメージ**: ``python:3.12-alpine``
* **フレームワーク**: FastAPI + Uvicorn
* **ヘルスチェック**: 自動監視機能

セットアップ手順
----------------

Docker Compose使用
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # リポジトリをクローン
   git clone https://github.com/yourname/gamechat-ai.git
   cd gamechat-ai

   # 環境変数ファイルを作成
   cp .env.example .env
   # .envファイルを編集して適切な値を設定

   # Docker サービスをビルド・起動
   docker-compose up --build -d

   # サービス状況確認
   docker-compose ps

フロントエンドイメージ構築状況
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   **✅ ビルド完了済み**（2025年6月15日）
   
   フロントエンド用Dockerイメージは本番環境用にビルド完了しています。

**ビルド済みイメージ情報**

* **イメージタグ**: ``gcr.io/gamechat-ai-production/gamechat-ai-frontend``
* **プラットフォーム**: linux/amd64
* **ベースイメージ**: Node.js 20 Alpine
* **ビルド方式**: マルチステージビルド
* **サイズ最適化**: 軽量Alpine Linuxベース

**本番イメージビルドコマンド**

.. code-block:: bash

   # 本番環境用フロントエンドイメージビルド
   docker build --platform linux/amd64 \
     -t "gcr.io/gamechat-ai-production/gamechat-ai-frontend" \
     frontend/

**ローカルテスト実行**

.. code-block:: bash

   # ビルド済みイメージでローカルテスト
   docker run -p 3000:3000 \
     -e NEXT_PUBLIC_API_URL=https://gamechat-ai-backend-507618950161.asia-northeast1.run.app \
     gcr.io/gamechat-ai-production/gamechat-ai-frontend

アクセス先
~~~~~~~~~~

起動後は以下のURLでアクセス可能です:

* **フロントエンド**: http://localhost:3000
* **バックエンド API**: http://localhost:8000
* **API ドキュメント**: http://localhost:8000/docs

開発用Docker使用
~~~~~~~~~~~~~~~~

開発環境では専用のDockerfileを使用可能です:

.. code-block:: bash

   # 開発用イメージでフロントエンドを起動
   docker build -f frontend/Dockerfile.dev -t gamechat-ai-frontend-dev frontend/
   docker run -p 3000:3000 -v $(pwd)/frontend:/app gamechat-ai-frontend-dev

運用コマンド
------------

よく使用するDocker操作コマンド:

.. code-block:: bash

   # ログ確認
   docker-compose logs -f

   # サービス停止
   docker-compose down

   # イメージ再ビルド（キャッシュクリア）
   docker-compose build --no-cache

   # 特定サービスの再起動
   docker-compose restart backend
   docker-compose restart frontend

   # コンテナ内でのシェル実行
   docker-compose exec backend bash
   docker-compose exec frontend sh

最適化のポイント
----------------

Alpine Linux採用による利点
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **軽量化**: 従来のDebian系イメージと比較して大幅なサイズ削減
2. **セキュリティ**: 最小限のパッケージで攻撃面を削減
3. **起動速度**: 軽量イメージによる高速な起動とデプロイ
4. **リソース効率**: メモリ使用量の削減

マルチステージビルド
~~~~~~~~~~~~~~~~~~~~

本番環境用Dockerfileでは以下の最適化を実施:

* **Builder Stage**: 依存関係インストールとビルド処理
* **Runtime Stage**: 実行時に必要な最小限のファイルのみ
* **セキュリティ**: 非root ユーザーでの実行
* **権限管理**: 適切なファイル権限設定

更新履歴
--------

2025年6月15日
~~~~~~~~~~~~~

* **✅ 本番環境デプロイ完了**: Cloud Run へのバックエンドデプロイ成功
* **✅ フロントエンドイメージ構築完了**: 本番環境用 Docker イメージビルド済み
* Alpine Linux ベースのイメージに移行完了
* 開発用・本番用Dockerfileを統一・最適化
* セキュリティ向上と軽量化を実現
* 不要なDockerfileを削除してメンテナンス性向上
* マルチステージビルドによる本番最適化実装

**デプロイ済み構成**

* **バックエンド**: Google Cloud Run (``gamechat-ai-backend``)
* **フロントエンド**: Docker イメージ準備完了
* **イメージサイズ**: バックエンド 532MB、フロントエンド 309MB
* **プラットフォーム**: linux/amd64 対応
