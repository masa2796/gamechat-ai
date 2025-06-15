# 環境変数設定ガイド

このプロジェクトの環境変数は整理されており、以下の構成になっています。

## ファイル構成

```
gamechat-ai/
├── .env.example                    # 開発環境用テンプレート
├── .env.production.example         # 本番環境用テンプレート
├── backend/
│   ├── .env                       # 開発環境用実際の設定（機密情報含む）
│   └── .env.production            # 本番環境用実際の設定（機密情報含む）
└── frontend/
    └── .env.production            # 本番環境用フロントエンド設定
```

## セットアップ手順

### 開発環境

1. **バックエンド設定**
   ```bash
   cp .env.example backend/.env
   ```
   
2. **backend/.envを編集**して以下の値を設定：
   - `OPENAI_API_KEY`: OpenAI APIキー
   - `UPSTASH_VECTOR_REST_URL`: Upstash Vector Database URL
   - `UPSTASH_VECTOR_REST_TOKEN`: Upstash Vector Database トークン
   - `RECAPTCHA_SECRET`: reCAPTCHA秘密鍵
   - `RECAPTCHA_SITE`: reCAPTCHAサイトキー

3. **フロントエンド設定**（必要に応じて）
   ```bash
   # フロントエンド固有の設定が必要な場合のみ
   touch frontend/.env.local
   ```

### 本番環境

1. **設定ファイル作成**
   ```bash
   cp .env.production.example backend/.env.production
   cp .env.production.example frontend/.env.production
   ```

2. **各ファイルを編集**して本番環境用の値を設定

## 設定診断

設定が正しく読み込まれているかを確認：

```bash
python scripts/diagnose_config.py
```

## 注意事項

- **機密情報を含むファイル**（`.env`, `.env.production`等）はGitにコミットされません
- **テンプレートファイル**（`.env.example`, `.env.production.example`）はコミット対象です
- 開発環境では`backend/.env`から設定が読み込まれます
- 本番環境では`backend/.env.production`から設定が読み込まれます

## 設定の優先順位

1. `backend/.env.production`（本番環境時）
2. `backend/.env`（開発環境時）
3. システム環境変数
4. デフォルト値

## トラブルシューティング

### 設定が読み込まれない場合

1. ファイルパスが正しいか確認
2. ファイルの権限を確認
3. 診断スクリプトを実行して詳細を確認

### APIキーが認識されない場合

1. `.env`ファイルに空白行や不正な文字がないか確認
2. `override=True`オプションで強制上書きを確認
3. アプリケーションを再起動
