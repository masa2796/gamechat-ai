# 本番環境デプロイガイド

## 概要
本番環境への安全なデプロイのためのガイドです。

## 環境変数設定

### 1. 本番環境用環境変数ファイルの作成

#### ルートディレクトリ
```bash
cp .env.production.example .env.production
```

#### フロントエンド
```bash
cp frontend/.env.production frontend/.env.production
```

#### バックエンド
```bash
cp backend/.env.production backend/.env.production
```

### 2. 環境変数の設定

各 `.env.production` ファイルで以下の値を本番環境用に更新してください：

#### 必須設定項目

**API Keys**
- `OPENAI_API_KEY`: 本番用OpenAI APIキー
- `UPSTASH_VECTOR_REST_URL`: 本番用Upstash Vector URL
- `UPSTASH_VECTOR_REST_TOKEN`: 本番用Upstash Vectorトークン
- `RECAPTCHA_SECRET_PRODUCTION`: 本番用reCAPTCHA秘密キー

**ドメイン設定**
- `CORS_ORIGINS`: 本番ドメイン（例：https://yourdomain.com）
- `NEXT_PUBLIC_API_URL`: 本番API URL（例：https://api.yourdomain.com）

### 3. セキュリティ設定

#### CORS設定
本番環境では特定のドメインのみを許可：
```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### セキュリティヘッダー
以下のセキュリティヘッダーが自動的に適用されます：
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Content Security Policy (CSP)

## デプロイ手順

### 1. 環境変数ファイルの準備
```bash
# 環境変数ファイルが存在することを確認
ls -la .env.production
ls -la frontend/.env.production
ls -la backend/.env.production
```

### 2. 本番環境でのビルドとデプロイ
```bash
# 本番環境用Docker Composeでデプロイ
docker-compose -f docker-compose.prod.yml up -d --build
```

### 3. デプロイ確認
```bash
# サービス状態確認
docker-compose -f docker-compose.prod.yml ps

# ヘルスチェック
curl http://localhost/health

# ログ確認
docker-compose -f docker-compose.prod.yml logs
```

## 注意事項

### セキュリティ
1. **環境変数ファイルの管理**
   - `.env.production` ファイルはGitで管理されません
   - 本番サーバーで直接作成・編集してください
   - アクセス権限を適切に設定してください（600推奨）

2. **HTTPS証明書**
   - 本番環境では必ずHTTPSを使用してください
   - SSL証明書を `nginx/ssl/` ディレクトリに配置してください

3. **ファイアウォール**
   - 必要なポートのみを開放してください
   - 80, 443ポートのみ外部からアクセス可能にしてください

### 監視とログ
1. **ログローテーション**
   - Docker Composeでログローテーションが設定済み
   - 最大10MB、3ファイルまで保持

2. **ヘルスチェック**
   - バックエンドサービスにヘルスチェックが設定済み
   - 30秒間隔でチェック実行

### トラブルシューティング
1. **環境変数が反映されない場合**
   ```bash
   # コンテナを再作成
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

2. **CORS エラーが発生する場合**
   - `CORS_ORIGINS` が正しく設定されているか確認
   - フロントエンドのドメインが含まれているか確認

3. **SSL証明書エラー**
   - nginx設定とSSL証明書のパスを確認
   - 証明書の有効期限を確認

## 環境変数一覧

### バックエンド (.env.production)
| 変数名 | 必須 | 説明 |
|--------|------|------|
| OPENAI_API_KEY | ✓ | OpenAI APIキー |
| UPSTASH_VECTOR_REST_URL | ✓ | Upstash Vector URL |
| UPSTASH_VECTOR_REST_TOKEN | ✓ | Upstash Vectorトークン |
| ENVIRONMENT | ✓ | 環境設定（production） |
| CORS_ORIGINS | ✓ | 許可するオリジン |
| DEBUG | ✓ | デバッグモード（false） |
| LOG_LEVEL | ✓ | ログレベル（WARNING） |
| RECAPTCHA_SECRET_PRODUCTION | - | reCAPTCHA秘密キー |

### フロントエンド (.env.production)
| 変数名 | 必須 | 説明 |
|--------|------|------|
| NEXT_PUBLIC_API_URL | ✓ | バックエンドAPI URL |
| NODE_ENV | ✓ | Node.js環境（production） |
| NEXT_TELEMETRY_DISABLED | - | Next.jsテレメトリ無効化 |
| NEXT_PUBLIC_ENVIRONMENT | - | フロントエンド環境設定 |
