# Sentry Alert Configuration
# 本番環境でのアラート設定ガイド

## 必須アラート設定

### 1. 高優先度アラート（即座に対応が必要）

#### エラー率アラート
- **条件**: エラー率が5%を超えた場合（5分間）
- **通知先**: Slack #alerts, メール, PagerDuty
- **設定値**:
  ```
  Event type: error
  Condition: count() > 50 in 5 minutes
  Environment: production
  ```

#### 重要なAPIエンドポイントの可用性
- **条件**: /api/rag/query エンドポイントのエラー率が1%を超えた場合
- **通知先**: Slack #alerts, メール
- **設定値**:
  ```
  Event type: transaction
  Condition: failure_rate() > 0.01 in 5 minutes
  Tag: transaction=/api/rag/query
  Environment: production
  ```

#### 応答時間アラート
- **条件**: P95応答時間が10秒を超えた場合
- **通知先**: Slack #performance
- **設定値**:
  ```
  Event type: transaction
  Condition: p95() > 10000ms in 10 minutes
  Environment: production
  ```

### 2. 中優先度アラート（24時間以内の対応）

#### エラーの急増
- **条件**: 前時間比でエラーが300%増加
- **通知先**: Slack #monitoring
- **設定値**:
  ```
  Event type: error
  Condition: percent_change() > 300% compared to previous period
  Period: 1 hour
  Environment: production
  ```

#### メモリ使用量警告
- **条件**: メモリ関連エラーの発生
- **通知先**: Slack #infrastructure
- **設定値**:
  ```
  Event type: error
  Condition: count() > 10 in 1 hour
  Tag: error.type=MemoryError
  Environment: production
  ```

### 3. 低優先度アラート（監視目的）

#### 新しいエラータイプの検出
- **条件**: 新しいタイプのエラーが発生
- **通知先**: Slack #development
- **設定値**:
  ```
  Event type: error
  Condition: is new issue
  Environment: production
  ```

## アラート設定の実装手順

### 1. Sentry Web UIでの設定

```bash
# Sentry Web UIにアクセス
# https://sentry.io/organizations/[your-org]/projects/

# Projects > gamechat-ai > Alerts に移動
# Create Alert Rule をクリック
```

### 2. Slack統合の設定

```yaml
# Slack Webhook URL を Sentry に設定
# Organization Settings > Integrations > Slack
webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
channels:
  - name: "#alerts"
    level: "error"
  - name: "#performance" 
    level: "warning"
  - name: "#monitoring"
    level: "info"
```

### 3. メール通知の設定

```yaml
# User Settings > Notifications
email_notifications:
  workflow: "always"
  deploy: "committed_only"
  issue_alerts: "always"
  performance_alerts: "always"
```

### 4. PagerDuty統合（重要アラートのみ）

```yaml
# Organization Settings > Integrations > PagerDuty
integration_key: "YOUR_PAGERDUTY_INTEGRATION_KEY"
escalation_policy: "Primary Escalation"
```

## 推奨設定値

### サンプリング率（本番環境）
```yaml
# フロントエンド
traces_sample_rate: 0.1
replay_session_sample_rate: 0.01
replay_on_error_sample_rate: 0.1
error_sample_rate: 0.9

# バックエンド
traces_sample_rate: 0.05
error_sample_rate: 0.8
profile_sample_rate: 0.01

# Edge環境
traces_sample_rate: 0.02
error_sample_rate: 0.5
```

### データ保持設定
```yaml
# 90日間のデータ保持（コスト最適化）
retention_days: 90

# 重要なエラーのみ長期保存
high_priority_retention_days: 180
```

### クォータ制限
```yaml
# 月間イベント数制限（コスト管理）
monthly_event_limit: 1000000
daily_event_limit: 50000

# レート制限
burst_limit: 1000
sustained_limit: 100
```

## 運用チェックリスト

### 日次確認事項
- [ ] エラー率の確認（目標: <1%）
- [ ] 応答時間の確認（目標: P95 < 5秒）
- [ ] 新しいエラーの確認と分類
- [ ] アラート疲れの確認と調整

### 週次確認事項
- [ ] サンプリング率の効果測定
- [ ] コスト分析とクォータ確認
- [ ] アラートルールの精度確認
- [ ] 誤検知アラートの調整

### 月次確認事項
- [ ] パフォーマンストレンドの分析
- [ ] エラー傾向の分析
- [ ] アラート設定の見直し
- [ ] コスト最適化の検討

## トラブルシューティング

### よくある問題と対処法

#### アラート疲れ
```yaml
# 解決策: より厳しい閾値設定
old_threshold: 10 errors in 5 minutes
new_threshold: 50 errors in 5 minutes

# または条件の細分化
specific_conditions:
  - error.type: "DatabaseError"
  - error.level: "fatal"
```

#### コスト超過
```yaml
# 解決策: サンプリング率の調整
traces_sample_rate: 0.05 → 0.02
replay_session_sample_rate: 0.01 → 0.005

# フィルタリングの強化
before_send: "より厳しいフィルタリング"
```

#### 重要なエラーの見逃し
```yaml
# 解決策: 重要エラーの除外設定
critical_errors:
  - "DatabaseConnectionError"
  - "AuthenticationError" 
  - "PaymentError"
sampling_override: 1.0 # 常に送信
```
