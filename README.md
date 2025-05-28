# gamechat-ai - AIチャット型ゲーム攻略アシスタント

ゲーム攻略情報を活用し、チャット形式で質問に答えるAIアシスタントです。  
RAG（検索拡張生成）技術を用いて、攻略Wikiや公式ガイドなどの情報を文脈に沿って提供します。

---

## 技術スタック

### フロントエンド
- Next.js (React + TypeScript)
- Tailwind CSS
- assistant-ui（shadcn/uiベース）

### バックエンド
- Node.js + Express
- Firebase Functions（オプション）

### AI・検索関連
- OpenAI API (ChatGPT, Embedding)
- Pinecone（ベクトル検索サービス）
- Python（データ埋め込み・アップロードスクリプト）

### インフラ・ホスティング
- Firebase Hosting / Vercel（フロントエンド）
- Firebase Firestore / Pinecone（データベース）
- AWS Lambda / Firebase Functions（サーバレスAPI）

---

## 開発環境

- `.nvmrc` により Node.js バージョンを統一（例: `18`）
- `.env.example` を `.env` にコピーして環境変数を設定
- `package-lock.json` により依存パッケージのバージョンを固定

| ツール / 言語          | バージョン例    | 備考                                      |
|----------------------|------------------|-------------------------------------------|
| Node.js              | 18.x 以上        | `nvm` でバージョン管理                   |
| npm                  | 9.x 以上         | パッケージ管理                            |
| React                | 19.x            |フロントエンドUIライブラリ                 |
| Python               | 3.9〜3.11        | 埋め込み処理やRAG部分で使用               |
| VS Code              | 最新             | 開発用IDE                                  |
| Git                  | 最新             | バージョン管理ツール                      |
| OpenAI API           | 利用予定         | `.env` にキーを設定                       |

### バージョン管理ファイル

- `.nvmrc`: Node.js のバージョン指定
- `.venv/`: Python 仮想環境ディレクトリ（`python -m venv .venv` で作成）
- `package-lock.json`: Node.js パッケージの固定
- `requirements.txt`: Python の依存パッケージ一覧
- `.env.example`: 環境変数のテンプレート

---

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourname/gamechat-ai.git
cd gamechat-ai
```

### 2. 依存パッケージのインストール

```bash
npm install
cd frontend
npm install
cd ../backend
npm install
```

### 3. 環境変数ファイルの作成

- `backend/.env` に OpenAI APIキー等を設定してください。
  ```
  OPENAI_API_KEY=your_openai_api_key
  PINECONE_API_KEY=your_pinecone_api_key
  ```
- `frontend/.env` は通常不要ですが、APIエンドポイント等を設定したい場合に利用します。

### 4. 開発サーバーの起動

- フロントエンド（Next.js）:  
  ```bash
  cd frontend
  npm run dev
  ```
  → http://localhost:3000

- バックエンド（Express）:  
  ```bash
  cd backend
  npm run dev
  ```
  → http://localhost:4000

---

## ディレクトリ構成

```
gamechat-ai/
├── frontend/                     # Next.js + TypeScript
│   ├── public/
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── utils/
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── .env
│
├── backend/                      # Node.js + Express
│   ├── src/
│   │   ├── routes/
│   │   ├── services/
│   │   └── index.ts
│   ├── package.json
│   └── .env
│
├── data/                         # 攻略データ（RAG用）
│   └── sample_data.json
│
├── scripts/                      # Pythonスクリプト
│   └── embed_and_upload.py
│
├── README.md
└── .gitignore
```

---

## テスト環境・実行方法

本プロジェクトのフロントエンド（Next.js）は、**Jest + React Testing Library** を用いてテストを実行します。

### 主なテスト関連パッケージ

- **Jest**: v29系
- **React Testing Library**: v16系（`@testing-library/react@16`）
- **jest-environment-jsdom**: v29系（`jest-environment-jsdom@29`）
- **ts-jest**: TypeScript用Jestトランスパイラ
- **@testing-library/jest-dom**: DOM用カスタムマッチャ

### インストール

```bash
npm install
cd frontend
npm install
```

### テストの実行

```
npm test
# または
npx jest
```

### 注意事項

- ESM依存の多いパッケージ（@assistant-ui系など）は jest.config.js の transformIgnorePatterns で対応しています。
- 型定義がないパッケージは @types/hast や @types/json-schema などを追加してください。
- Jestの設定は frontend/jest.config.js を参照してください。
- テストでは frontend/tsconfig.test.json を参照しています。

---

## CI/CD（CircleCI）

本プロジェクトは [CircleCI](https://circleci.com/) によるCI/CDパイプラインを導入しています。

- 依存パッケージのインストール
- ビルド
- テスト
- サーバー起動確認

これらのジョブが自動で実行され、mainブランチへのマージやPull Request作成時に品質チェックが行われます。

CircleCIの設定は `.circleci/config.yml` を参照してください。

---

## Gitブランチ命名ルール

<タイプ>/<変更内容>-<issue番号（任意）>

### タイプの種類：
- `feature`：新機能の追加
- `fix`：バグ修正
- `refactor`：リファクタリング（挙動を変えない改善）
- `chore`：設定ファイルやREADMEの更新など
- `test`：テストの追加・修正

---

## .gitignore（推奨）

```
# Next.js build output
.next/
# Node modules
node_modules/
# OS files
.DS_Store
Thumbs.db
# Env files
.env
.env.local
.env.*.local
# Log files
npm-debug.log*
yarn-debug.log*
yarn-error.log*
# Editor settings
.vscode/
# Test coverage
coverage/
```

---

## 注意事項

- OpenAI APIキーなどの機密情報は**絶対に公開しないでください**。
- `.env` ファイルは `.gitignore` で管理されています。

---

## 作者

MASAKI