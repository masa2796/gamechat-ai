# ユーティリティスクリプト

開発環境のセットアップ、設定診断、セキュリティチェックに使用するユーティリティ集です。

## 🛠️ スクリプト一覧

### [`dev-setup.sh`](./dev-setup.sh) - 開発環境セットアップ
**用途**: 開発環境の初期セットアップ
- 依存関係のインストール
- 環境変数テンプレートの作成
- 必要なディレクトリ・ファイルの準備

```bash
./dev-setup.sh
```

### [`diagnose-config.py`](./diagnose-config.py) - 設定診断
**用途**: 環境変数・設定ファイルの診断
- APIキー設定の確認
- データベース接続テスト
- 設定不備の検出・修正方法提案

```bash
python diagnose-config.py
```

### [`check-env-security.sh`](./check-env-security.sh) - 環境変数セキュリティチェック
**用途**: 環境変数ファイルのセキュリティ検証
- .envファイルのパーミッション確認
- 機密情報の漏洩チェック
- セキュリティベストプラクティスの適用

```bash
./check-env-security.sh
```

### [`security-check.sh`](./security-check.sh) - システムセキュリティチェック
**用途**: アプリケーション全体のセキュリティ監査
- 依存関係の脆弱性スキャン
- 設定の安全性確認
- セキュリティポリシーの適用状況確認

```bash
./security-check.sh
```

### [`verify-api-keys.sh`](./verify-api-keys.sh) - APIキー検証
**用途**: 外部APIキーの有効性検証
- OpenAI API接続テスト
- Upstash Vector DB接続確認
- reCAPTCHA設定の検証

```bash
./verify-api-keys.sh
```

## 🎯 使用シーン

### 初回セットアップ
1. **開発環境構築**: `dev-setup.sh`で環境準備
2. **設定確認**: `diagnose-config.py`で設定診断
3. **セキュリティ**: `security-check.sh`で安全性確認

### 日常開発
1. **問題診断**: `diagnose-config.py`でトラブルシューティング
2. **API確認**: `verify-api-keys.sh`で外部サービステスト
3. **セキュリティ**: `check-env-security.sh`で定期チェック

### デプロイ前
1. **最終確認**: 全スクリプトで環境・設定・セキュリティの確認
2. **問題解決**: 検出された問題の修正
3. **本番準備**: セキュリティポリシーの適用

## 🔧 トラブルシューティング

### よくある問題
- **環境変数未設定**: `diagnose-config.py`で検出・修正方法確認
- **APIキー無効**: `verify-api-keys.sh`で有効性確認
- **権限問題**: `check-env-security.sh`でパーミッション確認

### 対処方法
- 各スクリプトが詳細なエラーメッセージと修正方法を提供
- ログファイルで詳細な診断情報を確認
- セットアップガイドで手順を再確認

---
**最終更新**: 2025年6月17日
