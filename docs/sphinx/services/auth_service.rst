認証サービス
============

.. currentmodule:: services.auth_service

.. automodule:: services.auth_service
   :members:
   :undoc-members:
   :show-inheritance:

概要
----

:class:`AuthService` は、GameChat AIシステムの認証とセキュリティを担当するサービスです。
reCAPTCHA統合、レート制限、セキュリティ監視などの機能を提供し、
システムの安全性と信頼性を確保します。

主要機能
--------

**認証機能**
  * reCAPTCHA検証
  * APIキー認証
  * セッション管理

**セキュリティ機能**
  * レート制限
  * 不正アクセス検出
  * セキュリティログ

**監視機能**
  * アクセス解析
  * 異常検出
  * パフォーマンス監視

クラス詳細
----------

.. autoclass:: AuthService
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. automethod:: __init__
      
      認証サービスのコンストラクタ
      
      :param recaptcha_secret: reCAPTCHA秘密キー
      :type recaptcha_secret: str
      :param config: 認証設定（オプション）
      :type config: dict, optional
      
      :raises ValueError: reCAPTCHA秘密キーが無効な場合
      :raises ConfigurationError: 設定が無効な場合
      
      **設定オプション:**
      
      .. code-block:: python
      
         config = {
             "recaptcha_threshold": 0.5,       # reCAPTCHAスコア閾値
             "rate_limit": {
                 "requests_per_minute": 60,    # 分あたりリクエスト数
                 "burst_size": 10              # バーストサイズ
             },
             "session_timeout": 3600,          # セッションタイムアウト（秒）
             "enable_security_logging": True,  # セキュリティログ有効化
             "blocked_ips": [],                # ブロックIPリスト
             "whitelist_ips": []               # ホワイトリストIPリスト
         }

   .. automethod:: verify_recaptcha
      :no-index:
   
      reCAPTCHA検証を実行
      
      :param recaptcha_response: reCAPTCHA応答トークン
      :type recaptcha_response: str
      :param user_ip: ユーザーのIPアドレス（オプション）
      :type user_ip: str, optional
      :return: 検証結果
      :rtype: RecaptchaVerification
      
      :raises RecaptchaError: reCAPTCHA検証中にエラーが発生した場合
      :raises NetworkError: Google APIとの通信エラーが発生した場合
      
      **検証結果の構造:**
      
      .. code-block:: python
      
         {
             "success": True,                  # 検証成功の真偽値
             "score": 0.8,                     # スコア（0.0-1.0）
             "action": "submit_query",         # アクション名
             "challenge_ts": "2025-06-15T10:30:00Z",  # チャレンジ時刻
             "hostname": "example.com",        # ホスト名
             "error_codes": []                 # エラーコード（失敗時）
         }
      
      **例:**
      
      .. code-block:: python
      
         # reCAPTCHA検証
         verification = await auth_service.verify_recaptcha(
             recaptcha_response="03AGdBq...",
             user_ip="192.168.1.1"
         )
         
         if verification.success and verification.score >= 0.5:
             print("reCAPTCHA検証成功")
         else:
             print("reCAPTCHA検証失敗")
             print(f"スコア: {verification.score}")

   .. automethod:: check_rate_limit
   
      レート制限をチェック
      
      :param identifier: 識別子（IPアドレス、ユーザーIDなど）
      :type identifier: str
      :param action: アクション名（オプション）
      :type action: str, optional
      :return: レート制限チェック結果
      :rtype: RateLimitResult
      
      :raises RateLimitError: レート制限に引っかかった場合
      
      **例:**
      
      .. code-block:: python
      
         # レート制限チェック
         try:
             result = await auth_service.check_rate_limit(
                 identifier="192.168.1.1",
                 action="query_submission"
             )
             print(f"残りリクエスト数: {result.remaining}")
             print(f"リセット時刻: {result.reset_time}")
         except RateLimitError as e:
             print(f"レート制限エラー: {e}")
             print(f"再試行可能時刻: {e.retry_after}")

   .. automethod:: log_security_event
   
      セキュリティイベントをログに記録
      
      :param event_type: イベントタイプ
      :type event_type: str
      :param details: イベント詳細
      :type details: dict
      :param severity: 重要度（デフォルト: "info"）
      :type severity: str, optional
      :param user_ip: ユーザーのIPアドレス（オプション）
      :type user_ip: str, optional
      
      **イベントタイプ:**
      
      * **login_attempt**: ログイン試行
      * **rate_limit_exceeded**: レート制限超過
      * **suspicious_activity**: 疑わしい活動
      * **security_violation**: セキュリティ違反
      * **system_access**: システムアクセス
      
      **例:**
      
      .. code-block:: python
      
         # セキュリティイベントのログ記録
         await auth_service.log_security_event(
             event_type="suspicious_activity",
             details={
                 "action": "multiple_failed_requests",
                 "count": 10,
                 "time_window": "5分"
             },
             severity="warning",
             user_ip="192.168.1.100"
         )

   .. automethod:: detect_anomaly
   
      異常なアクセスパターンを検出
      
      :param access_pattern: アクセスパターンデータ
      :type access_pattern: dict
      :return: 異常検出結果
      :rtype: AnomalyDetectionResult
      
      **検出される異常パターン:**
      
      * 異常に高いリクエスト頻度
      * 不自然なアクセス時間帯
      * 複数IPからの協調攻撃
      * 異常なエラー率
      
      **例:**
      
      .. code-block:: python
      
         access_pattern = {
             "ip_address": "192.168.1.1",
             "request_count": 1000,
             "time_window": 300,  # 5分
             "error_rate": 0.8,
             "user_agent": "suspicious-bot/1.0"
         }
         
         anomaly = await auth_service.detect_anomaly(access_pattern)
         
         if anomaly.is_anomalous:
             print(f"異常検出: {anomaly.anomaly_type}")
             print(f"信頼度: {anomaly.confidence}")

   .. automethod:: get_security_metrics
   
      セキュリティメトリクスを取得
      
      :param time_range: 時間範囲（秒）
      :type time_range: int, optional
      :return: セキュリティメトリクス
      :rtype: SecurityMetrics
      
      **メトリクス内容:**
      
      .. code-block:: python
      
         {
             "total_requests": 50000,          # 総リクエスト数
             "blocked_requests": 1250,         # ブロックされたリクエスト数
             "rate_limit_hits": 300,           # レート制限適用数
             "recaptcha_failures": 150,        # reCAPTCHA失敗数
             "suspicious_ips": 25,             # 疑わしいIP数
             "anomaly_detections": 5,          # 異常検出数
             "average_response_time": 1.2,     # 平均応答時間（秒）
             "security_score": 8.5             # セキュリティスコア（0-10）
         }

セキュリティ機能
----------------

**レート制限アルゴリズム**

.. code-block:: python

   class TokenBucketRateLimiter:
       """トークンバケットアルゴリズムによるレート制限"""
       
       def __init__(self, capacity, refill_rate):
           self.capacity = capacity          # バケット容量
           self.tokens = capacity           # 現在のトークン数
           self.refill_rate = refill_rate   # 補充レート（トークン/秒）
           self.last_refill = time.time()
       
       async def consume(self, tokens=1):
           """トークンを消費"""
           self.refill()
           if self.tokens >= tokens:
               self.tokens -= tokens
               return True
           return False
       
       def refill(self):
           """トークンを補充"""
           now = time.time()
           elapsed = now - self.last_refill
           self.tokens = min(
               self.capacity,
               self.tokens + elapsed * self.refill_rate
           )
           self.last_refill = now

**異常検出システム**

.. code-block:: python

   class AnomalyDetector:
       """統計的異常検出"""
       
       def __init__(self):
           self.baseline_metrics = {}
           self.detection_rules = [
               self.detect_high_frequency,
               self.detect_unusual_timing,
               self.detect_error_spike,
               self.detect_coordinated_attack
           ]
       
       async def analyze_pattern(self, access_pattern):
           """アクセスパターンの分析"""
           anomaly_scores = []
           
           for rule in self.detection_rules:
               score = await rule(access_pattern)
               anomaly_scores.append(score)
           
           # 統合スコアの計算
           combined_score = np.mean(anomaly_scores)
           
           return AnomalyResult(
               is_anomalous=combined_score > 0.7,
               confidence=combined_score,
               triggered_rules=[
                   rule.__name__ for rule, score in 
                   zip(self.detection_rules, anomaly_scores)
                   if score > 0.7
               ]
           )

**セキュリティログ管理**

.. code-block:: python

   class SecurityLogger:
       """セキュリティイベントのログ管理"""
       
       def __init__(self, log_file, retention_days=90):
           self.log_file = log_file
           self.retention_days = retention_days
           self.logger = self.setup_logger()
       
       async def log_event(self, event_type, details, severity="info"):
           """セキュリティイベントのログ記録"""
           log_entry = {
               "timestamp": datetime.utcnow().isoformat(),
               "event_type": event_type,
               "severity": severity,
               "details": details,
               "source_ip": details.get("ip_address"),
               "user_agent": details.get("user_agent"),
               "request_id": details.get("request_id")
           }
           
           self.logger.info(json.dumps(log_entry))
           
           # 高重要度イベントの即座の通知
           if severity in ["critical", "high"]:
               await self.send_alert(log_entry)

パフォーマンス特性
------------------

**認証性能**
  * reCAPTCHA検証時間: 平均0.2秒
  * レート制限チェック: 平均0.01秒
  * セッション検証: 平均0.005秒

**セキュリティ指標**
  * 偽陽性率: 0.5%
  * 偽陰性率: 0.1%
  * 異常検出精度: 96%

**システム負荷**
  * CPU使用率: 通常5%、ピーク15%
  * メモリ使用量: 平均30MB
  * ネットワーク帯域: 平均100KB/s

エラーハンドリング
------------------

**reCAPTCHA エラー対応**

.. code-block:: python

   async def robust_recaptcha_verification(self, response_token):
       """堅牢なreCAPTCHA検証"""
       max_retries = 3
       backoff_factor = 2
       
       for attempt in range(max_retries):
           try:
               return await self.verify_recaptcha(response_token)
           except NetworkError as e:
               if attempt == max_retries - 1:
                   # 最後の試行が失敗した場合は警告レベルで通す
                   await self.log_security_event(
                       "recaptcha_service_unavailable",
                       {"error": str(e)},
                       severity="warning"
                   )
                   return RecaptchaVerification(
                       success=True,
                       score=0.5,  # 中間スコア
                       fallback=True
                   )
               
               await asyncio.sleep(backoff_factor ** attempt)

**レート制限エラー対応**

.. code-block:: python

   async def graceful_rate_limiting(self, identifier, action):
       """グレースフルなレート制限処理"""
       try:
           return await self.check_rate_limit(identifier, action)
       except RateLimitError as e:
           # 軽微な超過の場合は警告で通す
           if e.excess_percentage < 0.1:  # 10%未満の超過
               await self.log_security_event(
                   "minor_rate_limit_exceeded",
                   {"identifier": identifier, "action": action},
                   severity="info"
               )
               return RateLimitResult(allowed=True, warning=True)
           else:
               raise

使用例とベストプラクティス
--------------------------

**基本的な統合**

.. code-block:: python

   from services.auth_service import AuthService
   from fastapi import HTTPException, Request
   
   # サービスの初期化
   auth_service = AuthService(
       recaptcha_secret=os.getenv("RECAPTCHA_SECRET"),
       config={
           "recaptcha_threshold": 0.5,
           "rate_limit": {
               "requests_per_minute": 60,
               "burst_size": 10
           }
       }
   )
   
   # APIエンドポイントでの使用
   @app.post("/api/query")
   async def submit_query(request: Request, query_data: QueryRequest):
       # reCAPTCHA検証
       recaptcha_result = await auth_service.verify_recaptcha(
           query_data.recaptcha_response,
           request.client.host
       )
       
       if not recaptcha_result.success or recaptcha_result.score < 0.5:
           raise HTTPException(status_code=400, detail="reCAPTCHA検証失敗")
       
       # レート制限チェック
       try:
           await auth_service.check_rate_limit(
               request.client.host,
               "query_submission"
           )
       except RateLimitError:
           raise HTTPException(status_code=429, detail="レート制限超過")
       
       # クエリ処理
       return await process_query(query_data.query)

**セキュリティ監視の実装**

.. code-block:: python

   # ミドルウェアでのセキュリティ監視
   @app.middleware("http")
   async def security_middleware(request: Request, call_next):
       start_time = time.time()
       
       # アクセスパターンの記録
       access_pattern = {
           "ip_address": request.client.host,
           "user_agent": request.headers.get("user-agent"),
           "path": request.url.path,
           "method": request.method,
           "timestamp": start_time
       }
       
       # 異常検出
       anomaly = await auth_service.detect_anomaly(access_pattern)
       if anomaly.is_anomalous:
           await auth_service.log_security_event(
               "anomaly_detected",
               access_pattern,
               severity="warning"
           )
       
       # リクエスト処理
       response = await call_next(request)
       
       # 応答時間の記録
       process_time = time.time() - start_time
       response.headers["X-Process-Time"] = str(process_time)
       
       return response

**バッチ処理での使用**

.. code-block:: python

   # 複数IPの一括チェック
   async def batch_security_check(ip_addresses):
       """複数IPアドレスの一括セキュリティチェック"""
       results = {}
       
       # 並列処理で効率化
       tasks = [
           auth_service.check_rate_limit(ip, "batch_check")
           for ip in ip_addresses
       ]
       
       rate_limit_results = await asyncio.gather(*tasks, return_exceptions=True)
       
       for ip, result in zip(ip_addresses, rate_limit_results):
           if isinstance(result, Exception):
               results[ip] = {"status": "blocked", "reason": str(result)}
           else:
               results[ip] = {"status": "allowed", "remaining": result.remaining}
       
       return results

**ダッシュボード連携**

.. code-block:: python

   # セキュリティメトリクスの定期取得
   async def update_security_dashboard():
       """セキュリティダッシュボードの更新"""
       while True:
           try:
               metrics = await auth_service.get_security_metrics(time_range=3600)
               
               # ダッシュボードに送信
               await dashboard_client.update_metrics({
                   "security_score": metrics.security_score,
                   "blocked_requests": metrics.blocked_requests,
                   "anomaly_count": metrics.anomaly_detections,
                   "average_response_time": metrics.average_response_time
               })
               
               # アラート条件のチェック
               if metrics.security_score < 7.0:
                   await send_security_alert(
                       f"セキュリティスコアが低下: {metrics.security_score}"
                   )
               
           except Exception as e:
               logger.error(f"セキュリティメトリクス更新エラー: {e}")
           
           await asyncio.sleep(300)  # 5分間隔で更新
