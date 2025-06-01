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
- Upstash Vector（ベクトル検索サービス／Hybrid Index対応）
- Python（データ埋め込み・アップロードスクリプト）

### インフラ・ホスティング
- Firebase Hosting / Vercel（フロントエンド）
- Firebase Firestore / Upstash Vector（データベース）
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
| React                | 19.x             | フロントエンドUIライブラリ                |
| Python               | 3.9〜3.11        | 埋め込み処理やRAG部分で使用               |
| VS Code              | 最新             | 開発用IDE                                 |
| Git                  | 最新             | バージョン管理ツール                      |
| OpenAI API           | 利用予定         | `.env` にキーを設定                       |
| Upstash Vector       | 利用予定         | `.env` にURL・トークンを設定              |

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
  UPSTASH_VECTOR_REST_URL=your_upstash_vector_url
  UPSTASH_VECTOR_REST_TOKEN=your_upstash_vector_token
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
├── frontend/                     # Next.js + TypeScript（フロントエンド）
│   ├── public/
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   ├── components/           # UIコンポーネント
│   │   ├── hooks/                # Reactカスタムフック
│   │   ├── lib/                  # ライブラリ・ユーティリティ
│   │   └── utils/                # 汎用ユーティリティ
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── vitest.config.ts
│   ├── vitest.setup.ts
│   ├── tsconfig.json
│   └── .env
│
├── backend/                      # Node.js + Express（バックエンドAPI）
│   ├── src/
│   │   ├── routes/
│   │   ├── services/
│   │   └── index.ts
│   ├── package.json
│   └── .env
│
├── data/                         # 攻略データ（git管理外）
│
│
├── scripts/                      # Pythonスクリプト
│   ├── convert_to_embedding_format.py  
│   ├── embed_and_upload.py
│   └── test_upstash_connection.py  # Upstash Vector接続テストスクリプト
│
├── .nvmrc
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

---

## ベクトルDBサービスについて

Upstash Vector（Hybrid Index対応）を利用しています。
ベクトルのテストやアップロードには scripts/test_upstash_connection.py などのPythonスクリプトを利用します。

---

## テスト環境・実行方法

### テストフレームワーク
このプロジェクトでは、テストフレームワークとして [Vitest](https://vitest.dev/) を使用しています。Vitest は Vite をベースとした高速なテストランナーです。

### 主なテスト関連パッケージ
- **vitest**: 高速なテストランナー。
- **@testing-library/react**: React コンポーネントのテストを容易にするためのユーティリティ。
- **@testing-library/jest-dom**: DOM の状態をアサートするためのカスタム Jest マッチャを提供 (Vitest でも利用可能)。
- **@testing-library/user-event**: より現実に近いユーザーインタラクションをシミュレート。
- **jsdom**: テスト環境でブラウザの DOM API をシミュレート。
- **@vitejs/plugin-react**: Vitest で React プロジェクトをサポートするための Vite プラグイン。
- **@types/jest**: Jest のグローバルな型定義（`describe`, `it` など）。Vitest は Jest と互換性のある API を多く提供しており、`globals: true` 設定と合わせてこれらの型定義が利用されることがあります。

### 設定ファイル
- **`frontend/vitest.config.ts`**: Vitest の設定ファイル。テストファイルの場所、セットアップスクリプト、カバレッジ設定などが定義されています。
- **`frontend/vitest.setup.ts`**: グローバルなテストセットアップファイル。`@testing-library/jest-dom` のインポートなど、各テストファイルの前に実行したい処理を記述します。
- **`frontend/tsconfig.json`**: TypeScript の設定ファイル。Vitest はこの設定（特に `paths` エイリアスなど）を参照します。

### テストの実行
`frontend` ディレクトリで以下のコマンドを実行します。

- **すべてのテストを実行:**
  ```bash
  npm test
  ```

  ---

## Gitブランチ命名ルール

`<タイプ>/<変更内容>-<issue番号（任意）>`

### タイプの種類：

- `feature`：新機能の追加
- `fix`：バグ修正
- `refactor`：リファクタリング（挙動を変えない改善）
- `chore`：設定ファイルやREADMEの更新など
- `test`：テストの追加・修正

---

## .gitignore（推奨）

```
# .env files (root, frontend, backend)
.env
.env.local
.env.*.local
frontend/.env
backend/.env

# Python仮想環境
.venv

# Node modules
node_modules/
frontend/node_modules/
backend/node_modules/

# Build output / cache
.next/
dist/
frontend/dist/
backend/dist/
coverage/

# Log files
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Editor/IDE settings
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# データディレクトリ（サンプルや生成データは原則Git管理外）
data/
```

---

## 注意事項

- OpenAI APIキーなどの機密情報は**絶対に公開しないでください**。
- `.env` ファイルは `.gitignore` で管理されています。

---

## 作者

MASAKI