// 共通チャット型定義（今後他機能でも利用可能なよう拡張前提）

export type Message = {
  role: "user" | "assistant";
  content: string;
};

export interface ChatMessagesProps {
  messages: Message[];
  loading?: boolean;
  cardContext?: import("./rag").RagContextItem[];
}

export interface ChatInputProps {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  loading?: boolean;
  sendMode: "enter" | "mod+enter";
  onSendModeChange: (mode: "enter" | "mod+enter") => void;
}
