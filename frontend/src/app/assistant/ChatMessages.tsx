import React, { useEffect, useRef } from "react";
import type { ChatMessagesProps, Message } from "../../types/chat";

export type { Message };

// MVP: カード表示機能は削除しシンプルなテキストチャットのみ

// 個別メッセージコンポーネント
const MessageItem = React.memo<{ msg: Message; idx: number }>(({ msg, idx }) => {
  const messageKey = msg.id || `msg_${idx}`;

  if (msg.role === "assistant") {
    return (
      <div
        key={messageKey}
        className="flex items-start gap-3 my-4 animate-fadeIn"
        role="article"
        aria-label="アシスタントメッセージ"
      >
        <div className="w-8 h-8 rounded-full bg-gray-200 mt-0.5 shrink-0" />
        <div className="flex-1 prose prose-sm max-w-none dark:prose-invert leading-relaxed break-words text-[15px]">
          {msg.content}
        </div>
      </div>
    );
  }

  if (msg.role === "user") {
    return (
      <div
        key={messageKey}
        className="flex items-end gap-3 my-4 justify-end animate-fadeIn"
        role="article"
        aria-label="ユーザーメッセージ"
      >
        <div className="flex-1" />
        <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-2 text-[15px] shadow-sm whitespace-pre-wrap leading-relaxed">
          {msg.content}
        </div>
        <div className="w-8 h-8 rounded-full bg-gray-200" />
      </div>
    );
  }

  // fallback: system / その他
  return (
    <div
      key={messageKey}
      className="flex items-end gap-3 my-3 animate-fadeIn"
      aria-label="システムメッセージ"
    >
      <div className="w-8 h-8 rounded-full bg-gray-200" />
      <div className="flex-1 text-sm text-gray-600 whitespace-pre-wrap">{msg.content}</div>
      <div className="flex-1" />
    </div>
  );
});

MessageItem.displayName = 'MessageItem';

export const ChatMessages: React.FC<ChatMessagesProps> = React.memo(({ messages, loading }) => {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex flex-col gap-2 px-1 sm:px-2 py-2 sm:py-4">
      {messages.length === 0 && !loading && (
        <div className="text-gray-400 text-center py-10 text-sm select-none">メッセージはまだありません</div>
      )}
      {messages.map((msg, idx) => (
        <MessageItem key={msg.id || `msg_${idx}`} msg={msg} idx={idx} />
      ))}
      {loading && (
        <div className="text-gray-400 text-center py-4 text-sm animate-pulse">送信中...</div>
      )}
      <div ref={endRef} />
    </div>
  );
});

ChatMessages.displayName = 'ChatMessages';
