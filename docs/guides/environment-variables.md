# 環境変数設定ガイド

## 概要

GameChat AIでは、開発環境と本番環境で異なる環境変数ファイルを使用します。
シンプルで分かりやすい構成に整理しました。

## 📁 ファイル構成

```
gamechat-ai/
├── .env.example                      # 全体のテンプレート・ガイド
├── backend/
│   ├── .env                         # 開発環境設定（実際のファイル）
│   ├── .env.production              # 本番環境設定（実際のファイル）
│   └── .env.production.template     # 本番環境テンプレート
└── frontend/
    ├── .env.local                   # 開発環境設定（実際のファイル）
    ├── .env.production              # 本番環境設定（実際のファイル）
    ├── .env.firebase               # Firebase Hosting用（実際のファイル）
    ├── .env.local.template         # 開発環境テンプレート
    ├── .env.production.template    # 本番環境テンプレート
    └── .env.firebase.example       # Firebase Hosting用テンプレート
```

## 🚀 セットアップ手順

### 1. 開発環境

```bash
# バックエンド設定
cp .env.example backend/.env
# backend/.env を編集して実際のAPIキーを設定

# フロントエンド設定
cp frontend/.env.local.template frontend/.env.local
# 通常はデフォルト設定で動作
```

### 2. 本番環境（通常デプロイ）

```bash
# バックエンド設定
cp backend/.env.production.template backend/.env.production
# backend/.env.production を編集

# フロントエンド設定
cp frontend/.env.production.template frontend/.env.production
# frontend/.env.production を編集
```

### 3. Firebase Hosting環境

```bash
# Firebase Hosting専用設定
cp frontend/.env.firebase.example frontend/.env.firebase
# frontend/.env.firebase を編集
```

## 🔧 主な設定項目

### バックエンド必須設定

```env
# OpenAI API（必須）
OPENAI_API_KEY=sk-xxxxxxxxxx

# Upstash Vector（必須）
UPSTASH_VECTOR_REST_URL=https://xxxxxxxxxx
UPSTASH_VECTOR_REST_TOKEN=xxxxxxxxxx

# セキュリティ
SECRET_KEY=your-secure-key
CORS_ORIGINS=http://localhost:3000  # 開発時
```

### フロントエンド設定

```env
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000  # 開発時
NEXT_PUBLIC_API_URL=https://your-api.com   # 本番時

# 基本設定
NODE_ENV=development  # または production
NEXT_TELEMETRY_DISABLED=1
```

## 🔍 設定確認

設定が正しく読み込まれているかを確認：

```bash
# 設定診断スクリプト実行
python scripts/diagnose_config.py
```

## ⚠️ セキュリティ注意事項

- **実際のファイル**（`.env`、`.env.production`、`.env.firebase`）はGitで管理されません
- **テンプレートファイル**（`.template`、`.example`）のみコミット対象です
- 本番環境では環境変数やシークレット管理サービスの使用を推奨
- APIキーは絶対にコミットしないでください

## 📋 チェックリスト

### 開発環境
- [ ] `backend/.env` の作成・設定
- [ ] `frontend/.env.local` の作成（オプション）
- [ ] OpenAI APIキーの設定
- [ ] Upstash Vector設定

### 本番環境
- [ ] `backend/.env.production` の作成・設定
- [ ] `frontend/.env.production` の作成・設定
- [ ] 本番用APIキーの設定
- [ ] CORS設定の更新
- [ ] セキュリティ設定の確認

### Firebase Hosting
- [ ] `frontend/.env.firebase` の作成・設定
- [ ] Cloud Run URLの設定
- [ ] Firebase プロジェクトURLの設定

## 🛠️ トラブルシューティング

### 環境変数が読み込まれない
```bash
# ファイルの存在確認
ls -la backend/.env
ls -la frontend/.env.local

# 設定内容確認
python scripts/diagnose_config.py
```

### APIキーエラー
```bash
# APIキー検証スクリプト
./scripts/verify-api-keys.sh
```

## 参考リンク

- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/)
- [Firebase Hosting Environment Variables](https://firebase.google.com/docs/hosting/functions)
