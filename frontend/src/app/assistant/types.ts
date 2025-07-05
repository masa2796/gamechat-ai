// チャット関連の型定義

export type Message = {
  role: "user" | "assistant";
  content: string;
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
