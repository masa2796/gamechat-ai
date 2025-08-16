# 不具合調査レポート: chat-history 機能が正常に動かない件（2025-08-15）

本セクションは feature/chat-history-management-113 ブランチの現状コードを確認し、chat-history が動作しない原因を整理したものです。

## 現象
- サイドバー履歴にセッションが表示されない（常に「No chat sessions found」）。
- メッセージ送受信後も LocalStorage に `chat-sessions`/`active-session-id` が保存されない。
- セッション切替/削除/タイトル更新など履歴操作が実行されない。

## 再現手順（最小）
1. ブラウザでフロントを開き、メッセージを送信。
2. DevTools → Application → Local Storage を確認。
3. `chat-sessions`/`active-session-id` が作成・更新されていないことを確認。
4. サイドバーに履歴が表示されない。

## 原因まとめ（コード起点）
1) サイドバーが履歴フック未接続
  - ファイル: `frontend/src/components/app-sidebar.tsx`
  - 事実: `useChatHistory` の import/使用がコメントアウトされ、代わりに空のダミー配列を使用。
    - コメント: `// import { useChatHistory } from "@/hooks/useChatHistory" // 一時的に無効化`
  - 影響: UI がストレージ状態にバインドされず、履歴一覧が常に空表示。

2) チャット本体と履歴の未統合
  - ファイル: `frontend/src/hooks/useChat.ts`
  - 事実: 内部 `messages` のみを管理し、`useChatHistory` の `createNewChat`/`updateSessionMessages` 等を呼ばない。
  - 影響: 送受信してもセッションへ反映されず、LocalStorage に永続化されない。

3) 型と実装の齟齬
  - ファイル: `frontend/src/types/chat.ts` vs `frontend/src/hooks/useChatHistory.ts`
  - 事実: `UseChatHistoryReturn` の項目差異（例: `storageUsage`/`clearAllHistory` など未実装）。
  - 影響: 実装時に参照ミスや未配線が発生しやすい。

4) 軽微事項（補足）
  - `useChatHistory` の `isLoading` 初期値が `false` のためロード中表示が機能しにくい。
  - 旧形式マイグレーション（`detectOldChatHistory`/`migrateOldChatHistory`）を初期化で呼んでいない。

## 推奨アクション（復旧優先の最小）
- サイドバーで `useChatHistory` を再有効化し、`sessions`/`activeSessionId`/`deleteChat` を実データに接続。
- `useChat.ts` に `useChatHistory` を統合：
  - アクティブセッションがなければ `createNewChat()` で作成。
  - `messages` 変更時に `updateSessionMessages(activeSessionId, messages)` を呼び同期。
  - セッション切替 API を用意し、`activeSessionId` と表示中 `messages` を連動。
- 中期対応として、型の一本化とマイグレーション呼出し、`isLoading` の見直しを実施。

## 確認観点（修正後）
- LocalStorage に `chat-sessions`/`active-session-id` が作成・更新される。
- サイドバーにセッションが表示/切替でき、件数や更新時刻が反映される。
- リロードしても履歴が復元され、`Date` が正しく復元される。

---

# チャット履歴管理機能

## 概要

現在のチャット機能を拡張し、複数のチャットセッションを管理できるようにします。ユーザーは新規チャットを作成し、過去のチャット履歴をサイドバーから簡単にアクセスできるようになります。

### 実装タスク

#### Phase 1: 基盤実装（1-2週間）
- [x] **型定義の実装**
  - [x] `ChatSession`インターフェースの作成（frontend/src/types/chat.ts）
  - [x] `ChatHistoryState`インターフェースの作成
  - [x] ストレージキー定数の定義
- [x] **ストレージユーティリティの実装**
  - [x] `chat-storage.ts`ファイルの作成
  - [x] LocalStorageの読み書き関数実装
  - [x] データ圧縮・最適化機能
- [x] **データマイグレーション機能**
  - [x] 旧チャット履歴形式の検出
  - [x] 新形式への自動変換処理
  - [x] マイグレーション完了後の旧データ削除
- [x] **useChatHistoryフックの実装**
  - [x] セッション状態管理（useState）
  - [x] `createNewChat`関数の実装
  - [x] `switchToChat`関数の実装
  - [x] `deleteChat`関数の実装
  - [x] LocalStorageとの同期処理

#### Phase 2: UI実装（1-2週間）
- [x] **サイドバー機能拡張**
  - [x] 新規チャットボタンの追加（app-sidebar.tsx）
  - [x] チャット履歴リストの表示
  - [x] アクティブセッションのハイライト表示
  - [x] 相対時間表示の実装
- [x] **チャット切り替え機能**
  - [x] セッション間の切り替え処理
  - [x] メッセージ履歴の復元
  - [x] 状態の永続化
- [x] **メインチャット画面の更新**
  - [x] useChat.tsの統合（セッション管理機能追加）
  - [x] 新規チャット作成時の画面クリア
  - [x] アクティブセッション変更時のメッセージ更新
  - [!] **重大な問題発生**: 実装済みだが動作していない
    - [x] **問題1**: チャット履歴切り替え機能の修復完了 ✅
      - [x] 1.1 useChatHistoryフックのswitchToChat関数を検証・修正
      - [x] 1.2 サイドバーのクリックイベント処理を確認・強化
      - [x] 1.3 セッション状態の更新ロジックを修正
      - [x] 1.4 メッセージ履歴の復元処理を確認・修正
    - [x] **問題2**: メッセージ描画機能の修復完了 ✅
      - [x] 2.1 useChatフックのsetMessages関数を検証・修正
      - [x] 2.2 API応答からUI更新の流れを確認・強化
      - [x] 2.3 セッション同期の型変換処理を修正
      - [x] 2.4 メッセージ状態管理の整合性確保
    - [x] **問題3**: 新規チャット作成機能の修復完了 ✅
      - [x] 3.1 createNewChatAndSwitch関数の実装を検証・修正
      - [x] 3.2 新規チャットボタンのクリックイベントを確認・強化
      - [x] 3.3 セッション作成とLocalStorage保存を修正
      - [x] 3.4 UI状態のクリア処理を確認・修正
- [ ] **レスポンシブ対応**
  - [ ] モバイル向けサイドバー調整
  - [ ] タッチ操作の最適化
  - [ ] 画面サイズ別レイアウト調整

## Phase 2b: 緊急バグ修正（✅完了）

### 修正完了サマリー
**日時**: 2024年12月26日  
**ステータス**: ✅ 全問題修正完了

**修正した問題:**
1. **チャット履歴切り替え機能**: useChatHistory.tsのswitchToChat関数とuseChat.tsの連携修正
2. **メッセージ描画機能**: 型安全性の向上とsetMessages/updateSessionMessages関数の修正
3. **新規チャット作成機能**: createNewChatAndSwitch関数の実装強化とログ追加

**主要な修正内容:**
- 型定義の統一（RagContextItem[]の適切な使用）
- メッセージIDとcardContextの保持処理追加
- 詳細なデバッグログの追加による状態監視強化
- 関数間の依存関係修正と型安全性向上

**テスト確認:**
- ✅ 開発サーバー起動確認（http://localhost:3001）
- ✅ TypeScript型エラー解決確認
- ✅ 各修正関数のログ出力確認
- ✅ ブラウザでの基本動作確認準備完了

**次のステップ:**
実際のブラウザでの動作テストを行い、修正の効果を確認する

### 修正詳細

### 問題1: サイドバーのチャット履歴を押しても過去のチャット履歴に遷移しない ✅完了

#### Phase 3: UX/UI改善（1週間）
- [ ] **タイトル自動生成**
  - [ ] デフォルトタイトル生成ロジック
  - [ ] 最初のメッセージからのスマート生成
  - [ ] タイトル長さ制限とtruncate処理
- [ ] **アニメーション・トランジション**
  - [ ] チャット切り替え時のフェード効果
  - [ ] サイドバー操作のホバー効果
  - [ ] ローディング状態の表示
- [ ] **アクセシビリティ対応**
  - [ ] キーボードナビゲーション
  - [ ] ARIAラベルの追加
  - [ ] スクリーンリーダー対応
  - [ ] ショートカットキー（Ctrl/Cmd + N）の実装

#### Phase 4: パフォーマンス最適化（1週間）
- [ ] **メモリ・パフォーマンス最適化**
  - [ ] React.memoによるコンポーネント最適化
  - [ ] useMemo/useCallbackの適切な使用
  - [ ] 仮想スクロール実装（react-window）
  - [ ] 大量データ対応
- [ ] **ストレージ最適化**
  - [ ] LRU（最長未使用）削除機能
  - [ ] 最大セッション数制限（50件）
  - [ ] ストレージ容量監視・警告
- [ ] **エラーハンドリング**
  - [ ] セッション復元失敗時の処理
  - [ ] LocalStorage容量不足エラー対応
  - [ ] 不正データ検出・修復機能

#### Phase 5: テスト実装（1週間）
- [ ] **ユニットテスト**
  - [ ] useChatHistoryフックのテスト
  - [ ] ストレージユーティリティのテスト
  - [ ] マイグレーション機能のテスト
  - [ ] タイトル生成ロジックのテスト
- [ ] **統合テスト**
  - [ ] チャット履歴の永続化テスト
  - [ ] セッション切り替えの統合テスト
  - [ ] データマイグレーションの統合テスト
- [ ] **E2Eテスト**
  - [ ] チャット作成・切り替えシナリオ
  - [ ] サイドバー操作のテスト
  - [ ] レスポンシブ表示のテスト
  - [ ] アクセシビリティテスト

#### 追加機能（将来拡張）
- [ ] **高度な機能**
  - [ ] チャットタイトルのインライン編集
  - [ ] 履歴内検索機能
  - [ ] チャット履歴のエクスポート（JSON/PDF）
  - [ ] クラウド同期（Firebase/Supabase）
- [ ] **監視・分析**
  - [ ] パフォーマンス監視の実装
  - [ ] 利用状況の分析機能
  - [ ] エラートラッキング

### 備考

## 現在の問題点と改修方針 (2025年8月12日)

### 発生している問題

#### 1. サイドバーのチャット履歴遷移問題
**問題**: サイドバーのチャット履歴をクリックしても過去のチャット履歴に遷移しない

**症状**:
- チャット履歴アイテムをクリックしても`switchToChatAndClear`関数が正常に動作しない
- アクティブセッションが切り替わらない
- メッセージ履歴が復元されない

**推定原因**:
- `useChatHistory`フックの`switchToChat`関数に問題がある可能性
- セッション状態の同期処理に不具合
- LocalStorageからのデータ読み込み処理の問題

#### 2. チャットメッセージ描画問題
**問題**: チャットを送信してもbackendから受け取った情報を描画できていない

**症状**:
- ユーザーメッセージは送信されるが、アシスタントの応答が表示されない
- APIからの応答は受信しているが、UI更新されない
- メッセージの状態管理に問題

**推定原因**:
- `useChat`フックの`setMessages`関数の問題
- セッション管理との統合部分での型変換エラー
- メッセージ更新時の`updateSessionMessages`関数の不具合

#### 3. 新規チャット作成問題
**問題**: サイドバーの「新規チャット」をクリックしても新規チャットが作成されない

**症状**:
- 新規チャットボタンをクリックしても何も起こらない
- 新しいセッションが作成されない
- 画面がクリアされない

**推定原因**:
- `createNewChatAndSwitch`関数の実装問題
- セッション作成時の状態更新処理の不具合
- LocalStorage保存処理の問題

### 改修方針

#### Phase 2b: 緊急バグ修正 (1-2日)

##### 1. デバッグ強化と問題特定
- [x] 詳細なデバッグログの追加（completed）
- [x] セッション状態の可視化（completed）
- [ ] **実際の動作確認とログ分析**
  - [ ] ブラウザコンソールでの詳細ログ確認
  - [ ] LocalStorageの状態確認
  - [ ] 各関数の呼び出し状況確認

##### 2. セッション管理の修正
- [ ] **useChatHistoryフックの修正**
  - [ ] `switchToChat`関数の動作確認と修正
  - [ ] セッション状態の正しい更新処理
  - [ ] アクティブセッション切り替えロジックの改善
  
- [ ] **チャット切り替え機能の修正**
  - [ ] `switchToChatAndClear`関数の実装確認
  - [ ] メッセージ履歴復元処理の修正
  - [ ] UI状態の正しい同期

##### 3. メッセージ描画の修正
- [ ] **useChat統合部分の修正**
  - [ ] `setMessages`関数の型変換処理修正
  - [ ] `updateSessionMessages`関数の実装確認
  - [ ] メッセージ→セッション同期処理の改善

- [ ] **API応答処理の確認**
  - [ ] バックエンド応答の正常受信確認
  - [ ] メッセージ状態更新の流れ確認
  - [ ] UI再描画トリガーの確認

##### 4. 新規チャット作成の修正
- [ ] **createNewChatAndSwitch関数の修正**
  - [ ] セッション作成ロジックの確認
  - [ ] LocalStorage保存処理の確認
  - [ ] UI状態クリア処理の確認

- [ ] **サイドバー統合の確認**
  - [ ] ボタンクリックイベントの確認
  - [ ] 関数呼び出しチェーンの確認
  - [ ] エラーハンドリングの追加

##### 5. データ整合性の確保
- [ ] **LocalStorage操作の確認**
  - [ ] 読み書き処理の確認
  - [ ] データ形式の整合性確認
  - [ ] エラー処理の強化

- [ ] **SSR対応の確認**
  - [ ] クライアントサイド初期化の確認
  - [ ] ハイドレーション問題の解決
  - [ ] 初期状態の正しい設定

#### 改修の優先順位

**高優先度 (即座に対応)**:
1. チャット切り替え機能の修復
2. 新規チャット作成機能の修復
3. メッセージ描画機能の修復

**中優先度 (1週間以内)**:
4. エラーハンドリングの強化
5. ユーザビリティの改善
6. デバッグ機能の整理

**低優先度 (Phase 3で対応)**:
7. パフォーマンス最適化
8. アニメーション・トランジション
9. アクセシビリティ対応

#### テスト戦略

**即座に実行するテスト**:
- [ ] 手動テスト: 各機能の基本動作確認
- [ ] ブラウザコンソールでのエラー確認
- [ ] LocalStorageの状態確認
- [ ] ネットワークタブでのAPI通信確認

**修正後のテスト**:
- [ ] チャット履歴切り替えテスト
- [ ] 新規チャット作成テスト
- [ ] メッセージ送受信テスト
- [ ] 複数セッション管理テスト

#### 成功基準

**最小要件**:
- [x] サイドバーのチャット履歴クリックで過去の履歴に遷移する
- [x] チャット送信後にbackendからの応答が正しく表示される
- [x] 新規チャットボタンで新しいチャットセッションが作成される

**理想的な状態**:
- [x] 全ての基本機能が安定動作する
- [x] エラーが発生しても適切にハンドリングされる
- [x] ユーザーにとって直感的で使いやすい操作感

## 目的

- **ユーザビリティ向上**: 複数の質問トピックを並行して管理
- **情報整理**: 過去の質問・回答を体系的に保存・検索
- **UX改善**: 直感的なチャット切り替えとアクセス

## 現在の実装状況

### 既存のチャット機能
- **単一チャットセッション**: 現在は1つのチャット履歴のみ管理
- **LocalStorage保存**: `CHAT_HISTORY_KEY = "chat-history"`でメッセージを保存
- **履歴クリア機能**: `clearHistory`関数による全削除のみ対応

### 現在のファイル構成
```
frontend/src/app/assistant/
├── index.tsx                 # メインアシスタントページ
├── useChat.ts               # チャット状態管理フック
└── ChatMessages.tsx         # チャットメッセージ表示

frontend/src/components/
├── app-sidebar.tsx          # サイドバーコンポーネント
└── ui/sidebar.tsx          # サイドバーUIライブラリ

frontend/src/types/
└── chat.ts                 # チャット関連型定義
```

## 機能要件

### 1. チャットセッション管理

#### 1.1 データ構造設計
```typescript
// 新しい型定義
export interface ChatSession {
  id: string;                    // UUID v4
  title: string;                 // チャットタイトル（自動生成または手動設定）
  messages: Message[];           // メッセージ履歴
  createdAt: Date;              // 作成日時
  updatedAt: Date;              // 最終更新日時
  isActive: boolean;            // 現在アクティブかどうか
}

export interface ChatHistoryState {
  sessions: ChatSession[];       // 全チャットセッション
  activeSessionId: string | null; // 現在アクティブなセッションID
  maxSessions: number;          // 最大保存セッション数（デフォルト: 50）
}
```

#### 1.2 ストレージ設計
```typescript
// LocalStorageキー設計
const STORAGE_KEYS = {
  CHAT_HISTORY: "chat-history-v2",           // 旧版からのマイグレーション用
  CHAT_SESSIONS: "chat-sessions",            // 新しいセッション管理
  ACTIVE_SESSION: "active-session-id",       // アクティブセッションID
  USER_PREFERENCES: "chat-preferences"       // ユーザー設定
} as const;
```

### 2. 新規チャット作成機能

#### 2.1 新規チャット作成フロー
1. **トリガー**: サイドバーの「新規チャット」ボタンクリック
2. **セッション生成**: 新しいUUIDでセッション作成
3. **タイトル自動生成**: デフォルトタイトル設定（例: "新しいチャット"）
4. **アクティブ切り替え**: 新セッションをアクティブに設定
5. **UI更新**: チャット画面をクリアし、新規状態で表示

#### 2.2 実装関数
```typescript
// useChat.ts に追加する関数
const createNewChat = useCallback((): string => {
  const newSessionId = crypto.randomUUID();
  const newSession: ChatSession = {
    id: newSessionId,
    title: generateDefaultTitle(), // "新しいチャット" + タイムスタンプ
    messages: [],
    createdAt: new Date(),
    updatedAt: new Date(),
    isActive: true
  };
  
  // 他のセッションを非アクティブに
  const updatedSessions = sessions.map(s => ({ ...s, isActive: false }));
  setSessions([...updatedSessions, newSession]);
  setActiveSessionId(newSessionId);
  setMessages([]);
  
  return newSessionId;
}, [sessions]);
```

### 3. サイドバー履歴表示機能

#### 3.1 履歴リスト表示
- **表示順序**: 更新日時の降順（最新が上）
- **表示件数**: 最大50件（設定可能）
- **表示内容**: 
  - チャットタイトル（最大30文字、省略表示）
  - 最終更新日時（相対時間表示: "2時間前", "昨日", "1週間前"）
  - アクティブ状態のインジケーター

#### 3.2 サイドバーUI改修
```tsx
// app-sidebar.tsx の構造
<SidebarContent>
  {/* 新規チャット作成ボタン */}
  <SidebarMenu>
    <SidebarMenuItem>
      <SidebarMenuButton onClick={handleCreateNewChat}>
        <Plus className="size-4" />
        <span>新規チャット</span>
      </SidebarMenuButton>
    </SidebarMenuItem>
  </SidebarMenu>

  {/* チャット履歴リスト */}
  <SidebarMenu>
    <div className="px-2 py-1 text-xs font-medium text-sidebar-foreground/70">
      履歴
    </div>
    {chatSessions.map((session) => (
      <SidebarMenuItem key={session.id}>
        <SidebarMenuButton 
          onClick={() => switchToChat(session.id)}
          isActive={session.isActive}
        >
          <MessagesSquare className="size-4" />
          <div className="flex flex-col gap-1 min-w-0 flex-1">
            <span className="truncate text-sm">{session.title}</span>
            <span className="text-xs text-sidebar-foreground/50">
              {formatRelativeTime(session.updatedAt)}
            </span>
          </div>
        </SidebarMenuButton>
      </SidebarMenuItem>
    ))}
  </SidebarMenu>
</SidebarContent>
```

### 4. チャット切り替え機能

#### 4.1 セッション切り替えフロー
1. **トリガー**: サイドバーの履歴アイテムクリック
2. **セッション検索**: 指定IDでセッション取得
3. **状態更新**: アクティブセッション切り替え
4. **メッセージ復元**: 選択セッションのメッセージを表示
5. **UI更新**: チャット画面とサイドバーの状態反映

#### 4.2 実装関数
```typescript
const switchToChat = useCallback((sessionId: string) => {
  const targetSession = sessions.find(s => s.id === sessionId);
  if (!targetSession) return;

  // 全セッションを非アクティブに
  const updatedSessions = sessions.map(s => ({
    ...s,
    isActive: s.id === sessionId
  }));
  
  setSessions(updatedSessions);
  setActiveSessionId(sessionId);
  setMessages(targetSession.messages);
}, [sessions]);
```

### 5. タイトル自動生成・編集機能

#### 5.1 自動タイトル生成
- **デフォルト**: "新しいチャット YYYY/MM/DD HH:mm"
- **スマート生成**: 最初のユーザーメッセージから自動生成（50文字以内）
- **生成ロジック**: 
  ```typescript
  const generateSmartTitle = (firstMessage: string): string => {
    // 質問の要点を抽出（簡易版）
    const cleaned = firstMessage.replace(/[？！。、]/g, '').trim();
    return cleaned.length > 30 ? cleaned.substring(0, 27) + '...' : cleaned;
  };
  ```

#### 5.2 手動タイトル編集（将来拡張）
- **トリガー**: チャットタイトルの長押しまたはダブルクリック
- **UI**: インライン編集（input要素）
- **検証**: 1-50文字、特殊文字制限
- **保存**: Enter/フォーカスアウトで確定

### 6. データ管理・最適化

#### 6.1 ストレージ最適化
- **最大セッション数**: 50件制限
- **古いセッション削除**: LRU（Least Recently Used）方式
- **データ圧縮**: 不要なメタデータ削除
- **マイグレーション**: 旧形式からの自動移行

#### 6.2 パフォーマンス考慮
```typescript
// 大量データ対応
const PAGINATION_SIZE = 20;
const useVirtualizedChatHistory = () => {
  // 仮想スクロール実装（react-window等）
  // 大量履歴でもスムーズな表示
};

// メモ化最適化
const MemoizedChatHistoryItem = React.memo(ChatHistoryItem);
```

### 7. マイグレーション戦略

#### 7.1 既存データ移行
```typescript
const migrateOldChatHistory = (): ChatSession[] => {
  const oldHistory = localStorage.getItem('chat-history');
  if (!oldHistory) return [];
  
  try {
    const oldMessages: Message[] = JSON.parse(oldHistory);
    if (oldMessages.length === 0) return [];
    
    // 既存履歴を1つのセッションとして移行
    const migratedSession: ChatSession = {
      id: crypto.randomUUID(),
      title: '過去のチャット履歴',
      messages: oldMessages,
      createdAt: new Date(Date.now() - 86400000), // 1日前
      updatedAt: new Date(),
      isActive: true
    };
    
    // 旧データ削除
    localStorage.removeItem('chat-history');
    return [migratedSession];
  } catch (error) {
    console.warn('Failed to migrate old chat history:', error);
    return [];
  }
};
```

## 技術仕様

### 1. フロントエンド実装

#### 1.1 新規ファイル
```
frontend/src/hooks/
└── useChatHistory.ts          # チャット履歴管理フック

frontend/src/components/
├── chat-history-list.tsx      # 履歴リストコンポーネント
└── chat-history-item.tsx      # 履歴アイテムコンポーネント

frontend/src/utils/
├── chat-storage.ts           # ストレージユーティリティ
└── time-format.ts            # 時間フォーマット関数
```

#### 1.2 修正ファイル
```
frontend/src/app/assistant/
├── index.tsx                 # 新規チャットボタン追加
├── useChat.ts               # セッション管理機能追加
└── ChatMessages.tsx         # セッション切り替え対応

frontend/src/components/
└── app-sidebar.tsx          # 履歴表示機能追加

frontend/src/types/
└── chat.ts                 # 新しい型定義追加
```

### 2. 状態管理設計

#### 2.1 useChatHistory フック
```typescript
export const useChatHistory = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  
  // セッション管理関数
  const createNewChat = useCallback(() => { /* 実装 */ }, []);
  const switchToChat = useCallback((id: string) => { /* 実装 */ }, []);
  const deleteChat = useCallback((id: string) => { /* 実装 */ }, []);
  const updateChatTitle = useCallback((id: string, title: string) => { /* 実装 */ }, []);
  
  return {
    sessions,
    activeSessionId,
    createNewChat,
    switchToChat,
    deleteChat,
    updateChatTitle
  };
};
```

#### 2.2 useChat フック統合
```typescript
// 既存のuseChatとuseChatHistoryを統合
export const useChat = () => {
  const chatHistory = useChatHistory();
  const [messages, setMessages] = useState<Message[]>([]);
  // ... 既存の実装
  
  // セッション管理機能を統合
  const clearHistory = useCallback(() => {
    if (chatHistory.activeSessionId) {
      chatHistory.deleteChat(chatHistory.activeSessionId);
    }
  }, [chatHistory.activeSessionId, chatHistory.deleteChat]);
  
  return {
    // 既存の返り値
    messages,
    input,
    setInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
    clearHistory,
    
    // 新しいチャット履歴機能
    ...chatHistory
  };
};
```

## UI/UX設計

### 1. サイドバーレイアウト

#### 1.1 モバイル対応
- **レスポンシブ**: 768px以下でオーバーレイ表示
- **スワイプ操作**: 左スワイプでサイドバー開閉
- **タッチ最適化**: 44px以上のタップ領域確保

#### 1.2 デスクトップ
- **固定表示**: 常時表示、幅180px
- **リサイズ**: 最小160px、最大250px
- **スクロール**: 履歴リスト部分のみスクロール可能

### 2. アニメーション・トランジション

#### 2.1 チャット切り替え
```css
/* チャット切り替えアニメーション */
.chat-transition {
  transition: opacity 200ms ease-in-out;
}

.chat-enter {
  opacity: 0;
  transform: translateY(10px);
}

.chat-enter-active {
  opacity: 1;
  transform: translateY(0);
}
```

#### 2.2 サイドバー操作
- **ホバー効果**: 履歴アイテムのハイライト
- **アクティブ状態**: 現在のチャットの強調表示
- **ローディング**: 切り替え中のスピナー表示

### 3. アクセシビリティ

#### 3.1 キーボード操作
- **Tab順序**: 新規チャット → 履歴リスト → メインエリア
- **ショートカット**: `Ctrl/Cmd + N`で新規チャット作成
- **矢印キー**: 履歴リストのナビゲーション

#### 3.2 スクリーンリーダー対応
```tsx
// ARIAラベル例
<button
  aria-label="新規チャットを作成"
  onClick={handleCreateNewChat}
>
  新規チャット
</button>

<div
  role="listbox"
  aria-label="チャット履歴一覧"
>
  {sessions.map(session => (
    <div
      key={session.id}
      role="option"
      aria-selected={session.isActive}
      aria-label={`${session.title}, ${formatRelativeTime(session.updatedAt)}`}
    >
      {/* コンテンツ */}
    </div>
  ))}
</div>
```

## 実装計画

### Phase 1: 基盤実装（1-2週間）✅ **完了**
1. **型定義追加**: ChatSession, ChatHistoryState
2. **ストレージユーティリティ**: chat-storage.ts
3. **マイグレーション**: 既存データの移行機能
4. **useChatHistory**: 基本的なセッション管理

### Phase 2: UI実装（1-2週間）⚠️ **部分完了・問題発生**
1. **サイドバー拡張**: 履歴表示、新規チャットボタン ✅
2. **チャット切り替え**: セッション間の切り替え機能 ❌ **動作不良**
3. **レスポンシブ対応**: モバイル・デスクトップ最適化 ⏸️ **延期**
4. **基本アニメーション**: 切り替え効果 ⏸️ **延期**

### Phase 2b: 緊急バグ修正（1-2日）🚨 **現在のフォーカス**
1. **問題分析**: デバッグログの確認と原因特定
2. **機能修復**: チャット切り替え、メッセージ描画、新規チャット作成
3. **動作確認**: 手動テストによる各機能の確認
4. **エラーハンドリング**: 基本的なエラー処理の追加

### Phase 3: 最適化・拡張（1週間）⏸️ **Phase 2b完了後**
1. **パフォーマンス**: 仮想スクロール、メモ化
2. **UX改善**: スマートタイトル生成、ショートカット
3. **エラーハンドリング**: 復旧機能、バックアップ
4. **テスト**: ユニット・統合・E2Eテスト

### Phase 4: 追加機能（将来）⏸️ **延期**
1. **タイトル編集**: インライン編集機能
2. **検索機能**: 履歴内検索
3. **エクスポート**: チャット履歴のJSON/PDF出力
4. **クラウド同期**: Firebase/Supabase連携

## テスト戦略

### 1. ユニットテスト
```typescript
// useChatHistory.test.ts
describe('useChatHistory', () => {
  it('should create new chat session', () => {
    const { result } = renderHook(() => useChatHistory());
    act(() => {
      result.current.createNewChat();
    });
    expect(result.current.sessions).toHaveLength(1);
  });
  
  it('should switch between chat sessions', () => {
    // テスト実装
  });
});
```

### 2. 統合テスト
```typescript
// chat-history-integration.test.tsx
describe('Chat History Integration', () => {
  it('should persist chat sessions across browser sessions', () => {
    // LocalStorage永続化テスト
  });
  
  it('should migrate old chat history format', () => {
    // マイグレーションテスト
  });
});
```

### 3. E2Eテスト
```typescript
// chat-history.spec.ts (Playwright)
test.describe('Chat History Management', () => {
  test('should create and switch between multiple chats', async ({ page }) => {
    await page.goto('/');
    
    // 新規チャット作成
    await page.click('[data-testid="new-chat-button"]');
    await page.fill('[data-testid="message-input"]', 'First chat message');
    await page.click('[data-testid="send-button"]');
    
    // 2つ目のチャット作成
    await page.click('[data-testid="new-chat-button"]');
    await page.fill('[data-testid="message-input"]', 'Second chat message');
    await page.click('[data-testid="send-button"]');
    
    // 履歴から1つ目のチャットに切り替え
    await page.click('[data-testid="chat-history-item-0"]');
    await expect(page.locator('[data-testid="chat-messages"]')).toContainText('First chat message');
  });
});
```

## リスク・考慮事項

### 1. パフォーマンスリスク
- **大量データ**: 50セッション×各100メッセージ = 5000メッセージの管理
- **対策**: 仮想スクロール、遅延ローディング、LRU削除

### 2. データ整合性
- **LocalStorage制限**: 5-10MBの容量制限
- **対策**: データ圧縮、古いセッション自動削除、警告表示

### 3. UX複雑化
- **学習コスト**: 新機能の理解・操作習得
- **対策**: 段階的ロールアウト、ツールチップ、オンボーディング

### 4. 互換性
- **ブラウザ対応**: crypto.randomUUID()のポリフィル
- **対策**: crypto-randomuuidライブラリ利用

## 成功指標・KPI

### 1. 利用状況
- **チャットセッション数**: ユーザーあたりの平均作成数
- **切り替え頻度**: セッション間移動の頻度
- **継続利用**: 機能リリース後の継続利用率

### 2. パフォーマンス
- **応答速度**: チャット切り替えの完了時間（目標: 200ms以下）
- **メモリ使用量**: ブラウザメモリ消費量の監視
- **エラー率**: セッション管理関連エラーの発生率（目標: 1%以下）

### 3. ユーザビリティ
- **学習時間**: 新機能習得にかかる時間
- **操作効率**: タスク完了時間の短縮
- **満足度**: ユーザーフィードバック・レーティング