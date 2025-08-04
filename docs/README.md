# GameChat AI - ドキュメント

このディレクトリには、GameChat AIプロジェクトの各種ドキュメントが整理されています。

📖 **[ドキュメント ナビゲーション](./navigation.md)** - どこに何があるかの簡潔な案内

## 🎯 クイックスタート

### すぐに始めたい方
1. **[プロジェクト状況・計画](./project-status.md)** で現在の状況を確認
2. **[デプロイガイド](./deployment/deployment-guide.md)** でサービスをデプロイ
3. **[API仕様書](./api/api-specification.md)** でAPIの使い方を学習

### 開発に参加したい方
1. **[実装ガイド](./guides/)** で技術詳細を理解
2. **[ユーティリティスクリプト](../scripts/)** で開発ツールを活用
3. **[パフォーマンス結果](./performance/)** で現在の性能を把握

## 📁 ディレクトリ構成

### 📋 [`project-status.md`](./project-status.md) - プロジェクト状況・計画
**システムの現在の状況と今後の開発計画**
- 現在の問題点と解決状況
- 緊急・短期・中期の開発計画  
- パフォーマンス目標と技術的改善項目

### 🚀 [`deployment/`](./deployment/) - デプロイメント・インフラ
**すぐに使える実践的なデプロイガイド**
- [**デプロイガイド**](./deployment/deployment-guide.md) - 1分でデプロイ、本番環境設定
- [**🌟 クラウドサービス全体ガイド**](./deployment/cloud-services-overview.md) - GCP・Firebaseの包括的利用ガイド
- [**🐳 Docker利用ガイド**](./deployment/docker-usage.md) - Docker Composeによる環境別構築
- 2. [`deployment/environment-setup.md`](./deployment/environment-setup.md) で開発環境のセットアップ手順を確認
- [**📋 実装レポート統合**](./deployment/implementation-reports.md) - APIキー認証・Sentry・Cloud Storage実装

### 🛠️ [`guides/`](./guides/) - 実装・最適化ガイド
**技術実装の詳細な手順書**
- [**ハイブリッド検索**](./guides/search-hybrid-guide.md) - 検索システム実装ガイド
- [**LLM応答最適化**](./guides/llm-response-enhancement.md) - 87%応答時間短縮の実装
- [**ベクトル検索最適化**](./guides/search-vector-optimization.md) - 検索精度向上手法
- [**依存関係ガイド**](./guides/dependencies.md) - 依存関係と開発ガイド
- [**📝 開発ガイドライン**](./guides/development-guidelines.md) - 雑談対応・型ガイドライン・セキュリティ

### 📊 [`api/`](./api/) - API仕様書
**開発者向けAPI詳細仕様**
- [**RAG API仕様**](./api/api-specification.md) - エンドポイント、認証、エラーハンドリング

### 🔐 [`security/`](./security/) - セキュリティドキュメント
**システムセキュリティの包括的評価・管理**
- [**包括的セキュリティレポート**](./security/security-comprehensive-report.md) - 全体的なセキュリティ評価・改善計画
- [**Firebase セキュリティ監査**](./security/security-firebase-audit.md) - Firebase APIキー流出防止チェック
- [**セキュリティ強化実装レポート**](./security/security-enhancement-implementation-report.md) - セキュリティ強化実装詳細
- [**Firebase セキュリティ監査レポート**](./security/firebase-security-audit-report.md) - Firebase セキュリティ監査

### 🧪 [`testing/`](./testing/) - テスト・品質保証
**E2Eテスト、単体テスト、テスト自動化関連**
- [**E2Eテスト問題レポート**](./testing/testing-e2e-issues.md) - Playwright E2Eテストの現状と修正状況

### 📈 [`performance/`](./performance/) - パフォーマンス・メトリクス
**システム性能の測定結果と最適化データ**
- [**パフォーマンス結果データ**](./performance/performance_results.json) - システム性能メトリクス
- [**フロントエンド最適化**](./performance/performance-frontend-optimization.md) - フロントエンド性能改善

### 📖 [`sphinx/`](./sphinx/) - 技術ドキュメント自動生成
**API仕様の自動生成システム**
- 自動生成されるAPI仕様書とドキュメント
- `make html` でドキュメントを生成

## 🎯 用途別ガイド

### 🚀 すぐにデプロイしたい
1. [`project-status.md`](./project-status.md) で現在の状況を確認
2. [`deployment/deployment-guide.md`](./deployment/deployment-guide.md) の「1分でデプロイ」を実行
3. 問題が発生した場合は同ドキュメントの「トラブルシューティング」を参照

### 🌐 クラウドサービスを理解したい
1. [`deployment/cloud-services-overview.md`](./deployment/cloud-services-overview.md) でアーキテクチャ全体を把握
2. 使用サービス（Cloud Run、Firebase、Secret Manager等）の詳細を確認
3. 運用・管理、費用管理の手順を学習

### 🐳 Docker環境で開発したい
1. [`deployment/docker-usage.md`](./deployment/docker-usage.md) でDocker Composeファイルの使い分けを確認
2. 環境別（開発・本番・監視）の設定と起動コマンドを把握
3. トラブルシューティングで問題解決方法を学習

### 🔍 検索システムを理解したい
3. [`guides/search-hybrid-guide.md`](./guides/search-hybrid-guide.md) でハイブリッド検索の実装詳細を確認
2. [`guides/search-vector-optimization.md`](./guides/search-vector-optimization.md) で最適化を学習

### 🤖 AI応答を最適化したい
1. [`guides/llm-response-enhancement.md`](./guides/llm-response-enhancement.md) で応答戦略を理解
2. [`performance/`](./performance/) でパフォーマンス改善の実装方法を学習

### 📊 API仕様を確認したい
1. [`api/api-specification.md`](./api/api-specification.md) で詳細仕様を確認
2. 認証・エラーハンドリングを実装

### 🔐 セキュリティを確認したい
1. [`security/security-comprehensive-report.md`](./security/security-comprehensive-report.md) で全体的なセキュリティ状況を確認
2. [`security/security-firebase-audit.md`](./security/security-firebase-audit.md) で基本的な評価結果を確認
3. [`deployment/implementation-reports.md`](./deployment/implementation-reports.md) で認証実装詳細を確認

### 🧪 テスト品質を向上させたい
1. [`testing/testing-e2e-issues.md`](./testing/testing-e2e-issues.md) で現在のE2Eテスト問題を把握
2. Playwrightテストの実行とデバッグ手法を理解

### 🛠️ 開発に参加したい
1. [`project-status.md`](./project-status.md) で今後の計画を確認
2. [`guides/`](./guides/) で技術実装の詳細を学習  
3. [`../scripts/`](../scripts/) で開発ツールを活用
4. [`testing/`](./testing/) でテスト戦略を理解

## 📞 サポート

- **技術的な問題**: 各ガイドの「トラブルシューティング」セクションを確認
- **デプロイ問題**: [`deployment/`](./deployment/) のドキュメントを参照
- **パフォーマンス課題**: [`performance/`](./performance/) のメトリクスを確認

---
**最終更新**: 2025年7月27日
