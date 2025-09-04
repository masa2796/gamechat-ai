# 📦 Release MVP 開発タスク整理

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

## ✅ タスク一覧（How）

### フロントエンド

* [x] 入力欄＋送信ボタン＋チャット形式で応答を表示するコンポーネントを作成 (既存 `assistant` ページ流用)
* [ ] 最低限のデザイン適用（モバイルで読めるレベル）
* [ ] Firebase Hosting 用の設定追加 & デプロイ
  * 環境変数: `NEXT_PUBLIC_MVP_MODE=true` で `/chat` エンドポイントを利用

### バックエンド

* [x] `/chat` API を既存 `rag.py` 内に単純実装（専用MVPファイル廃止）
* [△] OpenAI API 呼び出し処理を実装（Embedding利用 / 回答はスタブLLM。後で本番LLM差し替え）
* [x] Upstash Vector に問い合わせる処理を実装（`VectorService` 利用。未設定時は空結果フォールバック）
* [x] 検索結果をプロンプトに組み込み回答を生成（簡易: context抽出 & スタブLLM入力）
* [ ] Cloud Run へデプロイ（未実施）

### データ

* [ ] ベクトル化済みカードデータをUpstashに格納（現状: タイトルで検索しローカル/Cloudの JSON から最小抽出）
* [x] 必要最低限の情報のみ残す（`mvp_chat` は title / effect_1 / 基本ステータスのみ返却）

---

## 🔄 追加メモ (MVP進捗)

* 既存 `rag.py` の `/chat` をシンプル実装へ置換（認証 / reCAPTCHA / ハイブリッド検索除外）
* フロントは `NEXT_PUBLIC_MVP_MODE=true` で `/api/rag/query` から `/chat` へ切替
* 失敗時も UX を保つフォールバック（擬似埋め込み / 汎用回答）
* 今後: Cloud Run デプロイ手順 / Firebase Hosting 設定追記 / モバイル向けスタイル微調整

---

## 🚫 除外範囲（Will Not Do）

* 挨拶検出・早期応答システム
* ハイブリッド検索（BM25 + ベクトル検索）
* 複合条件検索 / 戦略的推薦機能
* 検索モード自動選択（FILTERABLE / SEMANTIC / HYBRID）
* カード詳細ページ (`/cards/{card_id}/details`)
* 高度なエラーハンドリング・動的閾値調整
* 包括的テスト（Smoke Test のみ残す）
* モニタリング機能（Sentry, Prometheusなど）

---

## 🚀 リリース後の流れ

1. MVPをユーザーに触ってもらう
2. フィードバック収集
3. 優先度が高い機能から追加していく

---

## 🗑️ MVP向け削除実施リスト（2025-09-05）

MVPで不要と判断した機能/ファイルをこのブランチ（`release-mvp-120`）では削除。将来拡張時は Git 履歴から復元。

### 削除理由カテゴリ
- Hybrid検索 / 複合戦略: MVPはベクトル単独
- クエリ分類 / 挨拶検出: `/chat` は一律ベクトル検索
- 高度RAG統合 / 詳細取得: シンプル回答生成のみ
- モニタリング / パフォーマンス最適化: 初期リリースでは後回し
- 大量テスト: Smokeレベルへ縮小

### 削除(物理削除)ファイル初回バッチ
1. ルーター重複: `backend/app/routers/mvp_chat.py`
2. 検索高度化:
  - `backend/app/services/hybrid_search_service.py`
  - `backend/app/services/classification_service.py`
  - `backend/app/services/rag_service.py`
  - `backend/app/models/classification_models.py`
3. テスト: ハイブリッド / 分類 / RAG 関連
  - `backend/app/tests/services/test_hybrid_search_consolidated.py`
  - `backend/app/tests/services/test_classification_consolidated.py`
  - `backend/app/tests/services/test_classification_aggregation.py`
  - これらに依存する性能/統合系テスト（後続で段階的に削除予定）
4. スクリプト: 挨拶検出など
  - `scripts/testing/test_greeting_detection.py`
5. モニタリング/監視
  - `monitoring/` ディレクトリ一式
  - `docker-compose.monitoring.yml`
6. ドキュメント（後続コミットで整理）
  - `docs/guides/search-hybrid-guide.md`
  - `docs/guides/search_result_detail_refactor.md` (ハイブリッド節削除 or 丸ごと)
  - `docs/guides/search-vector-optimization.md` 中の hybrid 設定
  - `docs/sphinx_docs/services/hybrid_search_service.rst`
  - `docs/sphinx_docs/services/classification_service.rst`
  - `README.md` / `docs/README.md` 内 HYBRID/分類セクション圧縮

### 残すもの
- `/chat` のみ提供する最小 FastAPI (`backend/app/routers/rag.py`)
- `EmbeddingService`, `VectorService`, `LLMService`, `StorageService`
- ベクトル検索の最小検証テスト（未整備なら後で追加）

### 今後の追加メモ
- 追加で失敗する import（`conftest.py` など）から分類/ハイブリッド参照を除去予定
- README 短縮版作成 & 旧高度設計は `docs/archive/` へ移設検討

---
