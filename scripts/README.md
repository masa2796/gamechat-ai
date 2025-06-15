# Scripts Directory

このディレクトリには、GameChat AIプロジェクトの開発・運用・デプロイに使用するスクリプトが含まれています。

## 📁 スクリプト一覧

### 🚀 セットアップ・デプロイ

- **`dev-setup.sh`** - 開発環境のセットアップスクリプト
- **`prod-deploy.sh`** - 本番環境デプロイスクリプト
- **`production-deploy.sh`** - 本番環境デプロイ（詳細版）

### 🔍 テスト・検証

- **`test-pipeline.sh`** - CI/CDパイプライン用テストスクリプト
- **`test-pipeline-local.sh`** - ローカル環境でのパイプライン検証スクリプト
- **`lighthouse-audit.sh`** - Lighthouseパフォーマンス監査スクリプト

### 🔒 セキュリティ

- **`security-check.sh`** - セキュリティチェックスクリプト
- **`check-env-security.sh`** - 環境変数ファイルのセキュリティ検証
- **`verify-api-keys.sh`** - APIキー設定の検証

### 🛠️ ユーティリティ

- **`diagnose-config.py`** - 設定診断スクリプト
- **`diagnose_config.py`** - 設定診断スクリプト（代替版）

## 🎯 使用方法

### ローカル開発環境のセットアップ
```bash
./scripts/dev-setup.sh
```

### パイプラインのローカル検証
```bash
./scripts/test-pipeline-local.sh
```

### 環境変数のセキュリティチェック
```bash
./scripts/check-env-security.sh
```

### 本番環境へのデプロイ
```bash
./scripts/prod-deploy.sh
```

## 📋 注意事項

- 実行前にスクリプトに実行権限があることを確認してください（`chmod +x scriptname.sh`）
- 本番環境関連のスクリプトは慎重に実行してください
- 環境変数が適切に設定されていることを確認してください

## 📚 関連ドキュメント

- [デプロイメントガイド](../docs/deployment/)
- [開発環境セットアップ](../docs/guides/environment-setup.md)
- [パイプライン検証レポート](../docs/deployment/pipeline-verification-report.md)
