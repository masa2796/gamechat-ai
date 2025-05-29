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