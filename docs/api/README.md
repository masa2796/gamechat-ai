# API仕様書

このディレクトリには、GameChat AIのAPI仕様書とドキュメントが含まれています。

## � ドキュメント一覧

### [`rag_api_spec.md`](./rag_api_spec.md) 📋 **RAG API仕様**
**GameChat AI RAG APIの詳細仕様書**
- 🔌 **エンドポイント**: 利用可能なAPIエンドポイント一覧
- 🔐 **認証方式**: APIキー認証の実装方法
- 📝 **リクエスト・レスポンス**: 詳細なデータ形式
- ⚠️ **エラーハンドリング**: エラーコードと対応方法
- 🧪 **テスト方法**: APIのテスト・検証手順

## 🚀 クイックスタート

### 基本的なAPI呼び出し
```bash
curl -X POST "https://your-api-url/api/rag/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"question": "ポケモンについて教えて"}'
```

### 認証設定
- **APIキー**: `X-API-Key` ヘッダー（必須）
- **reCAPTCHA**: 本番環境では必須、開発環境では自動バイパス

## 🎯 使用方法

### API利用開始
1. [`rag_api_spec.md`](./rag_api_spec.md) でAPI仕様を確認
2. 認証設定（APIキー取得・設定）
3. テストリクエストの実行

### 開発統合
1. エンドポイント仕様の確認
2. SDKまたはHTTPクライアントでの実装
3. エラーハンドリングの実装
4. テスト・デバッグの実施

## 🔗 関連ドキュメント

- **デプロイ設定**: [`../deployment/api-key-authentication-implementation-report.md`](../deployment/api-key-authentication-implementation-report.md)
- **セキュリティ**: [`../security/`](../security/) - セキュリティ関連ドキュメント
- **実装ガイド**: [`../guides/`](../guides/) - 技術実装詳細

---
**最終更新**: 2025年6月24日
