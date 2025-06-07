# gamechat-ai - AIチャット型ゲーム攻略アシスタント

ゲーム攻略情報を活用し、チャット形式で質問に答えるAIアシスタントです。  
RAG（検索拡張生成）技術を用いて、攻略Wikiや公式ガイドなどの情報を文脈に沿って提供します。

---

## 技術スタック

### フロントエンド
- Next.js (React + TypeScript)
- Tailwind CSS

### バックエンド
- Python + FastAPI
- Firebase Functions（オプション）

### AI・検索関連
- OpenAI API (ChatGPT, Embedding)
- Upstash Vector（ベクトル検索サービス／Dense Index対応）
- Python（データ埋め込み・アップロードスクリプト）

### インフラ・ホスティング
- Firebase Hosting / Vercel（フロントエンド）
- Firebase Firestore / Upstash Vector（データベース）
- AWS Lambda / Firebase Functions（サーバレスAPI）

---

## 開発環境

- `.nvmrc` により Node.js バージョンを統一（例: `18`）
- `.env.example` を `.env` にコピーして環境変数を設定
- `requirements.txt` により Python パッケージのバージョンを固定
- `package-lock.json` や `package.json` は**バックエンドでは不要**（FastAPI運用時）

| ツール / 言語          | バージョン例    | 備考                                      |
|----------------------|------------------|-------------------------------------------|
| Node.js              | 18.x 以上        | `nvm` でバージョン管理（フロント用）      |
| npm                  | 9.x 以上         | パッケージ管理（フロント用）              |
| React                | 19.x             | フロントエンドUIライブラリ                |
| Python               | 3.9〜3.11        | 埋め込み処理やRAG部分で使用               |
| FastAPI              | 最新             | バックエンドAPI                           |
| VS Code              | 最新             | 開発用IDE                                 |
| Git                  | 最新             | バージョン管理ツール                      |
| OpenAI API           | 利用予定         | `.env` にキーを設定                       |
| Upstash Vector       | 利用予定         | `.env` にURL・トークンを設定              |

### バージョン管理ファイル

- `.nvmrc`: Node.js のバージョン指定
- `.venv/`: Python 仮想環境ディレクトリ（`python -m venv .venv` で作成）
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

- フロントエンド

```bash
npm install
cd frontend
npm install
cd ../backend
npm install
```

- バックエンド（FastAPI）

```bash
cd ../backend
python -m venv .venv
source .venv/bin/activate  # Windowsの場合は .venv\Scripts\activate
pip install -r [requirements.txt](http://_vscodecontentref_/0)
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

- バックエンド（FastAPI）:  
  ```bash
  cd backend
  uvicorn app.main:app --reload 
  ```
  → http://localhost:8000

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
├── backend/                      # Python + FastAPI（バックエンドAPI）
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPIアプリケーション
│   │   ├── config/
│   │   │   └── ng_words.py
│   │   ├── core/
│   │   │   ├── config.py          # 環境変数・設定
│   │   │   └── exception_handlers.py
│   │   ├── models/
│   │   │   └── rag_models.py      # Pydanticモデル
│   │   ├── routers/
│   │   │   └── rag.py             # APIエンドポイント
│   │   └── services/
│   │       ├── auth_service.py    # 認証処理
│   │       ├── embedding_service.py  # エンベディング
│   │       ├── vector_service.py  # ベクトル検索
│   │       └── llm_service.py     # LLM処理
│   ├── tests/
│   │   ├── test_api.py            # サービス層のテスト
│   │   ├── test_llm_service.py            # サービス層のテスト
│   │   ├── test_response_guidelines.py  # ガイドラインに基づく応答テスト
│   │   └── test_vector_service.py # ベクトル検索のテスト
│   └── requirements.txt
│
├── data/                         # 攻略データ（git管理外）
│
├── scripts/                      # Pythonスクリプト
│   ├── convert_to_format.py  
│   ├── embedding.py
│   ├── rag_query_answer.py
│   └── upstash_connection.py
│
├── docs/                         # ドキュメント
│   ├── talk-guidelines.md        # 雑談対応ガイドライン
│   ├── rag_api_spec.md           # RAG API仕様書
│   └── assistant-ui-notes.md     # UIに関するメモ
│
├── .nvmrc
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

## ベクトルDB（Upstash Vector）へのインデクシング・アップロード

### 概要
エンベディング済みの攻略データ（例: `embedding_list.jsonl`）を、Upstash Vectorにアップロードし、ベクトル検索可能な状態にします。

### インデックス管理方針
- Upstash Vectorのインデックスは「Dense（密）」型で作成してください（OpenAIのエンベディングは密ベクトルです）。
- データごとに `namespace` を分けて管理することで、用途や種類ごとの検索が可能です。
- インデックスのURLやトークンは `backend/.env` で安全に管理します。

### アップロード処理
- `scripts/upstash_connection.py` を利用して、`embedding_list.jsonl` の各行（1ベクトルずつ）をUpstash Vectorにアップロードします。
- スクリプトは以下のように実行します。

```bash
python upstash_connection.py
```

### スクリプトの主な流れ:
- .env からUpstashの接続情報を読み込む
- embedding_list.jsonl を1行ずつ読み込み、各ベクトルを Vector オブジェクトとして生成
- namespace ごとにUpstash Vectorへ upsert で登録
- アップロードが完了したベクトルIDを標準出力に表示

### 注意事項
- インデックスの型（Dense/Sparse）がデータと一致していることを必ず確認してください。
- APIキーやトークンなどの機密情報は .env で管理し、Gitには絶対に含めないでください。
- 大量データをアップロードする場合は、APIレート制限やエラー処理に注意してください。

---

## RAG API仕様

本APIはカードゲームのカード名に関する自然言語の質問に対し、検索拡張生成（RAG）を用いた回答を返します。

- エンドポイント：POST `/api/rag/query`
- リクエスト例・レスポンス例・バリデーション・セキュリティ対策などは [RAG API仕様書](./docs/rag_api_spec.md) を参照してください。

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

# データディレクトリ（サンプルや生成データ）
data/
```

---

## 注意事項

- OpenAI APIキーなどの機密情報は**絶対に公開しないでください**。
- `.env` ファイルは `.gitignore` で管理されています。

---

## 作者

MASAKI