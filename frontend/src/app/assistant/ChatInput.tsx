import React from "react";
import type { ChatInputProps } from "../../types/chat";

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  onInputChange,
  onSend,
  loading,
  sendMode,
  onSendModeChange,
}) => {
  return (
    <div className="flex flex-col gap-2 p-2 sm:p-3 bg-background">
      <div className="flex gap-2 items-stretch">
        <input
          className="flex-1 border rounded-md px-3 py-2 text-[15px] focus:outline-none focus:ring-2 focus:ring-blue-400/60 shadow-inner"
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
          className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors shadow"
          onClick={onSend}
          disabled={loading || input.trim().length === 0}
        >
          送信
        </button>
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-gray-500 px-0.5">
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
        <span className="text-[11px] text-gray-400">
          （改行: {sendMode === "enter" ? "Shift+Enter" : "Enter"}）
        </span>
      </div>
    </div>
  );
};
