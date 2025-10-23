# 🌱 MVP環境変数ガイド

**最終更新**: 2025年10月23日  
**対象**: MVP構成（最小価値検証版）

このドキュメントでは、GameChat AI のMVP構成で使用する環境変数について詳しく説明します。

## 📋 環境変数一覧

### フロントエンド (.env.local など)

| 変数名 | 必須レベル | 説明 | 設定例 | デフォルト値 |
|-------|-----------|------|-------|-------------|
| `NEXT_PUBLIC_MVP_MODE` | **必須** | MVPモードでの動作を有効化 | `true` | `false` |
| `NEXT_PUBLIC_API_URL` | 任意 | バックエンドのフルURL（未設定時は相対パス`/chat`で呼び出し） | `https://your-backend.run.app` | `""` (空文字) |
| `NEXT_PUBLIC_API_KEY` | 任意 | 将来用: APIキーをヘッダー付与する場合 | `gc_demo_xxx` | なし |

### バックエンド (.env.prod / Cloud Run環境変数)

#### 🔴 必須設定
| 変数名 | 説明 | 設定例 | 備考 |
|-------|------|-------|------|
| `UPSTASH_VECTOR_REST_URL` | Upstash Vector REST API URL | `https://example-vector.upstash.io` | Vector検索に必須 |
| `UPSTASH_VECTOR_REST_TOKEN` | Upstash Vector認証トークン | `xxxx` | Vector検索に必須 |

#### 🟡 推奨設定
| 変数名 | 説明 | 設定例 | デフォルト値 |
|-------|------|-------|-------------|
| `BACKEND_OPENAI_API_KEY` | OpenAI API キー（未設定時はフォールバック動作） | `sk-...` | なし（フォールバック） |
| `BACKEND_ENVIRONMENT` | 実行環境ラベル | `production` | `development` |
| `BACKEND_LOG_LEVEL` | ログレベル | `INFO` | `DEBUG` |

#### ⚪ オプション設定
| 変数名 | 説明 | 設定例 | デフォルト値 |
|-------|------|-------|-------------|
| `UPSTASH_VECTOR_INDEX_NAME` | Upstashインデックス名 | `gamechat_mvp` | 内部定義値 |
| `UPSTASH_VECTOR_NAMESPACE` | 検索対象namespace（未設定時はデフォルト） | `mvp_cards` | `""` (デフォルト) |
| `VECTOR_TOP_K` | Vector検索で取得する件数 | `5` | `5` |
| `VECTOR_TIMEOUT_SECONDS` | Vector検索タイムアウト秒 | `8` | `10` |
| `LLM_TIMEOUT_SECONDS` | LLM応答タイムアウト秒 | `25` | `30` |
| `CORS_ORIGINS` | CORS許可オリジン（JSON配列形式） | `["*"]` | `["*"]` |
| `BACKEND_TESTING` | テストモードフラグ | `false` | `false` |
| `BACKEND_MOCK_EXTERNAL_SERVICES` | 外部サービスモック | `false` | `false` |

## 🔄 フォールバック挙動詳細

### OpenAI API未設定時の動作
| 機能 | 通常動作 | フォールバック動作 | 影響 |
|------|----------|------------------|------|
| **Embedding生成** | OpenAI API使用 | SHA256ベース擬似ベクトル生成 | 検索精度低下（動作は継続） |
| **LLM応答生成** | OpenAI GPT使用 | スタブ回答（タイトル列挙型） | 回答品質大幅低下 |
| **ログ出力** | 通常 | WARN レベルでフォールバック使用を通知 | 運用監視で検知可能 |

### Upstash Vector未設定時の動作
| 機能 | 通常動作 | フォールバック動作 | 影響 |
|------|----------|------------------|------|
| **Vector検索** | Upstash API使用 | ダミータイトル生成（固定リスト） | 検索機能完全無効化 |
| **Context取得** | 実際のカードデータ | 空のcontextフィールド | コンテキスト情報なし |
| **retrieved_titles** | 実検索結果 | ダミータイトル配列 | タイトル情報も無意味 |

### リクエストパラメータによる動作制御
| パラメータ | 値 | 動作 | 用途 |
|-----------|----|----- |------|
| `with_context` | `true` | contextフィールドを含めてレスポンス | 詳細な情報が必要な場合 |
| `with_context` | `false` | contextフィールドを省略 | 軽量なレスポンスが必要な場合 |

## 🛠️ 環境別設定パターン

### 🔧 ローカル開発環境
```bash
# backend/.env.local
BACKEND_ENVIRONMENT=development
BACKEND_LOG_LEVEL=DEBUG
BACKEND_OPENAI_API_KEY=sk-your-dev-key
UPSTASH_VECTOR_REST_URL=https://your-dev-vector.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your-dev-token
UPSTASH_VECTOR_NAMESPACE=dev_cards

# frontend/.env.local
NEXT_PUBLIC_MVP_MODE=true
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### ☁️ 本番環境（推奨構成）
```bash
# backend/.env.prod
BACKEND_ENVIRONMENT=production
BACKEND_LOG_LEVEL=INFO
BACKEND_OPENAI_API_KEY=sk-your-prod-key
UPSTASH_VECTOR_REST_URL=https://your-prod-vector.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your-prod-token
UPSTASH_VECTOR_INDEX_NAME=gamechat_mvp
UPSTASH_VECTOR_NAMESPACE=mvp_cards
VECTOR_TOP_K=5
VECTOR_TIMEOUT_SECONDS=8
LLM_TIMEOUT_SECONDS=25
CORS_ORIGINS=["https://your-domain.web.app","https://your-domain.firebaseapp.com"]

# frontend環境変数（ビルド時）
NEXT_PUBLIC_MVP_MODE=true
NEXT_PUBLIC_API_URL=https://your-backend.run.app
```

### 🧪 最小動作確認（フォールバック許容）
```bash
# backend/.env.minimal
UPSTASH_VECTOR_REST_URL=https://your-vector.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your-token
# OpenAI未設定でフォールバック動作確認

# frontend/.env.minimal
NEXT_PUBLIC_MVP_MODE=true
# API_URL未設定で相対パス動作確認
```

## 🔍 トラブルシューティング

### よくある設定ミス

| 症状 | 考えられる原因 | 確認方法 | 対処法 |
|------|-------------|----------|--------|
| **404 /chat** | NEXT_PUBLIC_MVP_MODE未設定 | フロントエンド環境変数確認 | `NEXT_PUBLIC_MVP_MODE=true`設定 |
| **CORS エラー** | CORS_ORIGINS設定誤り | ブラウザDevTools Network確認 | オリジン追加またはワイルドカード設定 |
| **Vector検索エラー** | Upstash認証情報誤り | Cloud Runログ確認 | URL/TOKEN再確認 |
| **Empty context** | データ未投入またはnamespace不一致 | 検索結果を手動確認 | データ投入またはnamespace設定確認 |
| **タイムアウト** | TIMEOUT設定が短すぎ | レスポンス時間監視 | TIMEOUT値を増加 |

### デバッグ用コマンド

#### 環境変数確認
```bash
# Cloud Run環境変数一覧
gcloud run services describe gamechat-ai-backend \
  --region asia-northeast1 \
  --format='table(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)'

# ローカル環境変数確認
env | grep -E "(BACKEND_|UPSTASH_|NEXT_PUBLIC_)"
```

#### 動作確認テスト
```bash
# フォールバック動作確認（OpenAI未設定）
curl -X POST "$SERVICE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"テスト","with_context":false}'

# Vector検索確認
curl -X POST "$SERVICE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"強いカード","with_context":true}' | jq '.retrieved_titles'
```

## 📝 設定管理・運用メモ

### Namespace運用ポリシー（MVP）
- **開発時**: スクリプトで `--namespace dev_cards` を指定してテストデータ投入
- **本番時**: 
  - 迅速投入: デフォルトnamespaceにデータ投入（namespace指定なし）
  - 恒久運用: `UPSTASH_VECTOR_NAMESPACE=mvp_cards` で専用namespace使用

### セキュリティ考慮事項
- **API キー**: 環境変数のみで管理、コードに直書きしない
- **CORS**: 本番では特定ドメインのみ許可（ワイルドカードは開発時のみ）
- **ログ**: API キーやトークンをログ出力しない

### 関連スクリプト
- **Cloud Run デプロイ**: `scripts/deployment/deploy_cloud_run_mvp.sh`
- **データ投入**: `scripts/data-processing/upstash_upsert_mvp.py`
- **Firebase デプロイ**: `scripts/deployment/deploy_firebase_hosting_mvp.sh`

---

## 📚 関連ドキュメント

- [デプロイ手順詳細](../deployment/cloud_run_firebase_mvp.md)
- [プロジェクト状況](./release_mvp.md)
- [今後のタスク一覧](./future_tasks.md)

---

**重要**: 環境変数の変更後は必ずCloud Runの再デプロイが必要です。フロントエンドの`NEXT_PUBLIC_*`変数を変更した場合は、再ビルド・再デプロイが必要です。
```
BACKEND_OPENAI_API_KEY=sk-...
UPSTASH_VECTOR_REST_URL=...
UPSTASH_VECTOR_REST_TOKEN=...
UPSTASH_VECTOR_INDEX_NAME=gamechat_mvp
# （任意）検索で特定namespaceを利用する場合のみ
# UPSTASH_VECTOR_NAMESPACE=mvp_cards
NEXT_PUBLIC_MVP_MODE=true
```

## 備考
- Cloud Run: `gcloud run deploy` 時に `--set-env-vars` で渡す
- Firebase Hosting: ビルド時に `NEXT_PUBLIC_*` が評価されるため `scripts/deployment/deploy_firebase_hosting_mvp.sh` で `NEXT_PUBLIC_MVP_MODE=true` を export 済み
- 追加が必要になった場合は本ファイルを更新し `release_mvp.md` から参照リンクを貼る予定

### Namespace 取り扱いポリシー（MVP）
- 迅速対応（MVP投入時）: スクリプトで `--namespace` を付けず、Upstash のデフォルトnamespaceに投入します。
- 恒久対応（後追い）: 検索側は `UPSTASH_VECTOR_NAMESPACE` を設定すると、その namespace を参照します。未設定ならデフォルトnamespaceを参照します。

### 関連スクリプト
- `scripts/deployment/deploy_cloud_run_mvp.sh` : Cloud Run デプロイ時に `.env.prod` を読み込んで `--set-env-vars` を自動整形
- `scripts/data-processing/upstash_upsert_mvp.py` : Upstash の URL / TOKEN を環境変数から読み込みカードデータを投入
- `scripts/deployment/deploy_firebase_hosting_mvp.sh` : `NEXT_PUBLIC_MVP_MODE=true` を設定した状態でビルド・デプロイ
