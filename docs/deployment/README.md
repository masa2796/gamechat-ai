# デプロイメント関連ドキュメント

このディレクトリには、GameChat AIのデプロイメント、インフラ設定、運用に関するドキュメントが含まれています。

## 📋 ドキュメント一覧

### [`deployment-guide.md`](./deployment-guide.md) ⭐ **メインガイド**
**包括的なデプロイメントガイド**
- 🚀 **1分でデプロイ**: クイックスタートコマンド
- 📱 **本番環境**: Google Cloud Run + Firebase Hosting
- 🛠️ **開発環境**: ローカル・Docker環境
- 🔍 **監視・トラブルシューティング**: ログ確認、エラー対応

### [`DOCKER_USAGE.md`](./DOCKER_USAGE.md) 🐳 **Docker ガイド**
**Docker Composeを使用した開発・本番環境構築**
- 📦 **設定ファイル**: docker-compose.yml, docker-compose.prod.yml等の使い分け
- 🔧 **環境別設定**: 開発、本番、監視システム
- 🚀 **ワンコマンド起動**: 用途別Docker起動コマンド集
- 🔍 **トラブルシューティング**: よくある問題と解決方法

### [`cloud-services-overview.md`](./cloud-services-overview.md) 🌟 **クラウドサービス全体ガイド**
**Google Cloud & Firebase サービス全体ガイド**
- 🏗️ **アーキテクチャ概要**: システム全体の構成図
- 📦 **使用サービス**: Cloud Run, Firebase, Secret Manager等
- 🔧 **運用・管理**: 監視、ログ確認、費用管理
- 🔒 **セキュリティ**: IAM設定、災害復旧

### [`cloud-run-openai-setup.md`](./cloud-run-openai-setup.md) ⚙️ **OpenAI設定**
**Google Cloud Run OpenAI API設定専用ガイド**
- Secret Manager設定
- APIキー管理
- 環境変数設定
- セキュリティ考慮事項

### [`api-key-authentication-implementation-report.md`](./api-key-authentication-implementation-report.md) 🔐 **認証実装**
**APIキー認証実装レポート**
- 認証システムの実装詳細
- 問題解決過程
- セキュリティ設定

### [`frontend-sentry-implementation-report.md`](./frontend-sentry-implementation-report.md) 📊 **Sentry監視**
**フロントエンドエラー監視実装レポート**
- Sentry設定の詳細
- エラー監視システム実装
- パフォーマンス監視

### [`cloud-storage-implementation-report.md`](./cloud-storage-implementation-report.md) 💾 **Cloud Storage**
**Cloud Storage実装レポート**
- ストレージ設定詳細
- ファイル管理システム
- セキュリティ設定

### その他のレポート・設定ガイド
- [`ci-build-fixes.md`](./ci-build-fixes.md) - CI/CDビルド修正
- [`cloud-storage-migration-guide.md`](./cloud-storage-migration-guide.md) - Storage移行ガイド
- [`firebase-api-key-regeneration-report.md`](./firebase-api-key-regeneration-report.md) - Firebase APIキー再生成
- [`sentry-production-alerts.md`](./sentry-production-alerts.md) - Sentry本番アラート設定
- [`README-cloud-storage.md`](./README-cloud-storage.md) - Cloud Storage詳細README

## 🎯 用途別ガイド

### 🆕 クラウドサービス全体理解
[`cloud-services-overview.md`](./cloud-services-overview.md) でアーキテクチャと使用サービス全体を把握

### 🐳 Docker環境構築
[`DOCKER_USAGE.md`](./DOCKER_USAGE.md) でDocker Composeの環境別設定と起動方法を把握

### 初回デプロイ
1. [`deployment-guide.md`](./deployment-guide.md) の「クイックスタート」を実行
2. 問題が発生した場合は「トラブルシューティング」セクションを参照

### クラウド運用・管理
[`cloud-services-overview.md`](./cloud-services-overview.md) の「運用・管理」「費用管理」セクションを参照

### OpenAI API設定のみ
[`cloud-run-openai-setup.md`](./cloud-run-openai-setup.md) を参照

### 認証システム詳細
[`api-key-authentication-implementation-report.md`](./api-key-authentication-implementation-report.md) を参照

## 🔧 よくある問題

### デプロイエラー
- **APIキー認証エラー**: Secret Managerの設定を確認
- **タイムアウト**: Cloud Runの設定とリソース制限を確認
- **reCAPTCHA認証エラー**: 環境変数の設定を確認

### パフォーマンス問題
- **応答時間遅延**: [`../performance/`](../performance/) のメトリクスを参照
- **メモリ不足**: Cloud Runのメモリ制限を調整

## 📞 サポート

問題が解決しない場合：
1. 各ガイドの「トラブルシューティング」セクションを確認
2. Cloud Runのログを確認: `gcloud logging read`
3. 開発チームに相談

---
**最終更新**: 2025年6月17日
