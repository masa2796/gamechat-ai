# Firebase Hosting 移行ガイド

## 概要

このガイドでは、GameChat AIのフロントエンドをGoogle Cloud RunからFirebase Hostingに移行する手順について説明します。

## 移行の利点

### パフォーマンス向上
- **グローバルCDN**: 世界中に配信されるCDNによる高速化
- **静的配信**: HTMLファイルの高速配信
- **キャッシュ最適化**: 効率的なブラウザキャッシュ

### コスト削減
- **無料枠**: 月間10GBまで無料
- **従量課金**: 使用量に応じた料金体系
- **Cloud Run不要**: フロントエンドのCompute費用削減

### 運用性向上
- **自動デプロイ**: CI/CDパイプライン連携
- **ロールバック**: 簡単なバージョン管理
- **プレビュー**: Pull Request毎のプレビュー環境

## 移行前準備

### 1. Firebase プロジェクト設定

```bash
# Firebase CLI インストール（未インストールの場合）
npm install -g firebase-tools

# Firebase にログイン
firebase login

# プロジェクト初期化
firebase init hosting
```

### 2. Next.js設定変更

既存の`frontend/next.config.js`は Firebase Hosting用に最適化済みです：

```javascript
const nextConfig = {
  // Firebase Hosting用設定
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // ...その他の設定
}
```

### 3. 環境変数設定

```bash
# Firebase Hosting用環境変数ファイルを作成
cp frontend/.env.firebase.example frontend/.env.firebase

# 実際の値で編集
vim frontend/.env.firebase
```

## 移行手順

### Step 1: ローカルテスト

```bash
# フロントエンドディレクトリに移動
cd frontend

# 依存関係インストール
npm ci

# Firebase Hosting用ビルド
npm run build:firebase

# 静的ファイル生成確認
ls -la out/
```

### Step 2: Firebase Hosting デプロイ

```bash
# プロジェクトルートに戻る
cd ..

# デプロイスクリプト実行
./scripts/firebase-deploy.sh
```

### Step 3: 動作確認

```bash
# デプロイ済みサイトの確認
firebase hosting:sites:list

# ブラウザで動作確認
# https://your-project.web.app
```

## 設定詳細

### firebase.json

```json
{
  "hosting": {
    "public": "frontend/out",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "gamechat-ai-backend",
          "region": "asia-northeast1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

### 環境変数設定

#### frontend/.env.firebase
```env
NODE_ENV=production
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_API_URL=https://gamechat-ai-backend-507618950161.asia-northeast1.run.app
NEXT_PUBLIC_SITE_URL=https://your-firebase-project.web.app
NEXT_TELEMETRY_DISABLED=1
```

## トラブルシューティング

### よくある問題

#### 1. 静的ファイルが生成されない
```bash
# Next.js設定確認
grep -n "output.*export" frontend/next.config.js

# ビルドログ確認
cd frontend && npm run build:firebase
```

#### 2. API リクエストが失敗する
```bash
# firebase.json の rewrite設定確認
grep -A 10 "rewrites" firebase.json

# Cloud Run サービス確認
gcloud run services list --region=asia-northeast1
```

#### 3. 環境変数が反映されない
```bash
# 環境変数ファイル確認
cat frontend/.env.firebase

# ビルド時の環境変数確認
cd frontend && NODE_ENV=production npm run build:firebase
```

## 移行後の運用

### 継続的デプロイ

```bash
# GitHub Actions等でのデプロイ
- name: Deploy to Firebase Hosting
  run: |
    cd frontend
    npm ci
    npm run build:firebase
    cd ..
    firebase deploy --only hosting
```

### モニタリング

- Firebase Console でのアクセス解析
- Cloud Monitoring との連携
- パフォーマンス指標の監視

## 移行完了チェックリスト

- [ ] Firebase プロジェクトの作成・設定
- [ ] Next.js設定の変更確認
- [ ] 環境変数ファイルの作成・設定
- [ ] ローカルビルドテスト
- [ ] Firebase Hosting デプロイ
- [ ] 動作確認（フロントエンド・API連携）
- [ ] DNS設定（カスタムドメイン使用時）
- [ ] 監視・ログ設定
- [ ] ドキュメント更新

## 参考リンク

- [Firebase Hosting ドキュメント](https://firebase.google.com/docs/hosting)
- [Next.js Static Export](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)
- [Firebase CLI リファレンス](https://firebase.google.com/docs/cli)
