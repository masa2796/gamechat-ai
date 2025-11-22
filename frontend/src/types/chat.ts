// 共通チャット型定義（今後他機能でも利用可能なよう拡張前提）

export type Message = {
  id?: string; // メッセージの一意識別子
  role: "user" | "assistant";
  content: string;
  cardContext?: import("./rag").RagContextItem[];
};

export interface ChatMessagesProps {
  messages: Message[];
  loading?: boolean;
}

export interface ChatInputProps {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  loading?: boolean;
  sendMode: "enter" | "mod+enter";
  onSendModeChange: (mode: "enter" | "mod+enter") => void;
}

export interface UseChatReturn {
  messages: Message[];
  input: string;
  setInput: (value: string) => void;
  loading: boolean;
  sendMode: "enter" | "mod+enter";
  setSendMode: (mode: "enter" | "mod+enter") => void;
  sendMessage: () => Promise<void>;
  recaptchaReady: boolean;
  setRecaptchaReady: (ready: boolean) => void;
  clearHistory: () => void;
  activeSessionId: string | null; // 常に null (MVP)
  activeSession: ChatSession | null; // 常に null (MVP)
  createNewChatAndSwitch: () => string; // ダミー
  switchToChatAndClear: (sessionId: string) => void; // ダミー
}

// チャット履歴管理のための新しい型定義

/**
 * チャットセッション
 * 個別のチャット会話を管理するための型
 */
export interface ChatSession { 
  id: string; 
  title: string; 
  messages: Message[]; 
  createdAt: Date;
  updatedAt: Date;
  isActive?: boolean;
}

/**
 * チャット履歴の全体状態
 * 複数のチャットセッションを管理するための型
 */
export interface ChatHistoryState { 
  sessions: ChatSession[]; 
  activeSessionId: string | null;
  maxSessions?: number;
}

/**
 * LocalStorageキー定数
 * チャット履歴の保存に使用するキーの定義
 */
export const STORAGE_KEYS = { CHAT_HISTORY: "chat-history-v2" } as const;

/**
 * チャット履歴管理フックの返り値型
 */
export interface UseChatHistoryReturn {
  /** 全セッション（更新日時降順） */
  sessions: ChatSession[];
  /** アクティブセッションID */
  activeSessionId: string | null;
  /** アクティブセッション */
  activeSession: ChatSession | null;
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** ストレージ使用状況 */
  storageUsage: {
    totalSize: number;
    sessionCount: number;
    averageSessionSize: number;
    isNearLimit: boolean;
    isOverWarningThreshold: boolean;
  };
  /** 新規チャット作成 */
  createNewChat: (initialMessage?: string) => string;
  /** チャット切り替え */
  switchToChat: (sessionId: string) => void;
  /** チャット削除 */
  deleteChat: (sessionId: string) => void;
  /** チャットタイトル更新 */
  updateChatTitle: (sessionId: string, title: string) => void;
  /** セッションにメッセージ追加 */
  addMessageToChat: (sessionId: string, message: { role: 'user' | 'assistant', content: string }) => void;
  /** セッションのメッセージ更新 */
  updateSessionMessages: (sessionId: string, messages: { role: 'user' | 'assistant', content: string }[]) => void;
  /** エラークリア */
  clearError: () => void;
  /** 全履歴削除 */
  clearAllHistory: () => void;
}
