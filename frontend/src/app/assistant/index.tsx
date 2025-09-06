"use client";
import React, { useEffect } from "react";
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

  return (
    <div className="min-h-screen w-screen flex flex-col items-center bg-gray-50 p-4">
      <div className="w-full max-w-[780px] flex flex-col flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-100">
          <h2 className="font-semibold text-gray-800">チャット</h2>
          {messages.length > 0 && (
            <button
              onClick={clearHistory}
              className="text-xs px-2 py-1 rounded border text-gray-600 hover:text-red-600 hover:border-red-400"
            >クリア</button>
          )}
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <ChatMessages messages={messages} loading={loading} />
        </div>
        <div className="border-t">
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
      <p className="mt-4 text-xs text-gray-400">MVP Build</p>
    </div>
  );
};

export { AssistantPage as default };
