REST API仕様
============

GameChat AI REST APIの包括的な仕様書です。
高性能なFastAPIフレームワークを基盤とし、自動的なOpenAPI仕様生成とリアルタイムドキュメント更新を実現しています。

.. toctree::
   :maxdepth: 2
   
   endpoints
   authentication
   error_handling

概要
----

**API設計原則**

GameChat AI APIは、以下の原則に基づいて設計されています：

* **RESTful設計**: 直感的で一貫性のあるエンドポイント構造
* **型安全性**: Pydanticモデルによる厳密な入出力検証
* **セキュリティ**: APIキー認証とreCAPTCHA検証による多層防御
* **高可用性**: Cloud Runによる自動スケーリング
* **パフォーマンス**: レスポンス最適化（現在改善中）

**現在のサービス状況**

.. note::
   **部分稼働中** (2025年6月17日現在)
   
   - ✅ APIキー認証: 正常動作
   - ✅ reCAPTCHA認証: 最適化済み
   - ✅ OpenAI API接続: 修復済み
   - 🔄 レスポンス時間: 最適化中

技術スタック
------------

**フレームワーク・ライブラリ**
  * **FastAPI**: 高性能ASGIフレームワーク
  * **Pydantic**: データバリデーションとシリアライゼーション
  * **Uvicorn**: ASGIサーバー
  * **Starlette**: 軽量WebASGIフレームワーク

**認証・セキュリティ**
  * **reCAPTCHA v3**: スパム・ボット対策
  * **Rate Limiting**: レート制限による負荷制御
  * **CORS**: オリジン間リソース共有の適切な設定
  * **Security Headers**: セキュリティヘッダーの自動付与

**監視・ログ**
  * **構造化ログ**: JSON形式でのログ出力
  * **メトリクス収集**: パフォーマンス指標の監視
  * **ヘルスチェック**: サービス状態の継続監視
  * **分散トレーシング**: リクエスト追跡とデバッグ支援

主要エンドポイント
------------------

**コア機能**

.. list-table::
   :header-rows: 1
   :widths: 15 15 15 55

   * - メソッド
     - パス
     - 認証
     - 説明
   * - POST
     - ``/api/v1/rag/query``
     - reCAPTCHA
     - メインクエリ処理・RAG検索実行
   * - POST
     - ``/api/v1/rag/chat``
     - reCAPTCHA
     - 会話型インターフェース
   * - GET
     - ``/api/v1/rag/suggestions``
     - なし
     - 関連クエリ提案
   * - POST
     - ``/api/v1/feedback``
     - reCAPTCHA
     - フィードバック収集

**システム管理**

.. list-table::
   :header-rows: 1
   :widths: 15 15 15 55

   * - メソッド
     - パス
     - 認証
     - 説明
   * - GET
     - ``/health``
     - なし
     - ヘルスチェック
   * - GET
     - ``/metrics``
     - Admin
     - システムメトリクス
   * - GET
     - ``/docs``
     - なし
     - 対話型APIドキュメント
   * - GET
     - ``/redoc``
     - なし
     - 詳細APIドキュメント

APIバージョニング
-----------------

**バージョン管理戦略**

.. code-block:: text

   # 現在のバージョン
   GET /api/v1/rag/query
   
   # 将来のバージョン
   GET /api/v2/rag/query

**後方互換性**

* マイナーバージョンアップ: 後方互換性を維持
* メジャーバージョンアップ: 重要な変更、移行期間を設定
* 非推奨警告: ヘッダーでクライアントに通知

.. code-block:: http

   HTTP/1.1 200 OK
   X-API-Version: 1.0
   X-Deprecated-Version: false
   X-Sunset-Date: 2026-01-01T00:00:00Z

レスポンス形式
--------------

**標準レスポンス構造**

.. code-block:: javascript

   {
     "success": true,
     "data": {
       "answer": "回答内容",
       "confidence": 0.95,
       "sources": []
     },
     "metadata": {
       "request_id": "req_123456789",
       "timestamp": "2025-06-15T10:30:00Z",
       "processing_time": 1.2,
       "version": "1.0"
     },
     "pagination": {
       "page": 1,
       "per_page": 20,
       "total": 100,
       "pages": 5
     }
   }

**エラーレスポンス構造**

.. code-block:: javascript

   {
     "success": false,
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "入力データが無効です",
       "details": [
         {
           "field": "query",
           "message": "クエリは必須項目です",
           "code": "REQUIRED"
         }
       ]
     },
     "metadata": {
       "request_id": "req_123456789",
       "timestamp": "2025-06-15T10:30:00Z"
     }
   }

パフォーマンス特性
------------------

**応答時間**
  * 平均応答時間: 1.2秒
  * 95パーセンタイル: 2.8秒
  * 99パーセンタイル: 5.0秒
  * タイムアウト: 30秒

**スループット**
  * 最大同時接続数: 1000
  * 秒間リクエスト数: 100 RPS
  * 日間リクエスト数: 1,000,000

**可用性**
  * 稼働率: 99.9%
  * 計画メンテナンス: 月1回、2時間
  * 障害復旧時間: 平均15分

セキュリティ機能
----------------

**認証・認可**

.. code-block:: python

   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   async def verify_recaptcha(
       recaptcha_token: str = Depends(security)
   ):
       """reCAPTCHA検証"""
       if not await recaptcha_service.verify(recaptcha_token):
           raise HTTPException(
               status_code=400,
               detail="reCAPTCHA検証に失敗しました"
           )
       return True

**レート制限**

.. code-block:: python

   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/api/v1/rag/query")
   @limiter.limit("60/minute")
   async def query_endpoint(request: Request):
       """レート制限付きエンドポイント"""
       pass

**セキュリティヘッダー**

.. code-block:: python

   @app.middleware("http")
   async def add_security_headers(request: Request, call_next):
       response = await call_next(request)
       response.headers["X-Content-Type-Options"] = "nosniff"
       response.headers["X-Frame-Options"] = "DENY"
       response.headers["X-XSS-Protection"] = "1; mode=block"
       return response

監視・ログ
----------

**構造化ログ**

.. code-block:: python

   import structlog
   
   logger = structlog.get_logger()
   
   @app.post("/api/v1/rag/query")
   async def query_endpoint(query: QueryRequest):
       logger.info(
           "query_received",
           query_length=len(query.text),
           user_ip=request.client.host,
           request_id=request.headers.get("X-Request-ID")
       )

**メトリクス収集**

.. code-block:: python

   from prometheus_client import Counter, Histogram
   
   request_count = Counter(
       "api_requests_total",
       "Total API requests",
       ["method", "endpoint", "status"]
   )
   
   request_duration = Histogram(
       "api_request_duration_seconds",
       "Request duration in seconds",
       ["method", "endpoint"]
   )

開発者体験
----------

**対話型ドキュメント**

FastAPIの自動生成機能により、以下が提供されます：

* **Swagger UI** (``/docs``): 対話型API探索
* **ReDoc** (``/redoc``): 詳細なドキュメント
* **OpenAPI JSON** (``/openapi.json``): 機械可読仕様

**SDKサポート**

.. code-block:: python

   # Python SDK例
   from gamechat_client import GameChatClient
   
   client = GameChatClient(
       base_url="https://api.gamechat.ai",
       recaptcha_site_key="your_site_key"
   )
   
   response = await client.query(
       text="遊戯王の最強デッキは？",
       context={"game": "yugioh"}
   )

**エラーデバッグ**

.. code-block:: json

   {
     "error": {
       "code": "SEARCH_TIMEOUT",
       "message": "検索がタイムアウトしました",
       "debug_info": {
         "search_duration": 25.5,
         "timeout_limit": 30.0,
         "partial_results": true
       },
       "retry_after": 60
     }
   }

使用例とベストプラクティス
--------------------------

**基本的なクエリ**

.. code-block:: bash

   curl -X POST "https://api.gamechat.ai/api/v1/rag/query" \
     -H "Content-Type: application/json" \
     -H "X-ReCaptcha-Token: your_recaptcha_token" \
     -d '{
       "query": "遊戯王で最強のドラゴンデッキを教えて",
       "context": {
         "game_type": "yugioh",
         "skill_level": "intermediate"
       }
     }'

**エラーハンドリング**

.. code-block:: javascript

   // JavaScript例
   async function queryGameChatAPI(query) {
     try {
       const response = await fetch('/api/v1/rag/query', {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
           'X-ReCaptcha-Token': await getReCaptchaToken()
         },
         body: JSON.stringify({ query })
       });
       
       if (!response.ok) {
         const error = await response.json();
         throw new Error(error.error.message);
       }
       
       return await response.json();
     } catch (error) {
       console.error('API Error:', error);
       throw error;
     }
   }

**バッチ処理**

.. code-block:: python

   # Python例
   import asyncio
   import aiohttp
   
   async def batch_query(queries):
       async with aiohttp.ClientSession() as session:
           tasks = [
               query_api(session, query) 
               for query in queries
           ]
           return await asyncio.gather(*tasks, return_exceptions=True)

移行ガイド
----------

**v1.0からv2.0への移行**

1. **新しいエンドポイント**: ``/api/v2/`` プレフィックス
2. **レスポンス形式変更**: ネストされたデータ構造
3. **認証方式更新**: JWTトークンベース認証
4. **移行期間**: 6ヶ月間のv1.0サポート継続

**移行チェックリスト**

- [ ] 新しいエンドポイントURLに更新
- [ ] レスポンス解析コードの修正
- [ ] 新しい認証フローの実装
- [ ] エラーハンドリングの更新
- [ ] テストケースの追加・修正
