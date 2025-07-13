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

  return (
    <div style={{ background: '#f7f7f7', minHeight: '100vh', width: '100vw', overflowX: 'hidden' }}>
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'stretch' }}>
        <SidebarProvider>
          <div style={{ minWidth: 160, maxWidth: 200, width: 180, height: '100vh', position: 'sticky', top: 0, zIndex: 20 }}>
            <AppSidebar />
          </div>
        </SidebarProvider>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh', padding: '2rem 0 2rem 0', boxSizing: 'border-box', alignItems: 'center', position: 'relative' }}>
          {/* 入力欄を画面下部に固定（出力欄と左右幅・位置を完全一致） */}
          {/* ChatInputを使用 */}
          <div style={{
            position: 'fixed',
            left: '50%',
            transform: 'translateX(-40%)',
            bottom: 10,
            width: '100%',
            maxWidth: 900,
            minWidth: 0,
            zIndex: 100,
          }}>
            <ChatInput
              input={input}
              onInputChange={setInput}
              onSend={sendMessage}
              loading={loading}
              sendMode={sendMode}
              onSendModeChange={setSendMode}
            />
          </div>
          {/* チャット出力エリア（入力欄分だけ下に余白を確保し、ここだけスクロール） */}
          <div id="chat-area" style={{ width: '100%', maxWidth: 900, margin: '3rem 0 0 0', background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px #0001', padding: 0, display: 'flex', flexDirection: 'column', minHeight: '70vh', overflow: 'hidden', position: 'relative', height: 'calc(100vh - 7rem - 110px)' }}>
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', height: '100%' }}>
              <ChatMessages messages={messages} loading={loading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export { AssistantPage as default };
