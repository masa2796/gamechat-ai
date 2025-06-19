# reCAPTCHA v3 設定ガイド

## 📍 reCAPTCHA v3 設定手順

### 1. Google reCAPTCHA 管理画面でサイト登録

1. **Google reCAPTCHA 管理コンソール**にアクセス
   - URL: https://www.google.com/recaptcha/admin

2. **新しいサイトを作成**
   - **ラベル**: `GameChat AI`
   - **reCAPTCHA タイプ**: `reCAPTCHA v3` を選択
   - **ドメイン**: 
     - `gamechat-ai.web.app`
     - `localhost` (開発用)

3. **利用規約に同意**して送信

### 2. 取得したキーの設定

#### サイトキー（NEXT_PUBLIC_RECAPTCHA_SITE_KEY）
```bash
# frontend/.env.firebase に設定
NEXT_PUBLIC_RECAPTCHA_SITE_KEY=6Lc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### シークレットキー（バックエンド用）
```bash
# Google Cloud Secret Manager に保存
echo "6Lc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | gcloud secrets create RECAPTCHA_SECRET --data-file=-

# または既存シークレットを更新
echo "6Lc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | gcloud secrets versions add RECAPTCHA_SECRET --data-file=-
```

### 3. 環境変数の更新

#### フロントエンド
```bash
# frontend/.env.firebase
NEXT_PUBLIC_RECAPTCHA_SITE_KEY=6Lc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### バックエンド (Cloud Run)
```yaml
# cloud-run-env.yaml に追加
RECAPTCHA_SECRET: "6Lc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 4. デプロイ後の確認

#### フロントエンド確認
```bash
# ブラウザの開発者ツールで確認
console.log(process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY);
```

#### バックエンド確認
```bash
# Cloud Run環境変数確認
gcloud run services describe gamechat-ai-backend --region=asia-northeast1 --format="export"
```

### 5. テスト方法

#### reCAPTCHA動作テスト
1. Webアプリでチャット送信
2. ブラウザ開発者ツールのNetworkタブでreCAPTCHAトークン確認
3. バックエンドログでreCAPTCHA検証結果確認

### 6. トラブルシューティング

#### よくある問題
1. **ドメイン未登録**: reCAPTCHA管理画面でドメイン追加
2. **キー間違い**: サイトキーとシークレットキーの混同に注意
3. **CORS問題**: バックエンドのCORS設定にreCAPTCHA APIドメイン追加

#### デバッグコマンド
```bash
# reCAPTCHA APIテスト
curl -X POST "https://www.google.com/recaptcha/api/siteverify" \
  -d "secret=YOUR_SECRET_KEY" \
  -d "response=TOKEN_FROM_FRONTEND"
```

---

## ⚠️ セキュリティ考慮事項

1. **シークレットキー**: 絶対にフロントエンドやGitリポジトリに含めない
2. **ドメイン制限**: 本番ドメインのみに制限設定
3. **スコア閾値**: reCAPTCHA v3スコアの適切な閾値設定（通常0.5以上）

---

## 📝 設定チェックリスト

- [ ] Google reCAPTCHA管理画面でサイト作成
- [ ] サイトキーをフロントエンド環境変数に設定
- [ ] シークレットキーをSecret Managerに保存
- [ ] Cloud Run環境変数にシークレット追加
- [ ] フロントエンドビルド・デプロイ
- [ ] バックエンドデプロイ
- [ ] 動作テスト実行
