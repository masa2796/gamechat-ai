# API仕様書

GameChat AI APIの仕様書です。

## 📋 API仕様

### [`rag_api_spec.md`](./rag_api_spec.md) - RAG API仕様
**検索拡張生成APIの完全仕様**
- エンドポイント・認証・パラメータ定義
- エラーハンドリング・セキュリティ設定
- 実装例とテストケース

## � クイックスタート

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

## 📚 詳細情報
詳細な仕様は [`rag_api_spec.md`](./rag_api_spec.md) を参照してください。

---
**最終更新**: 2025年6月17日
