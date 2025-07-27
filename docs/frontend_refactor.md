## GameChat AI フロントエンド・リファクタリング進捗管理

### 概要
- コードの可読性・保守性・拡張性向上を目的としたリファクタリング・テスト拡充プロジェクト
- 主要UI（AssistantPage/ChatMessages/ChatInput）・ロジック（useChat等）の型安全化・責務分離・テスト網羅

---

### 進捗まとめ（2025/07/08時点）

- ✅ useChatカスタムフック実装・ロジック分離
- ✅ assistant.tsxはuseChatフック利用の形にリファクタ済み
- ✅ UI表示責務はChatMessages/ChatInput等に分割
- ✅ 型定義・strict化・any排除
- ✅ AssistantPage/ChatMessages/ChatInputのユニットテスト全観点網羅・通過
- ✅ テスト観点・カバレッジレポートに基づきprops/UI/異常系も型安全に検証
- ✅ useChatの異常系もErrorBoundaryでカバー
- ⬆ coverageレポートでカバレッジ0%の業務ロジック・UI部品を優先してテスト追加中
- ✅ src/hooks/use-pwa.tsのユニットテスト作成・React 19対応済み
  - @testing-library/reactのrenderHookを利用し、環境依存の仕様も考慮したテストを追加
- ✅ src/hooks/use-web-vitals.tsのテスト・環境分岐修正
- ✅ src/lib/firebase.tsのテスト・初期化/エラー/Analytics網羅
- ✅ src/lib/sentry.tsのテスト・全API/環境/モック網羅
- ✅ src/components/ui/input.tsxのテスト・全観点網羅
- ✅ src/components/error-boundary.tsxのテスト・全観点網羅
- ✅ src/components/app-sidebar.tsxのテスト・全観点網羅
- ⬆ Playwright等によるE2Eテスト拡充・主要ユーザーフロー自動化は進行中
- ⬆ 型定義共通化・型ガイドライン作成は一部進行中
- ⬆ CI/CDパイプラインでのカバレッジ閾値fail・自動化は一部進行中
- ⬆ yarn audit/npm auditの定期実行・未使用依存整理は一部進行中
- ⬆ テスト観点・運用ルール・開発フローのdocs/記載は一部進行中
- ⬆ Lighthouse等によるパフォーマンス・アクセシビリティ改善は一部進行中

---

### 優先タスク一覧（2025/07/08時点）

#### 【最優先】
1. カバレッジレポートの定期確認・未カバー領域の洗い出し
   - [ ] カバレッジ100%未満の箇所を抽出し、追加テストを検討【RELEASE_CHECKLIST.md:必須】
2. E2Eテスト・統合テストの拡充
   - [ ] Playwright等で主要ユーザーフローの自動化【RELEASE_CHECKLIST.md:必須】
   - [ ] エラー・例外・UI/UX観点のE2Eテスト追加【RELEASE_CHECKLIST.md:必須】
3. 型定義・型ガイドラインのドキュメント化
   - [ ] types.ts等の型定義共通化【RELEASE_CHECKLIST.md:必須】
   - [ ] 型ガイドライン・運用ルールの作成【RELEASE_CHECKLIST.md:必須】
4. CI/CDパイプラインでのテスト自動化・品質ゲート
   - [ ] PR時のテスト・カバレッジ・lint・型チェック自動化【RELEASE_CHECKLIST.md:必須】
   - [ ] カバレッジ閾値やlintエラーでfailする仕組み導入【RELEASE_CHECKLIST.md:必須】
5. 依存パッケージの棚卸し・セキュリティ監査
   - [ ] yarn audit/npm auditの定期実行と脆弱性対応【RELEASE_CHECKLIST.md:必須】
   - [ ] 未使用パッケージや重複依存の整理【RELEASE_CHECKLIST.md:必須】
6. ドキュメント・運用ルールの整備
   - [ ] テスト観点・運用ルール・開発フローをdocs/配下に記録【RELEASE_CHECKLIST.md:必須】
   - [ ] セットアップ手順やコントリビュートガイドの作成【RELEASE_CHECKLIST.md:必須】
7. パフォーマンス・アクセシビリティ改善
   - [ ] Lighthouse等で診断し、指摘事項を改善【RELEASE_CHECKLIST.md:リリース後可】

---

### 最低限やるべきリファクタリングタスク（2025/07/08追記）

1. 型定義共通化の最小雛形作成
   - [x] `src/types/`や`src/app/assistant/types.ts`等に共通型ファイルを作成し、主要な型（Message, Props等）を集約
   - [x] 既存の型定義を一部移動し、import経路を統一
   - [x] 型ガイドラインのドラフトを`docs/`配下に記載

2. CIでlint/型チェック/テストがfailする仕組みの導入（最低限）
   - [x] GitHub Actionsや`package.json`のscriptsで`eslint`・`tsc`・`jest/vitest`等を実行し、エラー時にCIをfailさせる
   - [x] PR時に必ずCIが走るように設定
   - [x] カバレッジ閾値や型エラーでfailする最低限のルールを導入

3. 依存整理のスクリプト実行・未使用パッケージの削除
   - [x] `yarn/npm dedupe`や`yarn/npm audit`を実行し、脆弱性・重複依存を検出
   - [x] `depcheck`等で未使用パッケージをリストアップし、`yarn remove`/`npm uninstall`で削除
   - [x] セキュリティ監査も最低限実施

4. docs/配下に現状の運用ルールのドラフト記載
   - [ ] `docs/guides/`や`docs/README.md`に「現状の運用ルール（例：ブランチ戦略・レビュー手順・テスト観点）」のドラフトをMarkdownで記載
   - [ ] 今後の運用改善のため、現状の課題や暫定ルールも明記

---

### 備考
- 進捗・優先度・必須/リリース後可の区分はRELEASE_CHECKLIST.mdと連携し、随時見直し
- 主要なタスクはRELEASE_CHECKLIST.mdの「フロントエンド」項目と完全に同期
- 完了済みタスクは[x]、進行中は⬆、未着手は[ ]で管理

---

### 参考：今後のアクション例
- strict化・型エラー修正
- 構成整理・スタイル共通化・依存整理
- 型定義の共通化・型ガイドライン作成
- E2Eテスト拡充
- coverage計測・不足箇所の洗い出し
- テスト観点・カバレッジ結果をdocs/testing/等に記録

---

### 優先的にテスト追加すべきファイル一覧（2025/07/06追記）
- [x] `src/hooks/use-pwa.ts`  
  - 理由: 100行あるが 0%
  - テストで確認すべき内容例: `beforeinstallprompt` のハンドリング、状態変化 (`isSupported`, `isInstalled`)
- [x] `src/hooks/use-web-vitals.ts`  
  - 理由: 同上
  - テストで確認すべき内容例: `getCLS`, `getLCP` の記録を `mock` してコール確認、副作用（console.log, fetch）もspyで検証済み
  - 修正完了: `import.meta.env.MODE`のNext.jsビルドエラーを修正し、環境判定ロジックを安全に実装済み
- [x] `src/lib/firebase.ts`  
  - 理由: 非同期通信
  - テストで確認すべき内容例: `getAnalytics()` などの初期化モック、呼び出し確認
  - 実装完了: Firebase設定・初期化・Analytics関連のテストを追加。環境変数による初期化制御、エラー処理、Analytics初期化の動作確認済み
- [x] `src/lib/sentry.ts`  
  - 理由: エラーログ
  - テストで確認すべき内容例: `init`, `captureException` の `spyOn` モック確認
  - 実装完了: 全21テストケース追加。APIエラー報告、ユーザーアクション記録、パフォーマンス測定、エラー監視、メトリクス記録の動作確認済み。環境分岐・サーバーサイド処理・モック検証も網羅
- [x] `src/components/ui/input.tsx`  
  - 理由: 状態変化
  - テストで確認すべき内容例: `onChange` や `value` の連携、ラベル描画確認など
  - 実装完了: 全37テストケース追加。基本描画、Props処理、スタイル適用、イベントハンドリング、input types、制御/非制御コンポーネント、アクセシビリティ、エッジケースを網羅
- [x] `src/components/error-boundary.tsx`  
  - 理由: Catch確認
  - テストで確認すべき内容例: 子がエラーを投げたとき、fallback UIに切り替わるか
  - 実装完了: 全24テストケース追加。エラーキャッチ、フォールバックUI表示、リセット機能、カスタムfallback、環境別エラー詳細表示、withErrorBoundary HOC、アクセシビリティ、各種エラータイプ（TypeError、null等）、ネスト・条件レンダリング等のエッジケースを網羅的にテスト
- [x] `src/components/app-sidebar.tsx`  
  - 理由: ロジック含む
  - テストで確認すべき内容例: 現在ページによる選択状態、ナビゲーション押下挙動
  - 実装完了: 全23テストケース追加。基本レンダリング、アイコン表示、リンク動作、メニューボタンサイズ、プロパティ伝播、アクセシビリティ、レスポンシブ対応、エラーハンドリング、コンポーネント統合、スタイリング、パフォーマンスを網羅的にテスト