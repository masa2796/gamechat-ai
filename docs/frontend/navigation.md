# GameChat AI ドキュメント ナビゲーション

**最終更新**: 2025年7月27日

このファイルは、docsディレクトリ内のドキュメントの整理後の構造と、どこに何が書かれているかの簡潔な案内です。

## 📑 すぐに見つけたい情報

### 🚨 緊急対応
- **システム障害**: [`deployment/deployment-guide.md`](./deployment/deployment-guide.md) → トラブルシューティング
- **セキュリティ問題**: [`security/security-comprehensive-report.md`](./security/security-comprehensive-report.md)
- **API エラー**: [`api/api-specification.md`](./api/api-specification.md) → エラーハンドリング

### 🚀 始めたい作業別

#### デプロイ・環境構築
- **すぐにデプロイしたい**: [`deployment/deployment-guide.md`](./deployment/deployment-guide.md)
- **Docker で開発**: [`deployment/docker-usage.md`](./deployment/docker-usage.md)
- **クラウド全体を理解**: [`deployment/cloud-services-overview.md`](./deployment/cloud-services-overview.md)
- **環境設定詳細**: [`deployment/environment-setup.md`](./deployment/environment-setup.md)
- **実装レポート確認**: [`deployment/implementation-reports.md`](./deployment/implementation-reports.md)

#### 開発・実装
- **API を使いたい**: [`api/api-specification.md`](./api/api-specification.md)
- **検索システムを理解**: [`guides/search-hybrid-guide.md`](./guides/search-hybrid-guide.md)
- **AI応答を最適化**: [`guides/llm-response-enhancement.md`](./guides/llm-response-enhancement.md)
- **依存関係を管理**: [`guides/dependencies.md`](./guides/dependencies.md)
- **開発ガイドライン**: [`guides/development-guidelines.md`](./guides/development-guidelines.md)

#### 監視・運用
- **現在の状況確認**: [`project-status.md`](./project-status.md)
- **パフォーマンス確認**: [`performance/performance_results.json`](./performance/performance_results.json)
- **セキュリティ確認**: [`security/security-comprehensive-report.md`](./security/security-comprehensive-report.md)

#### リリース・品質管理
- **リリース前チェック**: [`release-checklist.md`](./release-checklist.md)
- **テスト問題**: [`testing/testing-e2e-issues.md`](./testing/testing-e2e-issues.md)
- **運用ルール**: [`guides/operation-guideline-draft.md`](./guides/operation-guideline-draft.md)

## 📁 ディレクトリ別詳細

### [`deployment/`](./deployment/) - デプロイ・インフラ
- [`deployment-guide.md`](./deployment/deployment-guide.md) - **メインデプロイガイド**
- [`docker-usage.md`](./deployment/docker-usage.md) - Docker環境構築
- [`cloud-services-overview.md`](./deployment/cloud-services-overview.md) - クラウドアーキテクチャ全体
- [`environment-setup.md`](./deployment/environment-setup.md) - 環境変数・API設定統合ガイド
- [`implementation-reports.md`](./deployment/implementation-reports.md) - 実装レポート統合（APIキー認証・Sentry・Cloud Storage）

### [`guides/`](./guides/) - 実装ガイド・最適化
- [`search-hybrid-guide.md`](./guides/search-hybrid-guide.md) - **検索システム実装**
- [`llm-response-enhancement.md`](./guides/llm-response-enhancement.md) - AI応答最適化
- [`search-vector-optimization.md`](./guides/search-vector-optimization.md) - ベクトル検索最適化
- [`dependencies.md`](./guides/dependencies.md) - 依存関係管理
- [`development-guidelines.md`](./guides/development-guidelines.md) - 開発ガイドライン統合（雑談対応・型ガイドライン・セキュリティ）

### [`api/`](./api/) - API仕様・認証
- [`api-specification.md`](./api/api-specification.md) - **メインAPI仕様書**

### [`security/`](./security/) - セキュリティ
- [`security-comprehensive-report.md`](./security/security-comprehensive-report.md) - **包括的セキュリティ評価**
- [`firebase-security-audit-report.md`](./security/firebase-security-audit-report.md) - Firebase監査結果
- [`security-enhancement-implementation-report.md`](./security/security-enhancement-implementation-report.md) - セキュリティ強化詳細

### [`performance/`](./performance/) - パフォーマンス
- [`performance_results.json`](./performance/performance_results.json) - **メトリクス データ**
- [`frontend-optimization.md`](./performance/frontend-optimization.md) - フロントエンド最適化

### [`testing/`](./testing/) - テスト・品質
- [`testing-e2e-issues.md`](./testing/testing-e2e-issues.md) - E2Eテスト問題レポート

### [`sphinx/`](./sphinx/) - 自動生成ドキュメント
- API仕様の自動生成システム（`make html` で生成）