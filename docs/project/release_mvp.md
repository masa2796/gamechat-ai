# 📦 Release MVP 開発タスク整理

最終更新: 2025-10-12（branch: `release-mvp-120`）

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

## ✅ MVPタスク概要（最新整理）

- **バックエンド**: `backend/Dockerfile` を Cloud Run にデプロイし、`/chat` が `with_context` true/false の双方で 200 を返すことを確認。`UPSTASH_VECTOR_*` と任意の `BACKEND_OPENAI_API_KEY` を設定し、`pytest backend/app/tests/ -q` が引き続き PASS となるよう維持。
- **データ**: `scripts/data-processing/` に Upstash への投入スクリプトを整備し、`data/convert_data.json` などから最小項目をアップサート。投入後に `/chat` の `retrieved_titles` へ反映されることを検証。
- **フロントエンド**: `NEXT_PUBLIC_MVP_MODE=true` で `/chat` を利用する挙動を最終確認し、`firebase.json` の rewrites を活用して Firebase Hosting へデプロイ。`NEXT_PUBLIC_API_URL` 未設定時の挙動を README に明記。
- **ドキュメント**: `README.md`、`docs/deployment/cloud_run_firebase_mvp.md`、`docs/project/env_mvp.md` を MVP 前提で更新し、非MVP関連ガイドへ `ARCHIVE_CANDIDATE` 注記を追加。`docs/README.md` から必要資料へ辿れる導線を整備。
- **スクリプト・運用**: `scripts/deployment/deploy_cloud_run_mvp.sh` の実行権限を確認し、Firebase/Cloud Run 手順を掲載。`htmlcov/` や `logs/` は CI/CD から除外できるよう `.firebaseignore` や Cloud Build ignore を検討。

---

## 🧭 クリティカルパス（実行順）

1) バックエンドを Cloud Run にデプロイし、`/chat` を公開（フォールバック込みで安定稼働）
2) Upstash Vector にカードデータを投入（検索が結果に反映される状態）
3) フロントエンドを Firebase Hosting へデプロイ（`NEXT_PUBLIC_MVP_MODE=true` で `/chat` を利用）
4) README と最小デプロイガイドを整備（環境変数・起動・エンドポイント）

---

## 本日の横断確認による追加タスク/注意（P0/P1）

P0（最優先・ブロッカー防止）

- backend/.env.prod.example の追加/整備
  - 含める推奨キー: `BACKEND_ENVIRONMENT=production`, `BACKEND_LOG_LEVEL=INFO`, `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`, （任意）`BACKEND_OPENAI_API_KEY`
  - 備考: デプロイスクリプト側の表記 `LOG_LEVEL` と混在しないよう、バックエンドは `BACKEND_LOG_LEVEL` へ統一
- Upstash namespace 整合の明確化
  - 既存検索は「デフォルトnamespace」を参照（`VectorService` で namespace 未指定）
  - 迅速対応（MVP）: 投入時に `--namespace` を付けず「デフォルトnamespace」に投入する（スクリプト更新済）
  - 恒久対応（後追い）: 環境変数 `UPSTASH_VECTOR_NAMESPACE` を導入し、`Index.query(..., namespace=...)` を利用（`VectorService` 実装済）
- `.firebaseignore` の追加
  - 例: `htmlcov/`, `logs/`（必要に応じて `backend/`, `scripts/` など）を除外し、Hosting へ不要ファイルが載らないようにする
- CORS と環境判定の最終確認
  - 本番は FastAPI 側の `settings.CORS_ORIGINS`（Firebaseドメイン + localhost）。必要に応じて拡張
  - Cloud Run 本番では `BACKEND_ENVIRONMENT=production` を必ず設定
- デプロイスクリプトの実行権限
  - `scripts/deployment/deploy_cloud_run_mvp.sh`, `scripts/deployment/deploy_firebase_hosting_mvp.sh` に実行権限（macOS: `chmod +x`）

P1（できるだけ早めに）

- Cloud Build 運用整理（任意）
  - 手動スクリプト運用か Cloud Build かを一本化し、レジストリ/timeout設定の重複や差異を解消
- ドキュメント追記
  - 環境変数の命名差分（`BACKEND_LOG_LEVEL` と `LOG_LEVEL`）の扱いと、Upstash namespace 注意を `deployment-guide.md` / `cloud_run_firebase_mvp.md` / `env_mvp.md` に明記

## ✅ タスク一覧（How）

### フロントエンド

* [x] 入力欄＋送信ボタン＋チャット形式で応答を表示するコンポーネントを作成 (既存 `assistant` ページ流用)
* [x] 最低限のデザイン適用（モバイルで読めるレベル）
* [x] MVP用API切替ロジック（`NEXT_PUBLIC_MVP_MODE=true` で `/api/rag/query` → `/chat` に切替）
* [ ] Firebase Hosting 用の設定追加 & デプロイ
  - 詳細: `firebase.json` に hosting 設定を追加（public/rewrites など最小）、`NEXT_PUBLIC_MVP_MODE=true` でビルドしデプロイ（`mvp:build` スクリプト追加済）
  - 進捗: rewrites (`/chat` 含む) 追加済 / ビルドスクリプト追加済 / デプロイ未実施
  - DoD: 公開URLでトップが表示でき、チャットが `/chat` 経由で応答を返す（モバイルで視認性OK）

### バックエンド

* [x] `/chat` API を既存 `rag.py` 内にシンプル実装（専用MVPファイルを撤廃）
* [x] OpenAI Embedding を利用（未設定時は擬似ベクトルにフォールバック）/ 回答はスタブLLM（フォールバック時は WARN ログ／通常は INFO）
* [x] Upstash Vector への問い合わせ実装（`VectorService`。未設定時はダミータイトル生成でフォールバック）
* [x] 検索結果（カード簡易情報）をプロンプトに組み込み回答生成
* [ ] Cloud Run へデプロイ（DockerfileはMVP簡素化済み。実デプロイは未実施）
  - 詳細: `backend/Dockerfile` を利用してビルド→Cloud Run へデプロイ。必要な環境変数を設定（`.env.prod.example` 追加済）
    - 必須/推奨: `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`、（任意）`BACKEND_OPENAI_API_KEY`
  - 進捗: デプロイスクリプト `scripts/deployment/deploy_cloud_run_mvp.sh` 追加済 / 実デプロイ未実施
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
  - 状況: 削除済み（MVPからの恒久除外）
  - 関連: なし（該当実装ファイルは削除済み）
  - 影響: なし（MVPは固定でベクトル検索）

- カード詳細ページ (`/cards/{card_id}/details`)
  - 状況: 除外（未対応）
  - 影響: なし（チャットUIのみ）

- 高度なエラーハンドリング・動的閾値調整
  - 状況: 除外（未対応）
  - 影響: なし（最小のエラーハンドリング）
  - 補足（将来実装トリガー案）:
    - エラーハンドリング強化条件: 24h の 5xx 比率 > 2% または 同型 GameChatException > 50 件/日
    - 閾値調整開始条件: zero_hit_rate > 15% (直近100リクエスト移動平均) かつ total_requests >= 200
    - Precision 保持の上昇条件: plateau_events / total_requests < 8% かつ zero_hit_rate < 5%
    - 調整レンジ: 0.35 <= min_score <= 0.65 （ヒステリシス: 再調整間隔 >= 30 リクエスト）
    - 安全装備: ENV `VECTOR_DYNAMIC_THRESHOLD_ENABLED=true` でのみ有効化 / デフォルト無効
    - スタブ: `backend/app/services/dynamic_threshold_manager.py` は ARCHIVE_CANDIDATE として統計収集のみ

- 包括的テスト（Smoke Test のみ残す）
  - 状況: 除外（網羅テストは実施せず）
  - 代替: Smoke/フォールバック系のみ実行（現状 PASS）

 

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
  - `backend/app/services/rag_service.py`
  - （分類関連は削除済み）`backend/app/services/classification_service.py`, `backend/app/models/classification_models.py`
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

（最新版の一覧は `docs/project/env_mvp.md` を参照）

フロントエンド (抜粋): `NEXT_PUBLIC_MVP_MODE`, `NEXT_PUBLIC_API_URL`

バックエンド (抜粋): `BACKEND_OPENAI_API_KEY`, `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`

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

- バックエンド: `backend/Dockerfile` は単段構成に簡素化（`uvicorn` 直接起動）。Cloud Run 用スクリプト追加済み
- フロントエンド: Firebase Hosting 想定（`/chat` rewrite 追加 / ビルドスクリプト追加済）
- 詳細手順: `docs/deployment/cloud_run_firebase_mvp.md`

ヒント（例）:
1) Cloud Run（例）
  - イメージビルド → デプロイ（必要な環境変数を設定）
2) Firebase Hosting（例）
  - `NEXT_PUBLIC_MVP_MODE=true` を設定しビルド/デプロイ

詳細手順は `docs/deployment/deployment-guide.md` を参照し、MVP前提の最小構成で実施してください。

---

## 📁 ディレクトリ別タスク（MVP最小構成）

以下は「最小限の構成」で公開するために、各ディレクトリ単位で実施すべきタスクを整理したものです。区分の意味は次の通り:
- Keep: そのまま維持（必須）
- Adjust: 最小化や設定見直し（MVP向けの軽量化）
- Archive: 非MVP。`ARCHIVE_CANDIDATE` 注記 or `docs/archive/` へ移動候補
- No-op: 今回は操作不要（デプロイ対象外など）

### /（リポジトリ直下）
- Keep
  - `README.md`（MVPの使い方を冒頭に追記）
  - `firebase.json`（Hosting: rewrites に `/chat` を含む。現状追記済みを確認）
- Adjust
  - `cloudbuild.yaml`（Cloud Run に直接デプロイする場合は最小ジョブのみ残す or ドキュメント参照に留める）
  - `docker-compose.yml`（ローカル開発の最小構成: backend のみ or 必要最小限。監視系や非MVPサービスは無効化）
  - `docker-compose.prod.yml`（MVP運用では使用しない前提なら注記を追加）
  - `package.json`（ルートにある場合はドキュメント用スクリプトのみ残す。ビルドは各パッケージ側を主とする）
- Archive
  - 監視/高度運用向けの記述があれば注記（本番安定後に再検討）
- DoD
  - ルートREADMEに MVP 手順（/chat, 環境変数, 起動/デプロイ）を記述
  - デプロイに不要な compose/services は無効化方針が明記されている

### backend/
- Keep
  - `backend/Dockerfile`（単段構成、`uvicorn` 直接起動）
  - `backend/app/main.py`, `backend/app/routers/rag.py`（MVPの `/chat` を提供）
  - `backend/app/services/`（`EmbeddingService`, `VectorService`, `LLMService`, `StorageService`）
  - `backend/app/tests/test_mvp_chat_basic.py`（最小スモーク/フォールバック）
- Adjust
  - `backend/app/routers/mvp_chat.py` が残っていれば ARCHIVE 注記（重複ルーターは未使用）
  - `requirements.txt` は最小依存の確認（未使用パッケージの削減は任意）
  - Cloud Run 向け `.env.prod.example` を最新化（必須ENVの記載整備）
- Archive
  - 高度RAG/ハイブリッド関連: `services/hybrid_search_service.py`, `services/rag_service.py`（ドキュメント上は対象外）
  - 分類関連テスト/実装（既に削除済みまたは候補）
- DoD
  - Cloud Run 上で `POST /chat` が 200 を返す（`with_context` true/false 両対応）
  - Upstash未設定でもフォールバック応答可能（WARN/INFO ログ方針）
  - `pytest backend/app/tests/ -q` が PASS（Smoke）

### frontend/
- Keep
  - MVP用チャットUI（`assistant` ページ + `useChat.ts`）
  - `package.json` の `mvp:build` スクリプト
- Adjust
  - `NEXT_PUBLIC_MVP_MODE=true` で `/api/rag/query` → `/chat` に切替する挙動を最終確認
  - Firebase Hosting へデプロイ（`firebase.json` rewrites 確認済みのまま実施）
  - `NEXT_PUBLIC_API_URL` 未設定時の相対パス挙動を README に明記
- Archive
  - 非MVPページ/重い依存があれば一旦リンク外し or 注記
- DoD
  - 公開URLでトップが表示でき、`/chat` 経由で応答が得られる（モバイル読了性OK）

### scripts/
- Keep
  - `scripts/deployment/deploy_cloud_run_mvp.sh`（Cloud Run 最小デプロイ）
- Adjust
  - `scripts/data-processing/` に Upstash へのアップサートスクリプトを実装（`data/convert_data.json|data.json` から最小項目）
  - スクリプトに実行権限（macOS: `chmod +x`）
- Archive
  - 高度処理ユーティリティ（複合戦略/監視専用など）は注記のみに留める
- DoD
  - 1コマンドで Cloud Run デプロイが完了し、必要ENVが渡る
  - Upstash へのデータ投入が完了（件数が期待値以上）

### data/
- Keep
  - `data/convert_data.json`, `data/data.json`, `data/vector_index_effects.jsonl`（必要に応じて）
- Adjust
  - Upstash インデックスに必要な最小フィールドのみ投入（title / effect_1 / 基本ステータス）
  - データ量は初期検証に十分な最小セット
- DoD
  - `/chat` 検索結果に投入データが反映（retrieved_titles が期待通り）

### docs/
- Keep
  - 本ファイル（`docs/project/release_mvp.md`）
  - `docs/deployment/cloud_run_firebase_mvp.md` / `docs/deployment/deployment-guide.md`
  - `docs/project/env_mvp.md`（環境変数の一覧）
- Adjust
  - 非MVPドキュメントには `ARCHIVE_CANDIDATE` を注記し、リンクは残す
  - `docs/README.md` を MVP インデックスとして再構成（必読ドキュメントとアーカイブ候補を明示）
  - `docs/api/api-specification.md` を `/chat` + `/health` のみの仕様に刷新
  - `docs/deployment/deployment-guide.md` / `cloud_run_firebase_mvp.md` / `project/env_mvp.md` を最小手順に更新
- Archive
  - ハイブリッド検索などの詳細ガイドは `docs/archive/` へ移動候補
- DoD
  - MVP手順がここだけ見れば通せる最小構成で揃っている（`docs/README.md` から該当ドキュメントへ到達可能）

### nginx/
- No-op
  - MVPは Cloud Run + Firebase Hosting を前提とし Nginx は使用しない
- Adjust
  - リバースプロキシ構成の雛形として残す場合は README に「MVPでは未使用」と注記

### htmlcov/ ・ logs/
- No-op
  - デプロイ対象外。CI/CDやHostingから除外
  - 具体対応: ルートに `.firebaseignore` を追加し、`htmlcov/`, `logs/`（任意で `backend/`, `scripts/` など）を除外対象に設定
  - （任意）Cloud Build を使う場合はビルドコンテキストの除外方針も整理

### 受け入れ条件（ディレクトリ別タスク）
- ルート/バックエンド/フロント/スクリプト/データ/ドキュメントの各DoDを満たし、外形的に以下が成立
  - Cloud Run の `/chat` が 200 を返す（with/without context）
  - Firebase Hosting 公開URLでチャットが利用可能
  - Upstash の投入が検索結果に反映
  - 非MVP要素は `ARCHIVE_CANDIDATE` の注記または参照のみ

---

## ✅ 実施内容と次アクション（2025-10-17）

本日の作業で、MVPバックエンドの4要件「/chat API・OpenAI応答・Upstash Vector検索・Cloud Runデプロイ準備」を実装・確認し、テストまで完了しました。要点は以下です。

### 実施内容（Done）

- /chat API 実装確認
  - `backend/app/routers/rag.py` にて、リクエスト `{ message, top_k?, with_context? }` を受け取り、Embedding → Vector検索 → LLM応答の最小実装を確認。
  - `with_context=false` 時は `context` を省略。Embedding/Upstash未設定時はフォールバックで継続。

- OpenAIでの応答生成を追加
  - 変更ファイル: `backend/app/services/llm_service.py`
  - `BACKEND_OPENAI_API_KEY` がある場合は OpenAI Chat Completions（既定: `gpt-4o-mini`）を使用。未設定/テスト時は従来のスタブ回答へフォールバック。
  - 調整用ENV: `BACKEND_OPENAI_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`

- Upstash Vector検索の最小実装確認
  - `backend/app/services/vector_service.py`：`UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN` で `Index.query` を実行。
  - 未設定や失敗時はダミータイトルでフォールバック。`UPSTASH_VECTOR_NAMESPACE` があれば namespace クエリ。

- デプロイ資材整備
  - Dockerfile 確認: `backend/Dockerfile` は単段で `uvicorn` 実行、`/data` 同梱のMVP構成。
  - Cloud Run デプロイスクリプト: `scripts/deployment/deploy_cloud_run_mvp.sh`（実行権限付与済み）。
  - 環境変数雛形: `backend/.env.prod.example`（必須/推奨キー一式を含む）。
  - Firebase Hosting除外: `.firebaseignore` に `htmlcov/`, `logs/`, `backend/`, `scripts/` を追加済み。

- テスト実行
  - VS Code タスク「pytest backend」を実行し PASS（Smoke/フォールバック）を確認。

### 次アクション（Next）

1) Cloud Run 本番デプロイ
   - `backend/.env.prod.example` をコピーして `backend/.env.prod` を作成し値を設定。
     - 必須/推奨: `BACKEND_ENVIRONMENT=production`, `BACKEND_LOG_LEVEL=INFO`, `UPSTASH_VECTOR_REST_URL`, `UPSTASH_VECTOR_REST_TOKEN`
     - 任意: `BACKEND_OPENAI_API_KEY`（未設定でもスタブ動作）
   - `scripts/deployment/deploy_cloud_run_mvp.sh` を用いてビルド/プッシュ/デプロイ（`PROJECT_ID`, `REGION`, `SERVICE`, `ENV_FILE` を指定）。
   - デプロイ後、`/health` と `/chat`（`with_context` true/false）を確認。

2) Upstash へのデータ投入
   - `scripts/data-processing/` の投入スクリプトを使い、namespace なしでインデックスに投入（MVP方針）。
   - `/chat` の `retrieved_titles` に反映されることを確認。

3) ドキュメント最小整備
   - `README.md`、`docs/deployment/cloud_run_firebase_mvp.md`、`docs/project/env_mvp.md` に、今回のENV・手順を反映。

4) Firebase Hosting（フロント）
   - `NEXT_PUBLIC_MVP_MODE=true` でビルド/デプロイし、公開URLでチャットが `/chat` を叩いて応答することを確認。

### 動作確認の要点

- Health: GET `/health` が 200
- Chat: POST `/chat` に `{ "message": "おすすめの低コストカードは？" }` を送って 200 と最小レスポンス
- `with_context=false` でも 200 で `context` 非表示

### 品質ゲート結果（本日時点）

- Build: N/A（Docker本番ビルドはデプロイ時に実行）
- Lint/Typecheck: PASS（変更ファイルに静的エラーなし）
- Tests: PASS（VS Codeタスク「pytest backend」成功）

---

## ▶️ 直近の実行タスク（2025-10-18）

MVP 公開に向けて、今日これから着手すべき具体タスクです。上から順に実行すると早く価値が出ます（Cloud Run 公開 → データ投入 → Hosting 公開 → 動作確認）。

1) 本番用環境ファイルを用意（必須）
  - 目的: Cloud Run で必要な環境変数を一括管理
  - 手順:
    - `backend/.env.prod` を作成（存在しない場合は新規に作成）
    - 設定例:
     - `BACKEND_ENVIRONMENT=production`
     - `BACKEND_LOG_LEVEL=INFO`
     - `UPSTASH_VECTOR_REST_URL=...`
     - `UPSTASH_VECTOR_REST_TOKEN=...`
     - （任意）`BACKEND_OPENAI_API_KEY=sk-...`
     - （必要なら）`UPSTASH_VECTOR_NAMESPACE=mvp_cards`
  - 判定: 机上レビューでキー漏れがないこと

2) Cloud Run へバックエンドをデプロイ（必須）
  - 目的: `/chat` を公開環境で動かす
  - コマンド（例）:
    - `PROJECT_ID=<gcp-project>` `REGION=asia-northeast1` `SERVICE=gamechat-ai-backend` `ENV_FILE=backend/.env.prod` を設定し、`scripts/deployment/deploy_cloud_run_mvp.sh` を実行
  - 判定: `gcloud run services describe ...` で URL が取得でき、`GET /health` が 200

3) Upstash へカードデータ投入（推奨）
  - 目的: ベクトル検索で実データを返せるようにする
  - コマンド（例）:
    - `python scripts/data-processing/upstash_upsert_mvp.py --source data/convert_data.json`
    - namespace を使う場合は `UPSTASH_VECTOR_NAMESPACE=mvp_cards` を Cloud Run 環境変数に設定
  - 判定: インデックス件数が増加し、後述の `/chat` で `retrieved_titles` が期待通り返る

4) Firebase Hosting へフロントを公開（推奨）
  - 目的: 公開URLからチャットを操作可能にする
  - コマンド（例）:
    - `PROJECT_ID=<firebase-project>` を指定して `scripts/deployment/deploy_firebase_hosting_mvp.sh` を実行
  - 判定: 公開URLでトップが表示でき、チャットが `/chat` を叩いて応答する

5) 公開後のスモークテスト（必須）
  - 目的: 本番ルートでの最小確認
  - 観点:
    - Cloud Run: `GET /health` が 200
    - Cloud Run: `POST /chat` に `{ "message": "テスト", "with_context": true }` で 200 と最小レスポンス（`answer`, `retrieved_titles`, `context`）
    - `with_context=false` でも 200 で `context` が省略される

6) 環境変数命名の整合を修正（小タスク）
  - 目的: ドキュメントと実装の表記揺れを排除
  - 施策: `docs/project/env_mvp.md` を `BACKEND_ENVIRONMENT`/`BACKEND_LOG_LEVEL` 基準に統一し、`BACKEND_ENV`/`LOG_LEVEL` は互換注記を残す

7) CORS/Rewrite の最終確認（小タスク）
  - 目的: ブラウザからのアクセスでブロックされないようにする
  - 観点:
    - Firebase `firebase.json` の rewrites は `/chat` `/api/**` が Cloud Run 指定済み（現状OK）
    - FastAPI 側 `CORS_ORIGINS` が本番ドメインに合っているか（運用開始時は `[*]` でも可、後日絞り込み）

8) （任意）CI/CD の準備
  - 目的: 手動手順の省力化
  - 概要: GitHub Actions で Cloud Run / Firebase Hosting を自動デプロイ
  - 秘密情報: `GCP_SA_KEY`, `FIREBASE_TOKEN` など

補足:
- 進行順は 1→2→3→4→5 を推奨（先に Cloud Run を公開し、検索品質は投入進捗に応じて改善）
- それぞれの詳細手順は本ファイルおよび `docs/deployment/cloud_run_firebase_mvp.md` を参照
