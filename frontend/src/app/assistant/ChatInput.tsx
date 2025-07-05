import React from "react";
import type { ChatInputProps } from "./types";

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  onInputChange,
  onSend,
  loading,
  sendMode,
  onSendModeChange,
}) => {
  return (
    <div className="flex flex-col gap-2 p-2 border-t bg-background">
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded px-3 py-2 text-base"
          type="text"
          value={input}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={e => {
            if (loading) return;
            if (
              ((sendMode === "enter" && e.key === "Enter" && !e.shiftKey) ||
                (sendMode === "mod+enter" && e.key === "Enter" && (e.metaKey || e.ctrlKey))) &&
              input.trim().length > 0
            ) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder="メッセージを入力..."
          disabled={loading}
        />
        <button
          className="bg-primary text-primary-foreground rounded px-4 py-2 disabled:opacity-50"
          onClick={onSend}
          disabled={loading || input.trim().length === 0}
        >
          送信
        </button>
      </div>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <label className="flex items-center gap-1 cursor-pointer">
          <input
            type="radio"
            checked={sendMode === "enter"}
            onChange={() => onSendModeChange("enter")}
          />
          Enterで送信
        </label>
        <label className="flex items-center gap-1 cursor-pointer">
          <input
            type="radio"
            checked={sendMode === "mod+enter"}
            onChange={() => onSendModeChange("mod+enter")}
          />
          Cmd/Ctrl+Enterで送信
        </label>
        <span className="text-xs text-gray-400">
          （改行: {sendMode === "enter" ? "Shift+Enter" : "Enter"}）
        </span>
      </div>
    </div>
  );
};
