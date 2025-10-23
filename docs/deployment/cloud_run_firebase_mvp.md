# 🚀 Cloud Run + Firebase Hosting (MVP) デプロイ手順

**最終更新**: 2025年10月23日  
**対象**: MVP構成（最小価値検証版）

本手順はMVP向けの最小構成です。監視・カナリア・CI/CDパイプラインは範囲外。

## 📋 全体構成

```
[User Browser] --HTTPS--> [Firebase Hosting (Static)] --(rewrite /chat, /api/* )--> [Cloud Run Backend]
                                                      └--(Vector API)--> [Upstash Vector]
                                                      └--(OpenAI API)--> [OpenAI]
```

## 🔧 前提条件

- **GCP プロジェクト**: 作成済み & Cloud Run API 有効化
- **Firebase プロジェクト**: 作成済み（`firebase init hosting` 済み）
- **ローカル環境**: Python 3.11+, Node.js 18+, Docker, gcloud CLI, firebase-tools
- **必須アカウント**: Upstash Vector アカウント（推奨）、OpenAI APIキー（任意）

### 事前準備
```bash
# gcloud認証とプロジェクト設定
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

# Firebase認証
firebase login
firebase use YOUR_FIREBASE_PROJECT_ID
```

## 🛠️ 1. 環境変数設定

### バックエンド環境変数ファイル作成
```bash
# 本番用環境変数ファイル作成
cp backend/.env.prod.example backend/.env.prod
```

### .env.prod の設定例
```bash
# === 必須設定 ===
UPSTASH_VECTOR_REST_URL=https://your-vector-endpoint.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your-upstash-token

# === 推奨設定 ===
BACKEND_OPENAI_API_KEY=sk-your-openai-api-key
BACKEND_ENVIRONMENT=production
BACKEND_LOG_LEVEL=INFO

# === オプション設定 ===
UPSTASH_VECTOR_INDEX_NAME=gamechat_mvp
UPSTASH_VECTOR_NAMESPACE=mvp_cards
VECTOR_TOP_K=5
VECTOR_TIMEOUT_SECONDS=8
LLM_TIMEOUT_SECONDS=25
CORS_ORIGINS=["*"]
```

### フロントエンド環境変数
```bash
# frontend/.env.local
NEXT_PUBLIC_MVP_MODE=true
NEXT_PUBLIC_API_URL=https://your-backend-service.run.app
```

## ☁️ 2. バックエンド: Cloud Run デプロイ

### 自動デプロイスクリプト実行
```bash
PROJECT_ID=your-gcp-project \
SERVICE=gamechat-ai-backend \
REGION=asia-northeast1 \
ENV_FILE=backend/.env.prod \
  bash scripts/deployment/deploy_cloud_run_mvp.sh
```

### 手動デプロイ手順（参考）
```bash
# 1. Dockerイメージビルド
cd backend
docker build -t gcr.io/YOUR_PROJECT_ID/gamechat-ai-backend .

# 2. Container Registryにプッシュ
docker push gcr.io/YOUR_PROJECT_ID/gamechat-ai-backend

# 3. Cloud Runにデプロイ
gcloud run deploy gamechat-ai-backend \
  --image gcr.io/YOUR_PROJECT_ID/gamechat-ai-backend \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --env-vars-file backend/.env.prod \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --port 8000
```

### 動作確認
```bash
# サービスURL取得
SERVICE_URL=$(gcloud run services describe gamechat-ai-backend \
  --region asia-northeast1 \
  --format 'value(status.url)')

# ヘルスチェック
curl -s $SERVICE_URL/health
# 期待レスポンス: {"status": "healthy"}

# /chat エンドポイント確認
curl -s -X POST "$SERVICE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"テストクエリ","with_context":true}' | jq
```

## 📁 3. ベクトルデータ投入（推奨）

Upstash Vectorにゲームカードデータを投入します。

### データ投入スクリプト実行
```bash
# Pythonパッケージインストール
pip install -r backend/requirements.txt

# データ投入実行
python scripts/data-processing/upstash_upsert_mvp.py \
  --source data/convert_data.json \
  --namespace mvp_cards
```

### 投入確認
```bash
# 投入後の検索テスト
curl -s -X POST "$SERVICE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"強いカードを教えて","with_context":true}' | jq '.retrieved_titles'
```

**注意**: データ投入しない場合、`/chat`はダミータイトルでフォールバックし、最低限の回答を返します。

## 🌐 4. フロントエンド: Firebase Hosting デプロイ

### 自動デプロイスクリプト実行
```bash
PROJECT_ID=your-firebase-project \
  bash scripts/deployment/deploy_firebase_hosting_mvp.sh
```

### 手動デプロイ手順（参考）
```bash
cd frontend

# 1. 環境変数設定してビルド
NEXT_PUBLIC_MVP_MODE=true \
NEXT_PUBLIC_API_URL=https://your-backend-service.run.app \
  npm run build

# 2. Firebase Hostingにデプロイ
firebase deploy --only hosting --project your-firebase-project
```

### デプロイ確認
```bash
# 公開URL確認
firebase hosting:sites:list --project your-firebase-project

# ブラウザでアクセステスト
# 1. トップページの表示確認
# 2. チャット機能でメッセージ送信テスト
# 3. ブラウザDevToolsでネットワークタブを確認（/chatへのリクエスト成功）
## ⚙️ 5. Firebase Hosting設定詳細

### firebase.json の重要設定
```json
{
  "hosting": {
    "public": "frontend/out",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "/chat",
        "run": {
          "serviceId": "gamechat-ai-backend",
          "region": "asia-northeast1"
        }
      },
      {
        "source": "/api/**",
        "run": {
          "serviceId": "gamechat-ai-backend",
          "region": "asia-northeast1"
        }
      }
    ],
    "headers": [
      {
        "source": "**",
        "headers": [
          {"key": "X-Content-Type-Options", "value": "nosniff"},
          {"key": "X-Frame-Options", "value": "DENY"},
          {"key": "X-XSS-Protection", "value": "1; mode=block"}
        ]
      }
    ]
  }
}
```

### CORS設定の考え方
- **バックエンド側**: FastAPI の `CORS_ORIGINS` でMVPではワイルドカード（`["*"]`）運用
- **本番運用時**: 特定ドメインに制限することを推奨
- **Firebase Hosting**: `/chat` と `/api/**` をCloud Runへプロキシ

## 🔍 6. トラブルシューティング

### よくある問題と対処法

| 症状 | 原因 | チェック項目 | 対処法 |
|------|------|--------------|--------|
| **404 /chat** | Firebase Rewrites未設定 | `firebase.json`の`rewrites`セクション | `/chat`のrun設定を追加して再デプロイ |
| **500 Embedding Error** | OpenAI API未設定 | `BACKEND_OPENAI_API_KEY`の設定状況 | APIキー設定 or フォールバック許容 |
| **検索結果が常にダミー** | Upstash未設定 | `UPSTASH_VECTOR_REST_URL/TOKEN` | Upstash設定を追加して再デプロイ |
| **CORS Block** | オリジン制限 | ブラウザNetwork エラー詳細 | Cloud Runレスポンスヘッダー確認 |
| **デプロイタイムアウト** | リソース不足 | Cloud Runメモリ/CPU設定 | インスタンス仕様を上げる |
| **Cold Start遅延** | インスタンス起動時間 | 初回リクエスト応答時間 | min-instancesの設定検討 |

### デバッグ用コマンド
```bash
# Cloud Runログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gamechat-ai-backend" \
  --limit 50 --format json

# Firebase Hosting設定確認
firebase hosting:sites:list

# 環境変数確認
gcloud run services describe gamechat-ai-backend \
  --region asia-northeast1 \
  --format='value(spec.template.spec.template.spec.containers[0].env[].name)'
```

### パフォーマンス監視
```bash
# レスポンス時間測定
time curl -X POST "$SERVICE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"テスト","with_context":true}'

# リソース使用量確認
gcloud run services describe gamechat-ai-backend \
  --region asia-northeast1 \
  --format='value(status.traffic[0].latestRevision)'
```

## 🔄 7. ロールバック手順

### Cloud Run ロールバック
```bash
# 利用可能なリビジョン確認
gcloud run revisions list --service gamechat-ai-backend --region asia-northeast1

# 特定リビジョンにトラフィック切り替え
gcloud run services update-traffic gamechat-ai-backend \
  --region asia-northeast1 \
  --to-revisions REVISION_NAME=100
```

### Firebase Hosting ロールバック
```bash
# デプロイ履歴確認
firebase hosting:releases:list

# 前バージョンへのロールバック
firebase hosting:rollback
```

## 🔒 8. セキュリティ・運用考慮事項

### 現在のセキュリティレベル（MVP）
- **認証**: なし（公開API）
- **レート制限**: なし
- **CORS**: ワイルドカード許可
- **API キー**: バックエンド環境変数のみ

### 本番運用への改善案
```bash
# 1. CORS制限強化
CORS_ORIGINS=["https://your-domain.web.app","https://your-domain.firebaseapp.com"]

# 2. レート制限実装（Cloud Run + Cloud Armor検討）
# 3. API キー認証追加
# 4. ログ監視・アラート設定
```

### 監視指標案
- **応答時間**: 平均3秒以下、最大5秒以内
- **エラー率**: 1%未満
- **リクエスト頻度**: 1分あたり60回超過で要注意
- **Vector検索成功率**: 50%以上

## 🚀 9. 次のステップ・改善候補

### 短期改善
- [ ] CI/CD（GitHub Actions）でbuild & deploy自動化
- [ ] Upstash投入スクリプト差分同期機能
- [ ] ログ構造化とアラート設定

### 中期改善
- [ ] 認証システム導入（Firebase Auth等）
- [ ] レート制限・セキュリティ強化
- [ ] パフォーマンス最適化（キャッシュ等）

### 長期改善
- [ ] マルチリージョン展開
- [ ] 高可用性・DR対応
- [ ] 詳細監視・運用自動化

---

## 📚 関連ドキュメント

- [環境変数詳細ガイド](../project/env_mvp.md)
- [プロジェクト状況](../project/release_mvp.md)
- [今後のタスク一覧](../project/future_tasks.md)

---

**重要**: MVPでは「起動しユーザーが触れる」ことを最重視。複雑化は避け、安定性と簡素さを優先してください。必要になった時点で段階的に拡張することを推奨します。
