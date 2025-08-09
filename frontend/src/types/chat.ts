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
}

// チャット履歴管理のための新しい型定義

/**
 * チャットセッション
 * 個別のチャット会話を管理するための型
 */
export interface ChatSession {
  /** セッションの一意識別子（UUID v4） */
  id: string;
  /** チャットタイトル（自動生成または手動設定） */
  title: string;
  /** メッセージ履歴 */
  messages: Message[];
  /** 作成日時 */
  createdAt: Date;
  /** 最終更新日時 */
  updatedAt: Date;
  /** 現在アクティブかどうか */
  isActive: boolean;
}

/**
 * チャット履歴の全体状態
 * 複数のチャットセッションを管理するための型
 */
export interface ChatHistoryState {
  /** 全チャットセッション */
  sessions: ChatSession[];
  /** 現在アクティブなセッションID */
  activeSessionId: string | null;
  /** 最大保存セッション数（デフォルト: 50） */
  maxSessions: number;
}

/**
 * LocalStorageキー定数
 * チャット履歴の保存に使用するキーの定義
 */
export const STORAGE_KEYS = {
  /** 旧版からのマイグレーション用 */
  CHAT_HISTORY: "chat-history-v2",
  /** 新しいセッション管理 */
  CHAT_SESSIONS: "chat-sessions",
  /** アクティブセッションID */
  ACTIVE_SESSION: "active-session-id",
  /** ユーザー設定 */
  USER_PREFERENCES: "chat-preferences"
} as const;

/**
 * チャット履歴管理フックの返り値型
 */
export interface UseChatHistoryReturn {
  /** 全セッション */
  sessions: ChatSession[];
  /** アクティブセッションID */
  activeSessionId: string | null;
  /** 新規チャット作成 */
  createNewChat: () => string;
  /** チャット切り替え */
  switchToChat: (sessionId: string) => void;
  /** チャット削除 */
  deleteChat: (sessionId: string) => void;
  /** チャットタイトル更新 */
  updateChatTitle: (sessionId: string, title: string) => void;
}
