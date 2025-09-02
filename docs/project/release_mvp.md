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
