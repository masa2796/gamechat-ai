import React from "react";
import type { ChatMessagesProps, Message } from "../../types/chat";

export type { Message };

// MVP: カード表示機能は削除しシンプルなテキストチャットのみ

// 個別メッセージコンポーネント
const MessageItem = React.memo<{ msg: Message; idx: number }>(({ msg, idx }) => {
  const messageKey = msg.id || `msg_${idx}`;
  
  if (msg.role === "assistant") {
    return (
      <div key={messageKey} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.7rem', margin: '1.2rem 0' }}>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee', marginTop: '0.2rem' }} />
        <div style={{ flex: 1 }}><div>{msg.content}</div></div>
      </div>
    );
  } else if (msg.role === "user") {
    return (
      <div key={messageKey} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
        <div style={{ flex: 1 }} />
        <div style={{ background: '#1976d2', color: '#fff', borderRadius: '18px 18px 2px 18px', padding: '0.7rem 1.1rem', maxWidth: '70%', fontSize: '1rem' }}>{msg.content}</div>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
      </div>
    );
  } else {
    // fallback: system等
    return (
      <div key={messageKey} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
        <div style={{ flex: 1 }}>{msg.content}</div>
        <div style={{ flex: 1 }} />
      </div>
    );
  }
});

MessageItem.displayName = 'MessageItem';

export const ChatMessages: React.FC<ChatMessagesProps> = React.memo(({ messages, loading }) => {
  // デバッグ用ログ
  console.log(`[ChatMessages] レンダリング中 - メッセージ数: ${messages.length}`);
  messages.forEach((msg, idx) => {
    console.log(`[ChatMessages] メッセージ${idx}: role=${msg.role}, content="${msg.content}", cardContext=${msg.cardContext?.length || 0}件`);
  });
  
  return (
    <div className="flex flex-col gap-2 px-2 py-4 overflow-y-auto flex-1">
      {messages.length === 0 && !loading && (
        <div className="text-muted-foreground text-center py-8">メッセージはまだありません</div>
      )}
      {messages.map((msg, idx) => (
        <MessageItem key={msg.id || `msg_${idx}`} msg={msg} idx={idx} />
      ))}
      {loading && (
        <div className="text-muted-foreground text-center py-4">送信中...</div>
      )}
    </div>
  );
});

ChatMessages.displayName = 'ChatMessages';
