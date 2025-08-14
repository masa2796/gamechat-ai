"use client";
import React, { useEffect } from "react";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { useChat } from "./useChat";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
// import { useChatHistory } from "@/hooks/useChatHistory"; // 一時的に無効化

const AssistantPage: React.FC = () => {
  // チャット履歴管理フック（状態監視用）
  // const { activeSessionId } = useChatHistory(); // 一時的に無効化
  const activeSessionId = null; // 一時的にnullで固定

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
    <div className="chat-bg min-h-screen w-screen overflow-x-hidden">
      <div className="flex min-h-screen items-stretch">
        <SidebarProvider>
          <div className="sidebar-wrapper min-w-[160px] max-w-[200px] w-[180px] h-screen sticky top-0 z-20">
            <AppSidebar />
          </div>
        </SidebarProvider>
        <div className="main-content flex-1 flex flex-col min-h-screen py-8 box-border items-center relative">
          <div className="chat-container w-full max-w-[900px] mx-auto flex flex-col h-full relative">
            {/* チャット出力エリア */}
            <div id="chat-area" className="chat-area bg-white rounded-[10px] shadow-[0_2px_8px_#0001] flex flex-col overflow-hidden relative" style={{height: 'calc(100vh - 7rem - 20px)'}}>
              {/* チャットヘッダー */}
              <div className="chat-header flex items-center justify-between p-4 border-b border-gray-200">
                <div className="flex flex-col">
                  <h2 className="text-lg font-semibold text-gray-800">
                    {activeSession?.title || "チャット"}
                  </h2>
                  {activeSession && messages.length > 0 && (
                    <span className="text-sm text-gray-500">
                      {messages.length}件のメッセージ
                    </span>
                  )}
                </div>
                {messages.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="px-3 py-1 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded border border-gray-300 hover:border-red-300 transition-colors"
                    title="チャット履歴をクリア"
                  >
                    履歴クリア
                  </button>
                )}
              </div>
              <div className="chat-messages-scroll flex-1 overflow-y-auto p-6">
                <ChatMessages messages={messages} loading={loading} />
              </div>
            </div>
          {/* 入力欄を画面最下部に固定 */}
          <div className="chat-input-fixed w-full max-w-[900px] fixed bottom-3 transform z-[100] bg-white">
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
        </div>
      </div>
    </div>
  );
};

export { AssistantPage as default };
