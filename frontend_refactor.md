## フロントエンド・リファクタリング計画（GameChat AI）

### 進捗まとめ（2025/07/04時点）

- useChatカスタムフック実装・ロジック分離完了
- assistant.tsxはuseChatフック利用の形にリファクタ済み
- UI表示責務はChatMessages/ChatInput等に分割済み
- ドキュメント進捗も反映済み

---

### 1. 現状のコード構成（要点）

#### ディレクトリ構成

* `src/components/`：UI部品（`ui/`配下にButton, Input, Sidebar等のAtomic Design的な粒度の部品あり）
* `src/app/`：Next.jsのApp Router構成。layout.tsx, page.tsx, assistant.tsxなどページ・レイアウト単位で分割
* `src/hooks/`：カスタムフック（PWA, WebVitals, モバイル判定等）
* `src/lib/`：ユーティリティ・APIクライアント・外部連携（firebase, sentry, utils等）

#### 型安全性

* TypeScriptで実装されているが、tsconfig.jsonの`strict`がfalse（型安全性が甘い）

#### テスト

* `@testing-library/react`と`vitest`導入済み（`__tests__`配下にサンプルのみ）

#### エラーハンドリング・監視

* Sentry, ErrorBoundary, GlobalErrorHandlerなど堅牢な設計

#### PWA/パフォーマンス

* PWA対応、Web Vitals計測、Service Worker登録済み

---

### 2. 主な課題点

* **型安全性**

  * `strict: false` → 厳格な型定義が必要
  * `any`型や型推論任せの箇所が存在

* **コンポーネントの粒度と責務**

  * `assistant.tsx`などのページコンポーネントが肥大化
  * props型の明示と分離が必要

* **テスト**

  * 単体テストがサンプルレベルで主要機能が未テスト
  * E2Eテストが不足

* **ディレクトリ構成**

  * Atomic Designや機能単位（Feature-based）の構成整理が不十分

* **スタイルの統一性**

  * Tailwindクラスの一貫性に課題

* **依存パッケージ**

  * 未使用や古いパッケージが残っている可能性

---

### 3. リファクタリングの目的

> コードベース全体の可読性・保守性・拡張性を向上させ、将来の機能追加や不具合修正にかかる工数を削減する。

#### 観点別目的

* **型安全性**：バグの早期発見、補完性向上
* **責務分離**：UIの再利用性と見通しの良さを実現
* **テスト性**：品質と変更耐性の向上
* **構成明確化**：チーム内外でのスムーズな参照・修正
* **UI一貫性**：ユーザー体験と実装効率の向上
* **依存管理**：セキュリティとパフォーマンスの維持

---

### 4. 具体的なリファクタリング計画

#### 優先度：高

* tsconfig.jsonの`strict: true`化
* `any`削減と型定義の明示化
* `assistant.tsx`の分割と責務整理
* UI部品のprops型再設計
* ユニットテストとE2Eテストの拡充

#### 優先度：中

* ディレクトリ構成の再編（Atomic/Featureベース）
* スタイルの一貫性強化（共通化/デザインシステム）
* 不要パッケージ削除、依存のバージョン更新

---

### 5. Doneの定義（評価基準）

| カテゴリ    | Doneの定義                                            |
| ------- | -------------------------------------------------- |
| 型安全性    | `strict: true`で型エラーなし、`any`ゼロまたは理由付き明示             |
| コンポーネント | 各コンポーネントが100行未満、責務分離が明確、props型が明示                  |
| テスト     | カバレッジ50%以上、主要ロジックにユニット・E2Eテスト完備                    |
| 構成      | `components/`, `hooks/`などがAtomic/Feature単位で整理されている |
| スタイル    | 共通クラス・ユーティリティにまとめられ、スタイルガイド文書あり                    |
| 依存管理    | `yarn audit`で脆弱性なし、未使用依存ゼロ、主要ライブラリ最新               |

---

### 6. 次のアクション例

1. `tsconfig.json`の`strict: true`化と型エラー洗い出し
2. `assistant.tsx`の責務分離・分割案作成
3. coverage計測 → テスト対象リストアップ
4. `components/`, `hooks/`の構成整理案のドラフト作成
5. Tailwind共通ユーティリティ設計のたたき案作成
6. `package.json`から未使用依存の棚卸し
7. `useChat.ts`の実装・親コンポーネントのリファクタ（進行中）
8. `useChat`/`ChatMessages`/`ChatInput`のユニットテスト追加・テストカバレッジ計測
9. `tsconfig.json` strict化＆型エラー修正
10. 構成整理・スタイル共通化・依存整理

---

### 7. `assistant.tsx`の責務分離・分割案

#### 進捗状況（2025/07/05時点）

- ✅ UI表示責務の分離（`ChatMessages.tsx`, `ChatInput.tsx`の作成・props型明示）
- ✅ 親コンポーネント（`index.tsx`）での統合
- ✅ ロジック責務の分離（`useChat`カスタムフック化、API通信・認証・reCAPTCHA等）
- ✅ 型定義・型安全性強化（`tsconfig.json` strict化・型エラー/any型排除済み）
- ⬜ テスト（`Message`型共通化済み、テスト未着手）

---

### 次のリファクタリング作業提案

1. **テスト拡充**
   - `ChatMessages`/`ChatInput`/`useChat`のユニットテスト追加
   - テストカバレッジ計測・主要ロジックのテスト網羅
2. **ディレクトリ・構成整理**
   - `components/`, `hooks/`のAtomic/Featureベース整理案ドラフト作成
3. **Tailwind共通ユーティリティ設計**
   - 共通クラス・ユーティリティのたたき案作成
4. **依存パッケージの棚卸し**
   - `package.json`から未使用依存の洗い出し・削除
5. **テストカバレッジ向上・E2Eテスト拡充**
   - 主要機能のE2Eテスト追加、カバレッジ50%以上を目指す
6. **型定義の共通化・型ガイドライン作成**
   - `Message`型などの共通型を`types/`に集約し、型設計方針を文書化

---

#### 優先度順の次アクション

1. 🟡 `useChat`/`ChatMessages`/`ChatInput`のユニットテスト追加・カバレッジ計測
2. 構成整理・スタイル共通化・依存整理
3. 型定義の共通化・型ガイドライン作成
4. E2Eテスト拡充

---

### useChat/ChatMessages/ChatInputのユニットテスト追加・カバレッジ計測 ToDo

1. **テスト戦略の策定**
   - 主要ユースケース
     - [x] ユーザーがメッセージを入力し送信できる（ChatInput.test.tsxで実装・通過）
     - [x] アシスタントからの返信が表示される（ChatMessages.test.tsxで実装・通過）
     - [x] ローディング中のUI表示（ChatMessages.test.tsxで実装・通過）
     - [x] 送信モード（Enter/Mod+Enter）の切替挙動
   - 異常系
     - [x] 空メッセージ送信時のバリデーション
     - [x] APIエラー時のエラーハンドリング
     - [x] reCAPTCHA/認証失敗時の挙動
   - UIイベント
     - [x] 入力欄のonChange/onKeyDownイベント（テスト追加済み）
     - [x] 送信ボタンの活性/非活性（テスト追加済み）
     - [x] ラジオボタンによる送信モード切替（テスト追加済み）
   - API通信
     - [ ] メッセージ送信時のAPIリクエスト/レスポンス
     - [ ] API失敗時のリトライやエラー表示
     - [ ] reCAPTCHAトークン取得・認証トークン取得の分岐
2. **テストファイルの作成**
   - `src/hooks/__tests__/useChat.test.ts`
   - `src/app/assistant/__tests__/ChatMessages.test.tsx`
   - `src/app/assistant/__tests__/ChatInput.test.tsx`
3. **useChatのユニットテスト**
   - メッセージ送信/受信の状態遷移
   - API通信のモック・エラー時の挙動
   - reCAPTCHA/認証の分岐
4. **ChatMessagesのユニットテスト**
   - メッセージリストの表示
   - ローディング時のUI
   - propsの型安全性
5. **ChatInputのユニットテスト**
   - 入力値の変更・送信イベント
   - 送信モード切替の挙動
   - バリデーション・ボタン活性/非活性
6. **カバレッジ計測**
   - `vitest --coverage` でカバレッジを取得
   - 50%以上を目標に不足箇所を洗い出し
7. **テスト観点・カバレッジ結果をドキュメント化**
   - coverageレポートのスクショや主要観点を`docs/testing/`等に記録

---

#### 次のタスク

1. ラジオボタンによる送信モード切替のユニットテスト追加
2. メッセージ送信時のAPIリクエスト/レスポンステスト追加
3. API失敗時のリトライやエラー表示テスト追加
4. reCAPTCHA・認証トークン取得分岐のテスト追加

---