"use client";
import React, { useEffect, useRef } from "react";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { useChat } from "./useChat";
// MVP版: サイドバー/履歴管理を削除したシンプルページ

const AssistantPage: React.FC = () => {
  // チャット履歴管理フック（状態監視用）
  const activeSessionId = null; // MVPでは未使用

  // useChatの返り値をそのまま利用（型安全）
  const chat = useChat();
  const messages = chat.messages;
  const input = chat.input;
  const setInput = chat.setInput;
  const loading = chat.loading;
  const sendMode = chat.sendMode;
  const setSendMode = chat.setSendMode;
  const sendMessage = chat.sendMessage;
  const clearHistory = chat.clearHistory;
  const activeSession = chat.activeSession;

  // アクティブセッションがない場合は新規セッションを作成（現在は無効化）
  useEffect(() => {
    console.log('[AssistantPage] セッション自動作成チェック（無効化中）:', {
      activeSessionId,
      hasCreateFunction: !!chat.createNewChatAndSwitch
    });
    
    // 無限ループ防止のため、自動作成を一時的に無効化
    console.log('[AssistantPage] 自動セッション作成は現在無効化されています');
    return;
    
    // 以下のコードは無効化（削除予定）
    // 既に一度実行した場合はスキップ（無限ループ防止）
    // if (activeSessionId !== null) {
    //   console.log('[AssistantPage] アクティブセッションが存在するため、自動作成をスキップ');
    //   return;
    // }
    
    // createNewChatAndSwitch関数がない場合はスキップ
    // if (!chat.createNewChatAndSwitch) {
    //   console.log('[AssistantPage] createNewChatAndSwitch関数が利用できないため、自動作成をスキップ');
    //   return;
    // }
    
    // console.log('[AssistantPage] 新規セッション作成を実行...');
    // try {
    //   const newSessionId = chat.createNewChatAndSwitch();
    //   console.log('[AssistantPage] 新規セッション作成完了:', newSessionId);
    // } catch (err) {
    //   console.error('[AssistantPage] 新規セッション作成エラー:', err);
    // }
  }, [activeSessionId, chat.createNewChatAndSwitch]); // 依存関係を元に戻す

  // メッセージコンテナ参照（iOS でのスクロール挙動安定化）
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // 新しいメッセージ到着時に最下部へスムーススクロール
    const el = scrollContainerRef.current;
    if (!el) return;
    // ネイティブ挙動を優先し、強制ジャンプし過ぎないよう requestAnimationFrame
    requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    });
  }, [messages, loading]);

  return (
    <div className="min-h-dvh w-full flex flex-col items-center bg-gray-50 px-2 sm:px-4 py-2">
      <div className="w-full max-w-[780px] flex flex-col flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden h-[calc(100dvh-2rem)] sm:h-[calc(100dvh-3rem)]">
        <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-100/70 backdrop-blur supports-[backdrop-filter]:bg-gray-100/60">
          <h1 className="font-semibold text-gray-800 text-base sm:text-lg">チャット</h1>
          {messages.length > 0 && (
            <button
              onClick={clearHistory}
              className="text-[11px] sm:text-xs px-2 py-1 rounded border border-gray-300 text-gray-600 hover:text-red-600 hover:border-red-400 transition-colors"
              aria-label="履歴をクリア"
            >クリア</button>
          )}
        </div>
        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto overscroll-y-contain px-2 sm:px-4 py-3 scroll-smooth">
          <ChatMessages messages={messages} loading={loading} />
          {/* スクロール下部スペース（iOSの下部ジェスチャー領域確保） */}
          <div className="h-4" />
        </div>
        <div className="border-t bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
          <ChatInput
            input={input}
            onInputChange={setInput}
            onSend={sendMessage}
            loading={loading}
            sendMode={sendMode}
            onSendModeChange={setSendMode}
          />
        </div>
      </div>
      <p className="mt-2 text-[10px] sm:text-xs text-gray-400 select-none">MVP Build</p>
    </div>
  );
};

export { AssistantPage as default };
