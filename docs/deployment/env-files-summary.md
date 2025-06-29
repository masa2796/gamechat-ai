# GameChat AI プロジェクト - .envファイル一覧と用途まとめ

## 概要
このドキュメントは、プロジェクト内で利用されている .env 系ファイルの一覧・用途・不要判定・主な利用箇所をまとめたものです。

---

## ルートディレクトリ

| ファイル名         | パス                                 | 用途                           | 不要かどうか | 使用されている場所例・備考 |
|--------------------|--------------------------------------|--------------------------------|--------------|---------------------------|
| .env.ci            | /Users/masaki/Documents/gamechat-ai/.env.ci            | CI/CD用ダミー値                | 必要         | CIテスト用                |
| .env.local         | /Users/masaki/Documents/gamechat-ai/.env.local         | ローカル開発用                 | 必要         | backend, scripts/data-processing/ など |
| .env.template      | /Users/masaki/Documents/gamechat-ai/.env.template      | テンプレート（サンプル値）     | 必要         | 新規環境構築時の雛形      |

---

## backend ディレクトリ

| ファイル名         | パス                                 | 用途                           | 不要かどうか | 使用されている場所例・備考 |
|--------------------|--------------------------------------|--------------------------------|--------------|---------------------------|
| .env               | backend/.env                         | backend開発用                  | 必要         | backend/app/core/config.py |
| .env.production    | backend/.env.production              | backend本番用                  | 必要         | backend/app/core/config.py |
| .env.test          | backend/.env.test                    | backendテスト用                | 必要         | テスト・CI用              |

---

## frontend ディレクトリ

| ファイル名             | パス                                         | 用途                           | 不要かどうか | 使用されている場所例・備考 |
|------------------------|----------------------------------------------|--------------------------------|--------------|---------------------------|
| .env.ci                | frontend/.env.ci                             | フロントCI/CD用                | 必要         | CIビルド用                |
| .env.development       | frontend/.env.development                    | フロント開発用                 | 必要         | npm run dev など           |
| .env.firebase          | frontend/.env.firebase                       | Firebase Hosting用             | 必要         | firebase-deploy.sh, デプロイ時 |
| .env.local             | frontend/.env.local                          | フロントローカル開発用         | 必要         | npm run dev など           |
| .env.production.bak    | frontend/.env.production.bak                 | フロント本番用バックアップ     | 必要         | firebase-deploy.sh など    |
| .env.template          | frontend/.env.template                       | フロント用テンプレート         | 必要         | 新規環境構築時の雛形      |
| .env.test              | frontend/.env.test                           | フロントE2Eテスト用            | 必要         | tests/e2e/global-setup.ts  |

---

## 不要なファイル判定

- いずれも用途が明確で、テンプレートやテスト用もCIや新規環境構築時に利用されるため「不要な.envファイルは現状なし」と判断できます。
- `.env.production.bak` などは一時的なバックアップ用途ですが、運用上不要であれば削除可能です。

---

## 参照・利用箇所例

- backend: `backend/app/core/config.py` で `dotenv` により `.env`, `.env.production` などを読み込み
- frontend: Next.js/Node.jsの標準的な環境変数読み込み（`process.env`）、`firebase-deploy.sh` で `.env.firebase` などをコピー・編集
- テスト: `frontend/tests/e2e/global-setup.ts` で `.env.test` を明示的に読み込み

---

**補足**  
- `.env.template`/`.env.local` などは新規開発者やCI/CDセットアップ時の雛形として必須です。
- `.env.production` など本番用はGit管理外（.gitignore推奨）です。

---

最終更新: 2025-06-29
