# 🌱 MVP 環境変数一覧

最終更新: 2025-09-28

## フロントエンド (.env.local など)

| 変数 | 必須 | 説明 | 例 |
|------|------|------|----|
| NEXT_PUBLIC_MVP_MODE | Yes | `/chat` エンドポイントを利用するMVPモード | `true` |
| NEXT_PUBLIC_API_URL | Optional | バックエンドのフルURL（未設定時は相対パスで `/chat` を呼ぶ挙動を確認） | `https://<cloud-run-service>.run.app` |
| NEXT_PUBLIC_API_KEY | Optional | 将来用: APIキーをヘッダー付与する場合 | `gc_demo_xxx` |

## バックエンド (.env.prod / Cloud Run 環境変数)

| 変数 | 必須 | 説明 | 例 |
|------|------|------|----|
| BACKEND_ENV | Optional | 実行環境ラベル | `production` |
| LOG_LEVEL | Optional | ログレベル | `info` |
| BACKEND_OPENAI_API_KEY | Optional | OpenAI 埋め込み/LLM用（未設定時フォールバック擬似Embedding + スタブ回答） | `sk-...` |
| UPSTASH_VECTOR_REST_URL | Recommended | Upstash Vector REST URL | `https://example-vector.upstash.io` |
| UPSTASH_VECTOR_REST_TOKEN | Recommended | Upstash Vector Token | `xxxx` |
| UPSTASH_VECTOR_INDEX_NAME | Optional | インデックス名 (デフォルト内部定義があればそれを利用) | `gamechat_mvp` |
| UPSTASH_VECTOR_NAMESPACE | Optional | 検索時に参照する Upstash の namespace（未設定時はデフォルトnamespace） | `mvp_cards` |
| VECTOR_TOP_K | Optional | 取得する件数（リクエスト指定が優先） | `5` |
| VECTOR_TIMEOUT_SECONDS | Optional | ベクトル検索タイムアウト秒 | `8` |
| LLM_TIMEOUT_SECONDS | Optional | LLM 応答タイムアウト秒 | `25` |
| CORS_ORIGINS | Optional | CORS 許可オリジン配列(JSON) | `["*"]` |
| BACKEND_TESTING | Optional | テストモードフラグ | `false` |
| BACKEND_MOCK_EXTERNAL_SERVICES | Optional | 外部サービスモック | `false` |

## フォールバック挙動まとめ

| 条件 | 動作 |
|------|------|
| BACKEND_OPENAI_API_KEY 未設定 | 擬似Embedding生成 + スタブLLM回答 (WARN ログ) |
| Upstash 環境変数未設定 | ダミータイトル生成でベクトル部をフォールバック |
| with_context=false | `context` フィールド省略 |

## 推奨セット (最小リアル動作)
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
