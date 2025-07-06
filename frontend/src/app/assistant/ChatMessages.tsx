import React from "react";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

export interface ChatMessagesProps {
  messages: Message[];
  loading?: boolean;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, loading }) => {
  return (
    <div className="flex flex-col gap-2 px-2 py-4 overflow-y-auto flex-1">
      {messages.length === 0 && !loading && (
        <div className="text-muted-foreground text-center py-8">メッセージはまだありません</div>
      )}
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={
            msg.role === "user"
              ? "self-end bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]"
              : "self-start bg-accent text-accent-foreground rounded-lg px-4 py-2 max-w-[80%]"
          }
        >
          {msg.content}
        </div>
      ))}
      {loading && (
        <div className="text-center text-xs text-muted-foreground py-2">送信中...</div>
      )}
    </div>
  );
};
