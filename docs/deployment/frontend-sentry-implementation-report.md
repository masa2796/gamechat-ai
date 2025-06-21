# フロントエンドSentry統合実装レポート

## 📋 実装概要

フロントエンド（Next.js）にSentry統合を実装し、包括的なエラー監視とパフォーマンス追跡機能を追加しました。

## ✅ 実装済み機能

### 1. 基本設定ファイル
- `sentry.client.config.js` - クライアントサイドSentry設定
- `sentry.server.config.js` - サーバーサイドSentry設定  
- `sentry.edge.config.js` - Edge Runtime用Sentry設定
- `next.config.js` - Sentryプラグイン統合

### 2. エラー境界
- `global-error.tsx` - グローバルエラーハンドリング
- `sentry-provider.tsx` - Sentryプロバイダーコンポーネント

### 3. ユーティリティ関数
- `lib/sentry.ts` - Sentry操作用ヘルパー関数
  - `captureAPIError()` - API エラーの報告
  - `captureUserAction()` - ユーザーアクションの記録
  - `setSentryUser()` - ユーザー情報の設定
  - `setSentryTag()` - タグの設定
  - `setSentryContext()` - コンテキスト情報の設定
  - `startPerformanceTransaction()` - パフォーマンス測定

### 4. アプリケーション統合
- Assistantコンポーネントにエラー追跡機能を追加
- API呼び出し時のエラーハンドリング強化
- ユーザーアクションの自動追跡

## 🔧 設定項目

### 環境変数
```bash
# フロントエンド用
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ORG=your-org
SENTRY_PROJECT=your-project  
SENTRY_AUTH_TOKEN=your-token
```

### Sentry設定
- **トレース サンプリング率**: 100% （開発環境）
- **セッション リプレイ**: 10% のサンプリング
- **エラー時リプレイ**: 100%
- **プライバシー保護**: テキストとメディアをマスク

## 📊 監視機能

### 1. エラー監視
- JavaScript例外の自動キャッチ
- API エラーの詳細報告
- スタックトレース付きエラー詳細
- エラーコンテキスト情報（ユーザーメッセージ、エンドポイント等）

### 2. パフォーマンス監視
- ページロード時間
- API レスポンス時間
- ナビゲーション パフォーマンス
- Web Vitals メトリクス

### 3. ユーザーアクション追跡
- メッセージ送信イベント
- エラー発生時のユーザーコンテキスト
- ページ遷移の追跡

### 4. セッションリプレイ
- エラー発生時の画面操作再現
- プライバシー保護されたユーザーセッション記録

## 🚀 使用方法

### 基本的なエラー報告
```typescript
import { captureAPIError } from '@/lib/sentry';

try {
  // API呼び出し
} catch (error) {
  captureAPIError(error as Error, {
    endpoint: '/api/example',
    additionalContext: 'value'
  });
}
```

### ユーザーアクション追跡
```typescript
import { captureUserAction } from '@/lib/sentry';

captureUserAction('button_clicked', {
  buttonId: 'submit',
  formData: sanitizedData
});
```

### パフォーマンス測定
```typescript
import { startPerformanceTransaction } from '@/lib/sentry';

const transaction = await startPerformanceTransaction('api_call', 'http');
// 何かの処理
transaction?.finish();
```

## 🔒 セキュリティ考慮事項

1. **データマスキング**: ユーザー入力やメディアは自動的にマスクされます
2. **環境分離**: 開発/本番環境でそれぞれ異なるプロジェクトを使用
3. **PII保護**: 個人情報は追跡データから除外されます
4. **条件付き初期化**: DSNが設定されている場合のみSentryを有効化

## 📈 次のステップ

1. **カスタムダッシュボード作成**: プロジェクト固有のメトリクス監視
2. **アラート設定**: 重要なエラーの即座通知
3. **リリース追跡**: デプロイメントとエラーの関連付け
4. **ソースマップアップロード**: 本番環境でのより詳細なスタックトレース

## 📝 注意事項

- Sentry SDKは動的にインポートされるため、型エラーが発生する場合があります
- 本番環境では適切なサンプリング率を設定してコストを最適化してください
- 機密情報が含まれるエラーメッセージには注意が必要です

## 🔍 トラブルシューティング

### Sentryイベントが表示されない場合
1. DSNが正しく設定されているか確認
2. ネットワーク接続を確認
3. ブラウザの開発者ツールでSentryのリクエストを確認

### 型エラーが発生する場合
1. `@sentry/nextjs`パッケージの最新版を確認
2. TypeScript設定でSentryの型定義が含まれているか確認
3. 動的インポートを使用して型エラーを回避

この実装により、フロントエンドアプリケーションの包括的な監視とエラー追跡が可能になります。
