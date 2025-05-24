# gamechat-ai - AIチャット型ゲーム攻略アシスタント

ゲーム攻略情報を活用し、チャット形式で質問に答えるAIアシスタントです。  
RAG（検索拡張生成）技術を用いて、攻略Wikiや公式ガイドなどの情報を文脈に沿って提供します。

---

## 技術スタック

### フロントエンド
- React + TypeScript
- Vite
- Tailwind CSS

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

## 開発環境

本プロジェクトでは、以下の開発環境を推奨します。複数人で開発する場合でも環境の差異を最小限に抑えるため、バージョン管理ツールを併用することを推奨します。

### 開発環境のバージョン統一

- `.nvmrc` により Node.js バージョンを統一（例: `18`）
- `.env.example` を `.env` にコピーして環境変数を設定
- `package-lock.json` により依存パッケージのバージョンを固定

### 使用技術・ツール

| ツール / 言語       | バージョン例    | 備考                                      |
|----------------------|------------------|-------------------------------------------|
| Node.js              | 18.x 以上        | `nvm` でバージョン管理                   |
| npm                  | 9.x 以上         | パッケージ管理                            |
| Python               | 3.9〜3.11        | 埋め込み処理やRAG部分で使用               |
| VS Code              | 最新             | 開発用IDE                                  |
| Git                  | 最新             | バージョン管理ツール                      |
| OpenAI API           | 利用予定         | `.env` にキーを設定                       |

### バージョン管理ファイル（プロジェクトに同梱）

- `.nvmrc`: Node.js のバージョン指定
- `.python-version`: Python のバージョン指定（`pyenv`用）
- `package-lock.json`: Node.js パッケージの固定
- `requirements.txt`: Python の依存パッケージ一覧
- `.env.example`: 環境変数のテンプレート

### 開発環境のセットアップ手順（初回）

1. Node.js のインストール（nvm推奨）
   ```bash
   nvm install 18
   nvm use 18
   ```

## ディレクトリ構成

gamechat-ai/
├── frontend/                     # React + TypeScript
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/
│   │   ├── utils/
│   │   └── main.tsx
│   ├── vite.config.ts
│   ├── package.json
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

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourname/gamechat-ai.git
cd gamechat-ai
```

### 2. 依存パッケージのインストール（ルートでOK）

```bash
npm install
```

> ※初回のみ、`frontend` および `backend` ディレクトリでも `npm install` を実行してください。

### 3. 環境変数ファイルの作成

- `backend/.env` に OpenAI APIキー等を設定してください。
  ```
  OPENAI_API_KEY=your_openai_api_key
  PINECONE_API_KEY=your_pinecone_api_key
  ```
- `frontend/.env` は通常不要ですが、APIエンドポイント等を設定したい場合に利用します。

### 4. 開発サーバーの同時起動

```bash
npm run dev
```

- これでフロントエンド（http://localhost:5173）とバックエンド（http://localhost:4000）が同時に起動します。

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

## その他

- フロントエンドやバックエンドを個別に起動したい場合は、それぞれのディレクトリで `npm run dev` を実行してください。
- `.env.example` も用意しておくと、他の開発者が環境変数の設定内容を把握しやすくなります。

---

## 注意事項

- OpenAI APIキーなどの機密情報は**絶対に公開しないでください**。
- `.env` ファイルは `.gitignore` で管理されています。

---
## 作者

MASAKI