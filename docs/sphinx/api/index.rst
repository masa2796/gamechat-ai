API仕様
=======

GameChat AI APIの仕様について説明します。

.. toctree::
   :maxdepth: 2
   
   endpoints
   authentication
   error_handling

概要
----

GameChat AIは、RESTful APIを提供してフロントエンドとの通信を行います。
FastAPIを使用して実装されており、自動的にOpenAPI仕様が生成されます。

API エンドポイント
==================

主要なエンドポイント:

* ``POST /api/v1/rag/query`` - RAG検索・応答生成
* ``GET /api/v1/health`` - ヘルスチェック
* ``GET /docs`` - API ドキュメント（Swagger UI）
