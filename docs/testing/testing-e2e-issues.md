# E2Eテスト（Playwright）の現状と問題点

> **ARCHIVE_CANDIDATE**: E2Eテスト強化はMVP範囲外です。MVPではスモークテストのみ実施します。

## 概要
GameChat AIプロジェクトのE2Eテスト（`chat-functionality.spec.ts`）において、サイドバーのクリック操作で失敗が発生している問題について調査と修正を実施中。

## 問題の詳細

### 主要な問題
- **テスト失敗箇所**: `chat-functionality.spec.ts`のモバイルビューでのサイドバー操作
- **エラー内容**: `TimeoutError: locator.click: ... subtree intercepts pointer events`
- **発生環境**: Mobile Chrome (375x667 viewport)

### 根本原因
1. **アニメーション中のクリック妨害**: Radix UI Sheetコンポーネントのアニメーション実行中にポインターイベントが妨害される
2. **オーバーレイによるクリック阻害**: Sheet開閉時のオーバーレイ要素がクリックを阻止
3. **非同期アニメーションの待機不足**: `waitForTimeout`では確実な待機ができない

### 技術的詳細
- **UI実装**: Radix UI Dialogベースの`Sheet`コンポーネントを使用
- **アニメーション**: CSS Transition（300-500ms duration）
- **問題のセレクタ**: `[data-testid="sidebar-trigger"]`

## 実施した修正

### 1. テストコードの改善
- **ファイル**: `frontend/tests/e2e/chat-functionality.spec.ts`
- **修正内容**:
  - `force: true`オプションでクリック強制実行
  - `data-state`属性による確実なSheet状態確認
  - `waitForSelector`でアニメーション完了待機
  - テスト用`data-test-mode`属性の追加

### 2. UI側の改善
- **ファイル**: `frontend/src/components/ui/sidebar.tsx`
- **修正内容**:
  - SidebarTriggerに`pointerEvents: 'auto'`を明示的に設定

- **ファイル**: `frontend/src/components/ui/sheet.tsx`
- **修正内容**:
  - テスト時のアニメーション無効化クラスを追加

### 3. CSSアニメーション制御
- **ファイル**: `frontend/src/app/globals.css`
- **修正内容**:
  - `[data-test-mode="true"]`での高速アニメーション設定
  - `prefers-reduced-motion`対応

## 現在のテスト状況

### 修正前の問題
```
TimeoutError: locator.click: Timeout 15000ms exceeded.
=========================== logs ===========================
waiting for locator('[data-testid="sidebar-trigger"]').click()
  locator resolved to <button data-sidebar="trigger"…>
  attempting click action
  waiting for element to be visible, enabled and stable
  element is visible, enabled and stable
  scrolling into view if needed
  done scrolling
  <div class="fixed inset-0 z-50 bg-black/50" data-slot="sheet-overlay"…> from <div data-slot="sheet-portal"> subtree intercepts pointer events
```

### 修正後の現状（2025年6月24日現在）
複数の修正を実施したが、依然として全6テストが失敗している状況：

**実行結果**:
- **失敗数**: 6/6 テスト
- **主な問題**: Sheetが開かない（waitForSelectorタイムアウト）
- **環境**: Mobile Chrome (375x667)

**残存する課題**:
1. `waitForSelector('[data-state="open"]')` でタイムアウト
2. Sheetの開閉動作自体が機能していない可能性
3. テスト環境でのJavaScript実行に問題がある可能性

### 実装した修正効果
- アニメーション妨害の軽減（CSS制御）
- ポインターイベント明示化
- `force: true`でのクリック強制実行
- しかし、根本的なSheet開閉問題は未解決

## 未解決の課題

### 優先度高
1. **Sheet開閉機能の根本的問題**: モバイル環境でSheetが実際に開かない
2. **JavaScript実行環境**: テスト環境でのReact/UIライブラリの動作確認
3. **Radix UI互換性**: モバイルビューポートでのRadix UI Dialogの動作

### 優先度中
4. **クロスブラウザ対応**: Safari、Firefoxでの動作確認
5. **CI/CD環境**: GitHubActionsでの安定した実行
6. **待機条件の最適化**: より確実な非同期処理待機

### 優先度低
7. **パフォーマンス**: テスト実行時間の最適化
8. **レポート**: より詳細な失敗時情報の取得

## 次のステップ

### 緊急対応（短期）
1. **デスクトップ環境でのテスト確認**: モバイル特有の問題かを確認
2. **Sheet実装の詳細調査**: Radix UI DialogとSidebarの連携確認
3. **手動テスト**: ブラウザでの実際のUI動作確認
4. **ログ強化**: テスト実行時の詳細なデバッグ情報取得

### 根本解決（中期）
5. **UI実装の見直し**: モバイル対応の改善
6. **テスト戦略の再検討**: コンポーネント単体テストとの組み合わせ
7. **待機ロジックの改善**: より確実な非同期処理対応
8. **継続的監視**: テスト安定性の定期的なチェック

### 長期的改善
9. **テスト環境最適化**: CI/CDでの安定実行環境構築
10. **クロスブラウザ対応**: 全ブラウザでの動作保証

## ファイル構造

```
frontend/
├── tests/e2e/
│   ├── chat-functionality.spec.ts  # メインのE2Eテスト
│   └── global-setup.ts             # テスト環境設定
├── src/
│   ├── app/
│   │   ├── assistant.tsx           # SidebarTrigger実装
│   │   └── globals.css             # アニメーション制御CSS
│   └── components/ui/
│       ├── sidebar.tsx             # Sidebar関連コンポーネント
│       └── sheet.tsx               # Sheet (Modal) コンポーネント
├── playwright.config.ts            # Playwright設定
└── test-results/                   # テスト結果・レポート
```

## 関連するGitHubIssues

以下のissueを作成して追跡することを推奨：

### Issue 1: E2Eテストでのサイドバー操作失敗の修正
**タイトル**: `[Bug] E2E Test Failure: Sidebar click intercepted by overlay in mobile view`

**説明**:
```markdown
## 問題
Mobile Chrome環境でのE2Eテスト（`chat-functionality.spec.ts`）において、サイドバートリガーのクリックがオーバーレイによって妨害され、テストが失敗する。

## 環境
- ブラウザ: Mobile Chrome (375x667)
- テストファイル: `tests/e2e/chat-functionality.spec.ts`
- UI コンポーネント: Radix UI Sheet + Sidebar

## エラー内容
```
TimeoutError: locator.click: ... subtree intercepts pointer events
```

## 再現手順
1. `npx playwright test chat-functionality.spec.ts --project="Mobile Chrome"`
2. サイドバートリガーをクリックする処理で失敗

## 期待する動作
サイドバーが正常に開閉され、テストが成功する

## 修正案
- [ ] テスト時のアニメーション無効化
- [ ] 確実な状態待機の実装
- [ ] ポインターイベント制御の改善
```

**ラベル**: `bug`, `testing`, `e2e`, `ui`
**優先度**: `high`

### Issue 2: テスト安定性の向上
**タイトル**: `[Enhancement] Improve E2E test stability for UI animations`

**説明**:
```markdown
## 目的
アニメーション付きUI要素のE2Eテスト安定性を向上させる

## 提案
1. テスト環境でのアニメーション制御機能
2. より確実な要素状態確認
3. クロスブラウザでの動作保証

## 実装項目
- [ ] `data-test-mode`でのアニメーション制御
- [ ] Sheet/Modal状態の確実な検証
- [ ] 待機条件の最適化
- [ ] CI環境での安定性確認
```

**ラベル**: `enhancement`, `testing`, `ci-cd`
**優先度**: `medium`

---

# 付録: プロジェクト最終レポート・GitHub Issue案

## プロジェクト最終まとめ（2025年6月24日）
- 修正内容・成果・未解決課題・今後の推奨アクションは上記参照
- 詳細なファイル変更サマリー・教訓・知見・結論も含む

## GitHub Issue案（推奨）

### Issue 1: [E2E Bug] Sidebar Sheet fails to open in mobile viewport
- モバイル環境でのSheet開閉失敗・全テスト失敗
- 修正内容・残存課題・関連ファイルを明記

### Issue 2: [Enhancement] Improve E2E test stability for animated UI components
- テスト専用モード、待機ロジック、環境標準化、デバッグ強化

### Issue 3: [Investigation] Investigate Radix UI Sheet behavior in mobile viewport
- モバイルUIの手動・技術・比較調査、根本原因特定

---

（詳細は過去の`e2e-test-final-report.md`および`github-issues-proposal.md`を参照。今後は本ファイルのみを参照・更新してください）

**最終更新**: 2025年6月24日  
**担当者**: 開発チーム  
**ステータス**: 修正実装済み・検証待ち
