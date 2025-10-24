"use client";
import React, { useEffect } from "react";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { useChat } from "./useChat";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

const AssistantPage: React.FC = () => {
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
  const activeSessionId = chat.activeSessionId;

  // アクティブセッションがない場合は新規セッションを作成
  useEffect(() => {
    console.log('[AssistantPage] セッション自動作成チェック:', {
      activeSessionId,
      hasCreateFunction: !!chat.createNewChatAndSwitch
    });
    
    // 既にアクティブセッションがある場合はスキップ
    if (activeSessionId !== null) {
      console.log('[AssistantPage] アクティブセッションが存在するため、自動作成をスキップ');
      return;
    }
    
    // createNewChatAndSwitch関数がない場合はスキップ
    if (!chat.createNewChatAndSwitch) {
      console.log('[AssistantPage] createNewChatAndSwitch関数が利用できないため、自動作成をスキップ');
      return;
    }
    
    console.log('[AssistantPage] 新規セッション作成を実行...');
    try {
      const newSessionId = chat.createNewChatAndSwitch();
      console.log('[AssistantPage] 新規セッション作成完了:', newSessionId);
    } catch (error) {
      console.error('[AssistantPage] 新規セッション作成中にエラー:', error);
    }
  }, [activeSessionId, chat]);

  return (
    <SidebarProvider>
      <div className="flex h-screen">
        {/* サイドバー */}
        <AppSidebar />
        
        {/* メインコンテンツ */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* ヘッダー */}
          <div className="border-b bg-background p-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-semibold">
                  {activeSession?.title || "新しいチャット"}
                </h1>
                <p className="text-sm text-muted-foreground">
                  ゲーム関連の質問にお答えします
                </p>
              </div>
              
              {/* クリアボタン */}
              <button
                onClick={clearHistory}
                className="px-3 py-1 text-sm border rounded-md hover:bg-gray-50"
                data-testid="clear-history-button"
              >
                履歴をクリア
              </button>
            </div>
          </div>

          {/* チャット表示エリア */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <ChatMessages messages={messages} loading={loading} />
            <div className="p-4 border-t">
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
        </main>
      </div>
    </SidebarProvider>
  );
};

export default AssistantPage;
