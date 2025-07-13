"use client";
import React from "react";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { useChat } from "./useChat";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
// import { CardList } from "@/components/CardList";
const AssistantPage: React.FC = () => {

  // useChatの返り値が空でもデフォルト値で動作するようにする
  const chat = useChat() || {};
  const messages = chat.messages || [];
  const input = chat.input ?? "";
  const setInput = chat.setInput || (() => {});
  const loading = chat.loading ?? false;
  const sendMode = chat.sendMode || "enter";
  const setSendMode = chat.setSendMode || (() => {});
  const sendMessage = chat.sendMessage || (() => {});
  const cardContext = chat.cardContext;

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
              <div className="chat-messages-scroll flex-1 overflow-y-auto p-6">
                <ChatMessages messages={messages} loading={loading} cardContext={cardContext} />
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
