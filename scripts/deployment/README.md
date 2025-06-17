# デプロイメントスクリプト

本番環境・開発環境へのデプロイメントを自動化するスクリプト集です。

## 🚀 スクリプト一覧

### [`prod-deploy.sh`](./prod-deploy.sh) - 本番環境デプロイ
**用途**: 本番環境への自動デプロイ
- Docker Composeによる本番デプロイ
- ヘルスチェック・ロールバック機能付き

```bash
# 通常デプロイ
./prod-deploy.sh

# オプション付きデプロイ
./prod-deploy.sh --no-cache
./prod-deploy.sh --rollback
./prod-deploy.sh --health-check
```

### [`cloud-run-deploy.sh`](./cloud-run-deploy.sh) - Google Cloud Runデプロイ
**用途**: Google Cloud Runへのデプロイ
- コンテナビルド・デプロイの自動化
- 環境変数・シークレット設定

```bash
./cloud-run-deploy.sh
```

### [`firebase-deploy.sh`](./firebase-deploy.sh) - Firebase Hostingデプロイ
**用途**: フロントエンドのFirebase Hostingデプロイ
- Next.jsアプリケーションのビルド・デプロイ
- プレビュー・本番環境の選択

```bash
# 本番デプロイ
./firebase-deploy.sh

# プレビューデプロイ
./firebase-deploy.sh --preview
```

### [`migrate-to-firebase.sh`](./migrate-to-firebase.sh) - Firebase移行スクリプト
**用途**: 既存アプリケーションのFirebase移行
- 自動設定変更
- 段階的移行サポート

```bash
./migrate-to-firebase.sh
```

## 🔄 デプロイフロー

### 本番環境デプロイ
1. **事前チェック**: テストスクリプトで品質確認
2. **バックエンド**: `prod-deploy.sh`でCloud Runデプロイ
3. **フロントエンド**: `firebase-deploy.sh`でHostingデプロイ
4. **ヘルスチェック**: 動作確認とパフォーマンス測定

### 開発環境デプロイ
1. **ローカルテスト**: `../testing/test-pipeline-local.sh`
2. **プレビューデプロイ**: `firebase-deploy.sh --preview`
3. **動作確認**: 機能・パフォーマンステスト

## ⚠️ 重要な注意事項

### セキュリティ
- 本番環境のAPIキー・シークレットは適切に管理
- デプロイ前の環境変数チェック必須
- アクセス権限の確認

### 運用
- デプロイ時は事前にバックアップ取得
- ロールバック手順の確認
- モニタリングシステムでの監視継続

### トラブルシューティング
- デプロイ失敗時は`--rollback`オプションを使用
- ログの確認: Cloud Run、Firebase Hosting
- 緊急時の連絡体制を確認

---
**最終更新**: 2025年6月17日
