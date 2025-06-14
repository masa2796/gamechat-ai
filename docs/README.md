# GameChat AI - ドキュメント

このディレクトリには、GameChat AIプロジェクトの各種ドキュメントが整理されています。

## 📁 ディレクトリ構成

### [`api/`](./api/) - API仕様・設計ドキュメント
API設計、仕様書、インターフェース定義に関するドキュメント

- **[`rag_api_spec.md`](./api/rag_api_spec.md)** - RAG API仕様書
  - エンドポイント定義
  - リクエスト/レスポンス形式
  - バリデーション仕様
  - セキュリティ対策

### [`guides/`](./guides/) - 実装ガイド・チュートリアル
システムの実装方法、最適化手法、運用ガイドライン

- **[`hybrid_search_guide.md`](./guides/hybrid_search_guide.md)** - ハイブリッド検索システム実装ガイド
  - システムアーキテクチャ
  - 実装コンポーネント
  - API仕様とテスト方法

- **[`llm_response_enhancement.md`](./guides/llm_response_enhancement.md)** - LLM応答生成改修ドキュメント
  - 品質最適化戦略
  - パフォーマンス改善手法
  - 動的応答戦略

- **[`vector_search_optimization_guide.md`](./guides/vector_search_optimization_guide.md)** - ベクトル検索最適化ガイド
  - 検索精度向上手法
  - ネームスペース最適化
  - パフォーマンスチューニング

- **[`talk-guidelines.md`](./guides/talk-guidelines.md)** - 雑談対応ガイドライン
  - 雑談検出手法
  - 応答生成戦略
  - ユースケース例

- **[`assistant-ui-notes.md`](./guides/assistant-ui-notes.md)** - UIデザイン・実装メモ
  - インターフェース設計方針
  - ユーザビリティ考慮事項

### [`performance/`](./performance/) - パフォーマンス関連
システムパフォーマンス、ベンチマーク、最適化結果

- **[`performance_results.json`](./performance/performance_results.json)** - パフォーマンス測定結果
  - 応答時間データ
  - 検索精度メトリクス
  - システム最適化効果

### [`scripts/`](./scripts/) - ユーティリティスクリプト
データ処理、テスト、デバッグ用のスクリプト

- **[`convert_to_format.py`](./scripts/convert_to_format.py)** - データ形式変換スクリプト
- **[`embedding.py`](./scripts/embedding.py)** - 埋め込み生成スクリプト
- **[`upstash_connection.py`](./scripts/upstash_connection.py)** - Upstash Vector接続スクリプト
- **[`test_greeting_detection.py`](./scripts/test_greeting_detection.py)** - 挨拶検出テストスクリプト
- **[`test_performance.py`](./scripts/test_performance.py)** - パフォーマンステストスクリプト

### [`sphinx/`](./sphinx/) - Sphinxドキュメント生成
APIドキュメント自動生成システム

- **[`conf.py`](./sphinx/conf.py)** - Sphinx設定ファイル
- **[`index.rst`](./sphinx/index.rst)** - メインドキュメント
- **[`services/`](./sphinx/services/)** - サービス層APIドキュメント
- **[`Makefile`](./sphinx/Makefile)** - ビルド用Makefile

## 🚀 クイックスタート

### APIドキュメントの生成
```bash
cd sphinx/
make html
open _build/html/index.html
```

### ライブプレビュー（開発時）
```bash
cd sphinx/
make livehtml
```

## 📖 ドキュメント使用方法

### 開発者向け
1. **API設計時**: `api/`ディレクトリで仕様を確認
2. **実装時**: `guides/`ディレクトリで詳細な実装手法を参照
3. **最適化時**: `performance/`ディレクトリでベンチマーク結果を確認
4. **スクリプト実行時**: `scripts/`ディレクトリでユーティリティを活用

### 運用担当者向け
1. **システム理解**: `guides/hybrid_search_guide.md`でアーキテクチャを把握
2. **パフォーマンス監視**: `performance/`ディレクトリでメトリクスを確認
3. **トラブルシューティング**: 各ガイドのトラブルシューティングセクションを参照

## 🔄 ドキュメント更新ルール

1. **新機能追加時**: 対応するガイドドキュメントを更新
2. **API変更時**: `api/rag_api_spec.md`を必ず更新
3. **パフォーマンス改善時**: `performance/`ディレクトリに結果を記録
4. **docstring更新時**: `sphinx/`で自動生成ドキュメントを再生成

## 💡 参考リンク

- [プロジェクトメインREADME](../README.md)
- [フロントエンドディレクトリ](../frontend/)
- [バックエンドディレクトリ](../backend/)
- [データディレクトリ](../data/)
