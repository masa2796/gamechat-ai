# 📦 Release MVP 開発タスク整理

最終更新: 2025-09-19（branch: `release-mvp-120`）

## 🎯 目的（Why）

最小限の機能でアプリをリリースし、ユーザーに **触ってもらうことを最優先** にする。
機能追加や最適化よりも **「動く状態」** を重視する。

---

## 🛠️ ゴール（What）

* **フロントエンド**

  * シンプルなチャットUI
  * Firebase Hosting へデプロイ

* **バックエンド**

  * ユーザー入力を受け取るAPI
  * OpenAI API を呼び出して応答生成
  * ベクトル検索（Upstash Vector）のみ実装
  * Cloud Run へデプロイ

* **データ**

  * ベクトル化済みのカードデータ
  * 最小限の情報のみを格納

---

## ⏭️ 次にやること（Next）

1) フロントの公開準備
  - Firebase Hosting 設定の追加（`firebase.json` の hosting 設定を確認/追記）
  - `NEXT_PUBLIC_MVP_MODE=true` でビルドし、Firebase Hosting へデプロイ
2) バックエンドの公開準備
  - Cloud Run へデプロイ（`backend/Dockerfile` 利用、必要な環境変数を `.env.prod` に整理）
3) データ投入
  - Upstash Vector へのカードデータ投入スクリプト作成（`scripts/data-processing/` 配置）と実行
4) ドキュメント最小整備
  - README 冒頭に利用方法（/chat エンドポイント、起動、環境変数）を追記
  - Deployment ガイドに Cloud Run + Firebase の最小手順を追記
  - 環境変数一覧を `docs/project/env_mvp.md` に切り出して参照リンク化
5) 軽微な運用準備
  - 非MVP機能に ARCHIVE_CANDIDATE 注記 or `docs/archive/` へ移動計画
  - `NEXT_PUBLIC_API_URL` 未設定時の相対パス挙動の簡易検証（README に追記）

---

## 🧭 クリティカルパス（実行順）

1) バックエンドを Cloud Run にデプロイし、`/chat` を公開（フォールバック込みで安定稼働）
2) Upstash Vector にカードデータを投入（検索が結果に反映される状態）
3) フロントエンドを Firebase Hosting へデプロイ（`NEXT_PUBLIC_MVP_MODE=true` で `/chat` を利用）
4) README と最小デプロイガイドを整備（環境変数・起動・エンドポイント）

---

## ✅ タスク一覧（How）

### フロントエンド

* [x] 入力欄＋送信ボタン＋チャット形式で応答を表示するコンポーネントを作成 (既存 `assistant` ページ流用)
* [x] 最低限のデザイン適用（モバイルで読めるレベル）
* [x] MVP用API切替ロジック（`NEXT_PUBLIC_MVP_MODE=true` で `/api/rag/query` → `/chat` に切替）
* [ ] Firebase Hosting 用の設定追加 & デプロイ
  - 詳細: `firebase.json` に hosting 設定を追加（public/rewrites など最小）、`NEXT_PUBLIC_MVP_MODE=true` でビルドしデプロイ
  - DoD: 公開URLでトップが表示でき、チャットが `/chat` 経由で応答を返す（モバイルで視認性OK）

### バックエンド

* [x] `/chat` API を既存 `rag.py` 内にシンプル実装（専用MVPファイルを撤廃）
* [x] OpenAI Embedding を利用（未設定時は擬似ベクトルにフォールバック）/ 回答はスタブLLM（フォールバック時は WARN ログ／通常は INFO）
* [x] Upstash Vector への問い合わせ実装（`VectorService`。未設定時はダミータイトル生成でフォールバック）
* [x] 検索結果（カード簡易情報）をプロンプトに組み込み回答生成
* [ ] Cloud Run へデプロイ（DockerfileはMVP簡素化済み。実デプロイは未実施）
  - 詳細: `backend/Dockerfile` を利用してビルド→Cloud Run へデプロイ。必要な環境変数を設定
    - 必須/推奨: `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`、（任意）`BACKEND_OPENAI_API_KEY`
  - DoD: 公開URLで `POST /chat` が 200 を返し、`with_context=true/false` の両方が期待通り動作

### データ

* [ ] ベクトル化済みカードデータをUpstashに格納（現状: タイトルで検索しローカル/Cloudの JSON から最小抽出）
  - 詳細: `scripts/data-processing/` に投入スクリプトを作成し、`data/convert_data.json` または `data/data.json` を入力としてアップサート
  - DoD: Upstash 側のインデックス件数が期待値以上、かつ `/chat` の検索結果に反映
* [x] 必要最低限の情報のみ残す（`mvp_chat` は title / effect_1 / 基本ステータスのみ返却）
* [x] ローカル/Cloud JSON（`convert_data.json` / `data.json`）からの最小インデックス読み込み

---

## 🔄 追加メモ (MVP進捗)

* 既存 `rag.py` の `/chat` をシンプル実装へ置換（認証 / reCAPTCHA / ハイブリッド検索除外）
* フロントは `NEXT_PUBLIC_MVP_MODE=true` で `/api/rag/query` → `/chat` に切替（`frontend/src/app/assistant/useChat.ts`）
* 失敗時も UX を保つフォールバック（擬似埋め込み / ダミータイトル / 汎用回答）
* 実施済み: モバイル向け最小スタイル微調整（100dvh対応・自動スクロール・余白/フォーカス等）
* 今後: Cloud Run デプロイ手順 / Firebase Hosting 設定追記

---

## 📄 API契約（MVP /chat）

- エンドポイント: POST `/chat`
- リクエスト: `{ "message": string, "top_k"?: number=5, "with_context"?: boolean=true }`
- レスポンス: `{ "answer": string, "context"?: Array<object> | null, "retrieved_titles": string[] }`
- 実装: `backend/app/routers/rag.py`

備考:
- Embedding 生成に失敗/未設定時は擬似ベクトルで継続
- Upstash Vector が未設定でもフォールバック（ダミータイトル生成）
- `with_context=false` の場合は `context` を省略

---

## 🚫 除外範囲（Will Not Do）

* 挨拶検出・早期応答システム（削除済み）
* ハイブリッド検索（BM25 + ベクトル検索）
* 複合条件検索 / 戦略的推薦機能
* 検索モード自動選択（FILTERABLE / SEMANTIC / HYBRID）
* カード詳細ページ (`/cards/{card_id}/details`)
* 高度なエラーハンドリング・動的閾値調整
* 包括的テスト（Smoke Test のみ残す）
* モニタリング機能（Sentry, Prometheusなど）

---

## � 除外タスクの状況・運用（明確化）

以下の項目はMVPでは実装対象外です。関連コードや資料は「アーカイブ移行候補」として残置し、MVPの稼働には影響しません。

- 挨拶検出・早期応答システム
  - 状況: 削除済み（MVPからの恒久除外）
  - 関連: なし（関連スクリプト/ドキュメントを削除）
  - 影響: なし（`/chat` は一律ベクトル検索）

- ハイブリッド検索（BM25 + ベクトル検索）
  - 状況: 除外（未使用）
  - 関連: 該当実装/テストは削除済み（2025-09-22）。ドキュメント参照はアーカイブ候補（ARCHIVE_CANDIDATE）
  - 影響: なし（MVPはベクトル単独）

- 複合条件検索 / 戦略的推薦機能
  - 状況: 除外（未対応・未使用）
  - 関連: 該当実装なし（将来設計）。関連ユーティリティ `scripts/utilities/cleanup_compound_features.sh` は無効化（no-op）
  - 影響: なし

- 検索モード自動選択（FILTERABLE / SEMANTIC / HYBRID）
  - 状況: 除外（未使用）
  - 関連: `backend/app/services/classification_service.py`、`backend/app/models/classification_models.py`（ARCHIVE_CANDIDATE）
  - 影響: なし（MVPは固定でベクトル検索）

- カード詳細ページ (`/cards/{card_id}/details`)
  - 状況: 除外（未対応）
  - 影響: なし（チャットUIのみ）

- 高度なエラーハンドリング・動的閾値調整
  - 状況: 除外（未対応）
  - 影響: なし（最小のエラーハンドリング）

- 包括的テスト（Smoke Test のみ残す）
  - 状況: 除外（網羅テストは実施せず）
  - 代替: Smoke/フォールバック系のみ実行（現状 PASS）

- モニタリング機能（Sentry, Prometheusなど）
  - 状況: 除外（未使用）
  - 関連: `monitoring/` ディレクトリ、`docker-compose.monitoring.yml`（ARCHIVE_CANDIDATE）
  - 影響: なし

---

## �🚀 リリース後の流れ

1. MVPをユーザーに触ってもらう
2. フィードバック収集
3. 優先度が高い機能から追加していく

---

## 🗑️ MVP向け整理方針（2025-09-07）

MVPで不要と判断した高度機能は「即時削除」ではなく「アーカイブ移行候補」として扱い、動作に影響しない範囲で段階的に縮小します。将来拡張時は Git 履歴/`docs/archive/` から参照。

### 整理理由カテゴリ
- Hybrid検索 / 複合戦略: MVPはベクトル単独
- クエリ分類 / 挨拶検出: `/chat` は一律ベクトル検索
- 高度RAG統合 / 詳細取得: シンプル回答生成のみ
- モニタリング / パフォーマンス最適化: 初期リリースでは後回し
- 大量テスト: Smokeレベルへ縮小

### アーカイブ移行候補（現状: リポジトリ内に残置）
1. ルーター重複: `backend/app/routers/mvp_chat.py`（現状はスタブ化済み）
2. 検索高度化:
  - `backend/app/services/hybrid_search_service.py`
  - `backend/app/services/classification_service.py`
  - `backend/app/services/rag_service.py`
  - `backend/app/models/classification_models.py`
3. テスト: ハイブリッド / 分類 / RAG 関連
  - `backend/app/tests/services/test_hybrid_search_consolidated.py` ほか
4. スクリプト: （該当なし）
5. モニタリング/監視
  - `monitoring/` ディレクトリ一式
  - `docker-compose.monitoring.yml`
6. ドキュメントの整理対象
  - `docs/guides/search-hybrid-guide.md` ほか関連セクション

補足: アーカイブ運用ルール
- 対象ファイル/ディレクトリには `ARCHIVE_CANDIDATE` の注記コメントまたはドキュメント注釈を付与
- 実移動する場合は `docs/archive/` 配下に置き、参照元からリンク
- 将来的に復活させる際は、本セクションとGit履歴を起点に要件再定義

### 残すもの（MVP稼働に必要）
- `/chat` を提供する最小 FastAPI ルーター（`backend/app/routers/rag.py`）
- `EmbeddingService`, `VectorService`, `LLMService`, `StorageService`
- ベクトル検索の最小検証テスト: `backend/app/tests/test_mvp_chat_basic.py`

---

## 🔧 環境変数（MVP）

フロントエンド:
- `NEXT_PUBLIC_API_URL`（例: バックエンドの公開URL）
- `NEXT_PUBLIC_MVP_MODE=true`（`/chat` を使う）
- `NEXT_PUBLIC_API_KEY`（必要ならヘッダーに付与。MVPでは必須でない想定）

バックエンド:
- `BACKEND_OPENAI_API_KEY`（未設定時は擬似Embeddingへフォールバック）
- `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`（未設定時はダミータイトル生成）
- `BACKEND_TESTING`, `BACKEND_MOCK_EXTERNAL_SERVICES`（テスト/モック切替）

---

## 🧪 テスト状況（MVP）

- バックエンドの最小テストを整備：
  - Smoke: `/chat` が 200 を返し最小レスポンス構造を満たす
  - フォールバック: OpenAIキー未設定時／Upstash未設定時／`with_context=false` の挙動
- 現在の結果: PASS（`pytest backend/app/tests/ -q`）

実行コマンド（ローカル）：

```bash
pytest backend/app/tests/ --maxfail=3 --disable-warnings -q
```

受け入れ条件（DoD: テスト）:
- Smoke が PASS（`answer`, `retrieved_titles`, `context?` を満たす）
- フォールバック各条件で 200 と妥当な応答が返る（擬似Embedding/ダミータイトル/`with_context=false`）

---

## 🔗 依存関係・優先度

- P0: Cloud Run デプロイ（/chat 稼働）、Upstash へのデータ投入、Firebase Hosting デプロイ、README/デプロイガイド整備
- P1: `NEXT_PUBLIC_API_URL` 未設定時の相対パス挙動メモの追記、非MVP機能の ARCHIVE 注記
- P2: 任意の改善（UI微調整など）

---

## ✅ Definition of Done（MVP全体）

- 公開URLでチャットが一通り機能（モバイルで視認性OK）
- Cloud Run 上の `/chat` が安定稼働し、Upstash あり/なし双方でフォールバック含めて応答可能
- README と最小デプロイ手順が整備済み（エンドポイント・環境変数・起動）
- Smoke テストが PASS（主要ケース）

---

## 🚢 デプロイ概要（MVP）

- バックエンド: `backend/Dockerfile` は単段構成に簡素化（`uvicorn` 直接起動）。Cloud Run へのデプロイ準備済み
- フロントエンド: Firebase Hosting を想定（設定・実デプロイは未着手）

ヒント（例）:
1) Cloud Run（例）
  - イメージビルド → デプロイ（必要な環境変数を設定）
2) Firebase Hosting（例）
  - `NEXT_PUBLIC_MVP_MODE=true` を設定しビルド/デプロイ

詳細手順は `docs/deployment/deployment-guide.md` を参照し、MVP前提の最小構成で実施してください。

---
