# テスト・検証スクリプト

システムの機能テスト、パフォーマンス測定、品質保証に使用するスクリプト集です。

## 🧪 スクリプト一覧

### [`test_greeting_detection.py`](./test_greeting_detection.py) - 挨拶検出テスト
**用途**: 挨拶検出機能の精度テスト
- 分類精度の検証
- 早期応答システムのテスト

```bash
python test_greeting_detection.py
```

### [`test_performance.py`](./test_performance.py) - パフォーマンステスト
**用途**: API応答時間の測定
- エンドツーエンドテスト
- レスポンス時間分析

```bash
python test_performance.py
```

### [`test-pipeline.sh`](./test-pipeline.sh) - CI/CDパイプラインテスト
**用途**: 本番環境でのパイプライン検証
- 自動テスト実行
- デプロイ前の品質チェック

```bash
./test-pipeline.sh
```

### [`test-pipeline-local.sh`](./test-pipeline-local.sh) - ローカルパイプラインテスト
**用途**: ローカル環境でのパイプライン検証
- 開発環境での事前テスト
- CI/CD前の動作確認

```bash
./test-pipeline-local.sh
```

### [`lighthouse-audit.sh`](./lighthouse-audit.sh) - パフォーマンス監査
**用途**: フロントエンドのパフォーマンス測定
- Lighthouseによる自動監査
- SEO・アクセシビリティチェック

```bash
./lighthouse-audit.sh
```

## 🎯 テスト戦略

### 機能テスト
1. **挨拶検出**: 分類精度90%以上を目標
2. **API応答**: 平均応答時間5秒以内

### パフォーマンステスト
1. **負荷テスト**: 同時接続数の限界測定
2. **フロントエンド**: Lighthouse スコア90以上

### 品質保証
1. **パイプライン**: 自動テストによる品質確保
2. **継続的監視**: 定期的なパフォーマンス測定

## 📊 テスト結果の活用

- パフォーマンスデータは `/docs/performance/` に保存
- 改善提案は GitHub Issues で管理
- CI/CD結果はデプロイ判断に使用

---
**最終更新**: 2025年6月17日
