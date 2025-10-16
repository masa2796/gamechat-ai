# ローカル実行クイックスタート（MVP）

最小構成（MVP）でバックエンド/フロントエンドをローカル実行する手順です。OpenAI/Upstashのキーが未設定でもフォールバックで動作します。まずは動かすことを最優先にしています。

- 対象ブランチ: `release-mvp-120`
- バックエンド: FastAPI（/chat のみ）
- フロントエンド: Next.js（MVPモードで /chat を直接呼び出し）

---

## 前提環境

- macOS + zsh
- Node.js 18 以上 / npm
- Python 3.11 以上（3.13でも動作確認済み）
- Docker（任意。Composeでバックエンドを起動する場合）

> メモ: Docker Desktop を起動していると 8000 番ポートを使っていることがあるため、本手順ではバックエンドを 8001 で起動します。

---

## 1) バックエンド（FastAPI）

Python 仮想環境と依存をセットアップし、Uvicorn で起動します。

```bash
# プロジェクトルート
python3 -m venv .venv
source .venv/bin/activate

# 依存インストール
pip install --upgrade pip
pip install -r backend/requirements.txt

# バックエンド起動（8001）
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

ヘルスチェック:
```bash
curl -s http://localhost:8001/health
```

ポート競合（8000が使用中）を調べる:
```bash
lsof -i :8000 | sed -n '1,5p'
```

- 8000 を使いたい場合は、該当プロセスを停止するか Docker 側を止めるなどで解放してください
- 本ドキュメントでは衝突回避のため 8001 で進めます

---

## 2) フロントエンド（Next.js）

MVPモードで `/chat` に直接POSTするため、以下の 2 つの環境変数を使用します。

- `NEXT_PUBLIC_API_URL=http://localhost:8001`
- `NEXT_PUBLIC_MVP_MODE=true`

`.env.local` はリポジトリ内で以下のように設定済みです（差分要約）。必要に応じて値をご確認ください。

```
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_MVP_MODE=true
```

起動:
```bash
cd frontend
npm install
npm run dev
# http://localhost:3000 にアクセス
```

---

## 3) API を直接試す（任意）

```bash
curl -s -X POST http://localhost:8001/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"強いカードを教えて"}' | jq
```

OpenAI/Upstash のキーが未設定でも、擬似ベクトル + ダミータイトル生成で 200 応答します。

---

## 4) 代替: Docker Compose でバックエンドのみ起動

MVPの前提では Docker で backend のみ起動します（ポート: 8000）。

```bash
# バックエンドのみDockerで起動
npm run dev:docker
npm run dev:logs  # ログの確認
```

この場合はフロントの `frontend/.env.local` を 8000 向けに調整してください。

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MVP_MODE=true
```

---

## トラブルシューティング

- CORS でブロックされる
  - `backend/.env` の `BACKEND_CORS_ORIGINS` を確認。デフォルトで `http://localhost:3000` は許可されています
- OpenAI/Upstash のキーが無い
  - 未設定のままでOK（フォールバック実装あり）。本番接続時は `backend/.env` に設定してください
- データファイルが参照できない
  - `data/` 配下の `data.json` / `convert_data.json` / `embedding_list.jsonl` を参照。無い場合は文脈なしで回答します
- 8000 番ポートが使えない
  - 本手順のように 8001 で起動するか、占有プロセスを停止してください

---

## 品質チェック（任意）

- バックエンド テスト
  ```bash
  # プロジェクトルートで
  pytest backend/app/tests/ --maxfail=3 --disable-warnings -q
  ```
- フロント Lint/型チェック
  ```bash
  cd frontend
  npm run typecheck
  npm run lint
  ```

---

## 片付け

```bash
# バックエンド（Uvicorn）を終了: ターミナルで Ctrl+C
# フロント（Next.js）を終了: ターミナルで Ctrl+C
# 仮想環境の無効化

deactivate
```

---

## 参考

- バックエンドの最小環境変数例: `backend/.env.example`
- 既存ドキュメント: `docs/deployment/environment-setup.md`, ルート `README.md`
