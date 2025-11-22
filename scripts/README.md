# Scripts Directory

GameChat AIプロジェクトの開発・運用・デプロイに使用するスクリプト集です。カテゴリ別にサブディレクトリで整理されています。

## 📁 ディレクトリ構成

### � [`data-processing/`](./data-processing/) - データ処理
**ゲームデータの変換・埋め込み生成・DBアップロード**
- `convert_to_format.py` - データ形式変換
- `embedding.py` - 埋め込みベクトル生成
- `upstash_connection.py` - Vector DBアップロード

### 🧪 [`testing/`](./testing/) - テスト・検証
**システムの機能テスト・パフォーマンス測定・品質保証**
- `test_performance.py` - API応答時間測定
- `test-pipeline.sh` - CI/CDパイプラインテスト
- `test-pipeline-local.sh` - ローカルテスト
- `lighthouse-audit.sh` - フロントエンド監査

### 🚀 [`deployment/`](./deployment/) - デプロイメント
**本番・開発環境への自動デプロイ**
- `prod-deploy.sh` - 本番環境デプロイ
- `cloud-run-deploy.sh` - Google Cloud Runデプロイ
- `firebase-deploy.sh` - Firebase Hostingデプロイ
- `migrate-to-firebase.sh` - Firebase移行スクリプト

### �️ [`utilities/`](./utilities/) - ユーティリティ
**開発環境セットアップ・設定診断・セキュリティチェック**
- `dev-setup.sh` - 開発環境セットアップ
- `diagnose-config.py` - 設定診断ツール
- `check-env-security.sh` - 環境変数セキュリティチェック
- `security-check.sh` - システムセキュリティ監査
- `verify-api-keys.sh` - APIキー検証

## 🎯 クイックスタート

### 初回セットアップ
```bash
# 1. 開発環境セットアップ
./utilities/dev-setup.sh

# 2. 設定診断・確認
python utilities/diagnose-config.py

# 3. セキュリティチェック
./utilities/security-check.sh
```

### データ処理フロー
```bash
# 1. データ変換
python data-processing/convert_to_format.py

# 2. 埋め込み生成
python data-processing/embedding.py

# 3. Vector DBアップロード
python data-processing/upstash_connection.py
```

### テスト・検証
```bash
# ローカルテスト
./testing/test-pipeline-local.sh

# パフォーマンステスト
python testing/test_performance.py

# 機能テスト（該当なし）
```

### デプロイメント
```bash
# 本番環境デプロイ
./deployment/prod-deploy.sh

# Firebase Hosting
./deployment/firebase-deploy.sh
```

## 📋 使用時の注意事項

### 権限設定
```bash
# スクリプトに実行権限を付与
chmod +x utilities/*.sh deployment/*.sh testing/*.sh
```

### 環境変数
- `.env`ファイルが適切に設定されていることを確認
- APIキーやシークレットが正しく設定されているかチェック
- `utilities/diagnose-config.py`で診断実行

### セキュリティ
- 本番環境関連のスクリプトは慎重に実行
- `utilities/security-check.sh`で定期的にセキュリティチェック
- APIキーの漏洩防止に注意

## 📚 関連ドキュメント

- **[デプロイメントガイド](../docs/deployment/)** - デプロイメント詳細手順
- **[開発環境セットアップ](../docs/guides/)** - 開発環境構築ガイド
- **[パフォーマンス結果](../docs/performance/)** - テスト結果とメトリクス

---
**最終更新**: 2025年6月17日
