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
// MVPでは複数セッションを扱わないため簡略化（将来拡張用に型は最小限保持）
export interface ChatSession { id: string; title: string; messages: Message[]; }

/**
 * チャット履歴の全体状態
 * 複数のチャットセッションを管理するための型
 */
// 履歴管理はMVPで未使用のため簡略化
export interface ChatHistoryState { sessions: ChatSession[]; activeSessionId: string | null; }

/**
 * LocalStorageキー定数
 * チャット履歴の保存に使用するキーの定義
 */
export const STORAGE_KEYS = { CHAT_HISTORY: "chat-history-v2" } as const; // 将来復活時用プレースホルダ

/**
 * チャット履歴管理フックの返り値型
 */
// 履歴フックは削除済み
// 履歴機能はMVPで未使用のためエクスポートを停止（復活時に再導入）
// export interface UseChatHistoryReturn { sessions: ChatSession[]; }
