# GameChat AI - ドキュメント

### 🚀 [`deployment/`](./deployment/) - デプロイメント・インフラ
**すぐに使える実践的なデプロイガイド**
- [**デプロイガイド**](./deployment/deployment-guide.md) - 1分でデプロイ、本番環境設定
- [**🌟 クラウドサービス全体ガイド**](./deployment/cloud-services-overview.md) - GCP・Firebaseの包括的利用ガイド
- [**OpenAI設定**](./deployment/cloud-run-openai-setup.md) - APIキー・Secret Manager設定
- [**認証レポート**](./deployment/api-key-authentication-implementation-report.md) - セキュリティ実装詳細クトリには、GameChat AIプロジェクトの各種ドキュメントが整理されています。

## 🎯 クイックスタート

### すぐに始めたい方
1. **[プロジェクト状況・計画](./project-status.md)** で現在の状況を確認
2. **[デプロイガイド](./deployment/deployment-guide.md)** でサービスをデプロイ
3. **[API仕様書](./api/rag_api_spec.md)** でAPIの使い方を学習

### 開発に参加したい方
1. **[実装ガイド](./guides/)** で技術詳細を理解
2. **[ユーティリティスクリプト](./scripts/)** で開発ツールを活用
3. **[パフォーマンス結果](./performance/)** で現在の性能を把握

## 📁 ディレクトリ構成

### � [`project-status.md`](./project-status.md) - プロジェクト状況・計画
**システムの現在の状況と今後の開発計画**
- 現在の問題点と解決状況
- 緊急・短期・中期の開発計画  
- パフォーマンス目標と技術的改善項目

### �🚀 [`deployment/`](./deployment/) - デプロイメント・インフラ
**すぐに使える実践的なデプロイガイド**
- [**デプロイガイド**](./deployment/deployment-guide.md) - 1分でデプロイ、本番環境設定
- [**OpenAI設定**](./deployment/cloud-run-openai-setup.md) - APIキー・Secret Manager設定
- [**認証レポート**](./deployment/api-key-authentication-implementation-report.md) - セキュリティ実装詳細

### 🛠️ [`guides/`](./guides/) - 実装・最適化ガイド
**技術実装の詳細な手順書**
- [**ハイブリッド検索**](./guides/hybrid_search_guide.md) - 検索システム実装ガイド
- [**LLM応答最適化**](./guides/llm_response_enhancement.md) - 87%応答時間短縮の実装
- [**ベクトル検索最適化**](./guides/vector_search_optimization_guide.md) - 検索精度向上手法

### 📊 [`api/`](./api/) - API仕様書
**開発者向けAPI詳細仕様**
- [**RAG API仕様**](./api/rag_api_spec.md) - エンドポイント、認証、エラーハンドリング

### 📈 [`performance/`](./performance/) - パフォーマンス・メトリクス
**システム性能の測定結果と最適化データ**

### 🔧 [`../scripts/`](../scripts/) - スクリプト・ツール
**開発・運用・デプロイで使用するスクリプト集**
- **データ処理**: データ変換・埋め込み生成・DBアップロード
- **テスト・検証**: 機能テスト・パフォーマンス測定・品質保証
- **デプロイメント**: 本番・開発環境への自動デプロイ
- **ユーティリティ**: 環境セットアップ・設定診断・セキュリティチェック

### 📖 [`sphinx/`](./sphinx/) - 技術ドキュメント自動生成
**API仕様の自動生成システム**

## 🎯 用途別ガイド

### 🚀 すぐにデプロイしたい
1. [`project-status.md`](./project-status.md) で現在の状況を確認
2. [`deployment/deployment-guide.md`](./deployment/deployment-guide.md) の「1分でデプロイ」を実行
3. 問題が発生した場合は同ドキュメントの「トラブルシューティング」を参照

### 🌐 クラウドサービスを理解したい
1. [`deployment/cloud-services-overview.md`](./deployment/cloud-services-overview.md) でアーキテクチャ全체を把握
2. 使用サービス（Cloud Run、Firebase、Secret Manager等）の詳細を確認
3. 運用・管理、費用管理の手順を学習

### 🔍 検索システムを理解したい
1. [`guides/hybrid_search_guide.md`](./guides/hybrid_search_guide.md) でシステム全体を把握
2. [`guides/vector_search_optimization_guide.md`](./guides/vector_search_optimization_guide.md) で最適化を学習

### 🤖 AI応答を最適化したい
1. [`guides/llm_response_enhancement.md`](./guides/llm_response_enhancement.md) で応答戦略を理解
2. [`performance/`](./performance/) でパフォーマンス改善の実装方法を学習

### 📊 API仕様を確認したい
1. [`api/rag_api_spec.md`](./api/rag_api_spec.md) で詳細仕様を確認
2. 認証・エラーハンドリングを実装

### 🛠️ 開発に参加したい
1. [`project-status.md`](./project-status.md) で今後の計画を確認
2. [`guides/`](./guides/) で技術実装の詳細を学習
3. [`scripts/`](./scripts/) で開発ツールを活用

## 📞 サポート

- **技術的な問題**: 各ガイドの「トラブルシューティング」セクションを確認
- **デプロイ問題**: [`deployment/`](./deployment/) のドキュメントを参照
- **パフォーマンス課題**: [`performance/`](./performance/) のメトリクスを確認

---
**最終更新**: 2025年6月17日
