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
