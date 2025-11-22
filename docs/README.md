# GameChat AI ドキュメント (MVPインデックス)

**最終更新**: 2025年10月10日

MVPで必要なのはごく少数のドキュメントです。その他の資料は `ARCHIVE_CANDIDATE` の注記付きで参考情報として残しています。

---

## ✅ MVP必読ドキュメント

| 用途 | ドキュメント |
|------|--------------|
| 全体タスクとDoD | [`project/release_mvp.md`](./project/release_mvp.md) |
| 最小構成の手順まとめ | [`deployment/deployment-guide.md`](./deployment/deployment-guide.md) |
| Cloud Run + Firebase 詳細手順 | [`deployment/cloud_run_firebase_mvp.md`](./deployment/cloud_run_firebase_mvp.md) |
| 環境変数一覧 | [`project/env_mvp.md`](./project/env_mvp.md) |
| API仕様 (POST `/chat`) | [`api/api-specification.md`](./api/api-specification.md) |

補助ドキュメント:
- Firebase Hosting 用 rewrite はリポジトリ直下の `firebase.json` を参照
- スクリプト: `scripts/deployment/deploy_cloud_run_mvp.sh`, `scripts/deployment/deploy_firebase_hosting_mvp.sh`, `scripts/data-processing/upstash_upsert_mvp.py`

---

## � ARCHIVE_CANDIDATE 一覧

以下の資料はフル機能版や将来の改善を記録したものです。MVPでは読まなくても動作に影響しません。

| ディレクトリ/ファイル | 備考 |
|------------------------|------|
| `deployment/cloud-services-overview.md` | GCP全体設計メモ |
| `deployment/docker-usage.md` | Docker Compose 拡張構成 |
| `deployment/environment-setup.md` | 包括的な環境変数管理ガイド |
| `deployment/implementation-reports.md` | APIキー認証・Sentry などの実装レポート |
| `deployment/release-checklist.md` | フルリリース向けチェックリスト |
| `project/project-status.md` | 旧来のロードマップ・KPI |
| `guides/` 配下各種 | ハイブリッド検索 / LLM最適化 / 依存管理ガイドなど |
| `features/chat-history-management.md` | チャット履歴機能の仕様書 |
| `issues/` 配下各種 | 非MVP機能の課題・改善提案 |
| `performance/performance-frontend-optimization.md` | 最適化レポート |
| `security/` 配下各種 | 本番向けセキュリティ監査レポート |
| `testing/testing-e2e-issues.md` | E2Eテスト改善メモ |

`ARCHIVE_CANDIDATE` の注記が付いているファイルは、将来的に `docs/archive/` へ移動予定です。

---

## 🔎 よく使うリンク

- [リポジトリ README](../README.md) : MVPの使い方とローカル起動手順
- [Firebase Hosting 設定](../firebase.json)
- [Cloud Build (MVP)](../cloudbuild.yaml)
- [データ変換ファイル](../data/convert_data.json)

---

## � 更新ポリシー

- MVPで追加の情報が必要になった場合は `project/release_mvp.md` に追記し、本インデックスからリンクします。
- ARCHIVE_CANDIDATE 資料は過去の知見を保持する目的で残しています。参照しても構いませんが、MVP作業の妨げにならないよう注意してください。

MVPタスクの進捗は常に `project/release_mvp.md` を起点に確認してください。
