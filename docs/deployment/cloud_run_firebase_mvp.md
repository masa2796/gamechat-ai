# 🚀 Cloud Run + Firebase Hosting (MVP) デプロイ手順

最終更新: 2025-09-28

本手順は MVP 向けの最小構成です。監視 / カナリア / CI/CD パイプラインは範囲外。

## 全体構成

```
[User Browser] --HTTPS--> [Firebase Hosting (Static)] --(rewrite /chat, /api/* )--> [Cloud Run Backend]
                                                      └--(Vector API)--> [Upstash Vector]
                                                      └--(OpenAI API)--> [OpenAI]
```

## 前提
- GCP プロジェクト作成済み & Cloud Run API 有効化
- Firebase プロジェクト作成済み (`firebase init hosting` 済み)
- ローカルで Python / Node.js / Docker / gcloud / firebase-tools が利用可能

## 1. バックエンド: Cloud Run デプロイ

1. 環境変数ファイル作成
```
cp backend/.env.prod.example backend/.env.prod
# 必要値を編集
```
2. デプロイ
```
bash scripts/deployment/deploy_cloud_run_mvp.sh \
  PROJECT_ID=<gcp-project> \
  SERVICE=gamechat-ai-backend \
  REGION=asia-northeast1 \
  ENV_FILE=backend/.env.prod
```
3. 動作確認
```
curl -s $(gcloud run services describe gamechat-ai-backend --region asia-northeast1 --format 'value(status.url)')/health
```
4. `/chat` API 確認 (フォールバック試験例)
```
SERVICE_URL=$(gcloud run services describe gamechat-ai-backend --region asia-northeast1 --format 'value(status.url)')
curl -s -X POST "$SERVICE_URL/chat" -H 'Content-Type: application/json' -d '{"message":"テスト","with_context":true}' | jq
```

## 2. ベクトルデータ投入 (必要時)
`UPSTASH_VECTOR_*` が設定されている前提で、将来 `scripts/data-processing/` に追加される投入スクリプトを実行。未投入でもダミータイトルでフォールバック動作可。

## 3. フロントエンド: Firebase Hosting デプロイ

1. ビルド & エクスポート
```
bash scripts/deployment/deploy_firebase_hosting_mvp.sh PROJECT_ID=<firebase-project>
```
2. 公開 URL 確認
```
firebase hosting:sites:list --project <firebase-project>
```
3. ブラウザでトップページ → チャット送信して `/chat` 応答が返ることを確認

## 4. Rewrites / CORS の考え方
- `firebase.json` で `/chat` と `/api/**` を Cloud Run へプロキシ
- バックエンド FastAPI 側 `CORS_ORIGINS` は MVP ではワイルドカード (`["*"]`) 運用、必要に応じて後日制限

## 5. トラブルシュート
| 症状 | チェック | 対処 |
|------|----------|------|
| 404 /chat | firebase rewrites 不足 | `firebase.json` に `/chat` run セクションがあるか確認後再デプロイ |
| 500 Embedding | OpenAIキーなし | `BACKEND_OPENAI_API_KEY` を設定 or フォールバック許容 |
| 検索結果が常にダミー | Upstash未設定 | `UPSTASH_VECTOR_REST_URL/TOKEN` を設定後再デプロイ |
| CORS ブロック | ブラウザ Network エラー | Cloud Run レスポンスヘッダー / firebase.json headers を確認 |

## 6. ロールバック (手動)
- Cloud Run: 過去リビジョンにトラフィック 100% 切り替え
```
gcloud run services update-traffic gamechat-ai-backend \
  --region asia-northeast1 \
  --to-revisions <REVISION>=100
```
- Firebase Hosting: Channels を利用し前バージョン活用 (`firebase hosting:channel:deploy <channel>`)

## 7. セキュリティ最小メモ
- 現状: 認証なし公開 API。悪用リスクが顕在化したら API Key / レート制限 / reCAPTCHA を拡張検討
- 早期観測指標案: 1分あたりリクエスト > 60 継続、もしくは vector zero_hit_rate > 50%

## 8. 次の改善候補
- CI/CD (GitHub Actions) で build & deploy 自動化
- Upstash 投入スクリプト & 差分同期
- 規模増時の autoscaling パラメータ調整 (`--min-instances` など)

---

MVP では「起動しユーザーが触れる」ことを最重視。複雑化は避け、安定性と簡素さを優先。必要になった時点で段階的に拡張してください。
