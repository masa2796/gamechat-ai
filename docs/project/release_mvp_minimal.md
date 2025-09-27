# 🚀 Release MVP Minimal Guide

最終更新: 2025-09-27  (branch: `release-mvp-120`)
目的: 最小チャット体験を最速リリースし、実ユーザー行動と定性フィードバックを取得する。

---
## 1. Scope
In: シンプルチャットUI / POST /chat / Vector検索(任意) / Cloud Run / Firebase Hosting
Out: 認証 / ハイブリッド検索 / カード詳細画面 / 高度モニタリング / 包括テスト / 動的閾値調整

---
## 2. Single User Flow
1. ユーザーがフロントでメッセージ送信
2. サーバ：埋め込み生成 (未設定→擬似ベクトル)
3. Vector検索 (Upstash未設定→スキップ)
4. コンテキスト付きでLLM回答生成 (またはフォールバックメッセージ)
5. JSON応答返却

---
## 3. Public API (MVP)
POST /chat
Request: { "message": string }
Response: { "answer": string, "retrieved_titles": string[], "context"?: object[] }
内部固定値: top_k=5, with_context=true （外部パラメータ露出しない）
フォールバック方針: Upstash未設定→ retrieved_titles は空 or ダミー1件 / context 省略可

---
## 4. 外部依存 (最小)
必須: Cloud Run (Backend), Firebase Hosting (Frontend)
任意: Upstash Vector, OpenAI Embedding (無くても動作)
リスク: OpenAIレイテンシ / Upstash未設定時リコール低下

---
## 5. 環境変数 (最小)
Backend:
- BACKEND_OPENAI_API_KEY (任意)
- UPSTASH_VECTOR_REST_URL (任意)
- UPSTASH_VECTOR_REST_TOKEN (任意)
Frontend:
- NEXT_PUBLIC_API_URL (任意: 未設定なら相対パス `/chat` 試行)

削除/不採用: NEXT_PUBLIC_MVP_MODE フラグ（単一エンドポイントで簡素化）

---
## 6. Deploy (最短手順)
Backend:
1) Docker build & push
2) Cloud Run deploy --set-env-vars (上記任意含む)
3) ヘルス: POST /chat 200 確認
Frontend:
1) ビルド (環境変数設定)
2) Firebase deploy
Rollback: Cloud Run 旧Revisionへ切替 / Firebase 前回バージョン再デプロイ

---
## 7. Definition of Done
- 公開URLでチャット送信→回答表示 (モバイル視認性OK)
- Vector 有無いずれも 200 応答 + 意味のある `answer`
- README に API/Env/Deploy 最小情報が反映
- Smoke テスト 2ケース PASS (通常 / Vector無フォールバック)

---
## 8. Metric (単一)
Daily: /chat 200 成功リクエスト数 (初期閾値なし・単純計測)
将来: Retention/Zero-hit率/Latency は Post-MVP

---
## 9. セキュリティ注意
MVPは認証なし。公開後に異常トラフィック/コスト上昇検知したら APIキー付与 or Basic導入検討。

---
## 10. Post-MVP Backlog
GitHub Project (例): https://github.com/masa2796/gamechat-ai/projects
復活候補: ハイブリッド検索 / 詳細ページ / 動的閾値 / モニタリング

---
## 11. 簡易トラブル対応
- 5xx >5% / 1h: Cloud Run ログ調査
- 応答遅延 >8s 継続: OpenAI 有効/無効差分比較
- Zero-hit 目視多発: Upstash設定 / ベクトル投入漏れ確認

---
## 12. 保守方針
- 追加機能は `/chat` 改変より `/chat/v2` 新設を原則
- 古い高度機能文書は `docs/archive/` に段階移動

---
(End of Minimal Guide)
