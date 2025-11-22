# GameChat AI - デプロイメントガイド (MVP)

**最終更新**: 2025年10月10日

MVPリリースに必要な最小限のセットアップとデプロイ手順をまとめています。詳細な背景は `docs/project/release_mvp.md` を参照してください。

---

## 🔁 全体フロー

1. バックエンドを Cloud Run にデプロイ
2. （任意）カードデータを Upstash Vector に投入
3. フロントエンドを Firebase Hosting に公開
4. `/chat` を叩いて動作確認

---

## ✅ 前提条件

- Google Cloud / Firebase プロジェクトが作成済み
- `gcloud`, `firebase-tools`, `docker`, `python3`, `node` が利用可能
- プロジェクトルートで以下が準備済み
  - `backend/.env.prod` (必要な環境変数を記入)
  - `frontend` の依存関係 (`npm install`) が導入済み

参考: 環境変数は `docs/project/env_mvp.md` を参照。

---

## 1. Cloud Run へデプロイ

1. 環境変数ファイルを整備
   ```bash
   cp backend/.env.prod.example backend/.env.prod
   # 必要な値を編集
   ```
2. デプロイスクリプトを実行
   ```bash
   PROJECT_ID=<gcp-project> \
   SERVICE=gamechat-ai-backend \
   REGION=asia-northeast1 \
   ENV_FILE=backend/.env.prod \
     bash scripts/deployment/deploy_cloud_run_mvp.sh
   ```
3. ヘルスチェック
   ```bash
   SERVICE_URL=$(gcloud run services describe gamechat-ai-backend --region asia-northeast1 --format 'value(status.url)')
   curl -s "$SERVICE_URL/health"
   ```

---

## 2. Upstash Vector にデータ投入（推奨）

上記 `.env.prod` で Upstash の URL/TOKEN を設定後に実行します。OpenAI キーがない場合でも擬似ベクトルで投入されます。

```bash
pip install -r backend/requirements.txt
python scripts/data-processing/upstash_upsert_mvp.py \
  --source data/convert_data.json \
  --namespace mvp_cards
```

コンソールに投入件数が表示されます。投入しない場合でも `/chat` はダミータイトルでフォールバックします。

---

## 3. Firebase Hosting へデプロイ

1. Firebase CLI にログインして対象プロジェクトを選択
   ```bash
   firebase login
   firebase use <firebase-project>
   ```
2. スクリプトでビルド & デプロイ
   ```bash
   PROJECT_ID=<firebase-project> \
     bash scripts/deployment/deploy_firebase_hosting_mvp.sh
   ```

スクリプト内で `NEXT_PUBLIC_MVP_MODE=true` が自動設定され、`frontend/out` の静的出力が Hosting にアップロードされます。

---

## 4. 動作確認

```bash
SERVICE_URL=$(gcloud run services describe gamechat-ai-backend --region asia-northeast1 --format 'value(status.url)')
curl -s -X POST "$SERVICE_URL/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"MVP動作確認です","with_context":true}' | jq
```

Firebase 側では公開URLをブラウザで開き、メッセージ送信→応答が返ることを確認します。

---

## 🧰 トラブルシュート

| 症状 | チェック | 対処 |
|------|----------|------|
| `/chat` が 500 を返す | Cloud Run ログ | Upstash/ OpenAI 未設定時はフォールバックするため、ログの WARN を確認 |
| `upstash_upsert_mvp.py` が失敗 | `.env.prod` の Upstash 設定 | URL/TOKEN が正しいか、`pip install upstash-vector` 済みか確認 |
| Firebase デプロイで `out` が無い | `frontend` ビルド結果 | `npm run mvp:build` が成功しているか、`NEXT_PUBLIC_MVP_MODE` が true か確認 |

---

## � 参考ドキュメント

- `docs/project/release_mvp.md` : 全体タスクとDoD
- `docs/project/env_mvp.md` : 環境変数一覧
- `docs/deployment/cloud_run_firebase_mvp.md` : 本ガイドの詳細版

MVPではシンプルな運用を重視し、追加機能は後続フェーズで段階的に導入します。
