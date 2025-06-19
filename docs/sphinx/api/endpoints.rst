エンドポイント
==============

API エンドポイントの詳細仕様について説明します。

RAG API
-------

.. automodule:: routers.rag
   :members:
   :undoc-members:
   :show-inheritance:

主要機能
~~~~~~~~

query_endpoint
~~~~~~~~~~~~~~

.. autofunction:: routers.rag.query_endpoint

ヘルスチェック
--------------

アプリケーションの状態を確認するエンドポイントです。

.. code-block:: http

   GET /api/v1/health HTTP/1.1
   Host: localhost:8000

レスポンス:

.. code-block:: json

   {
     "status": "healthy",
     "timestamp": "2025-06-15T12:00:00Z"
   }
