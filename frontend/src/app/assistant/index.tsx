"use client";
import React from "react";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { useChat } from "./useChat";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
// import { CardList } from "@/components/CardList";







const AssistantPage: React.FC = () => {
  const {
    messages,
    input,
    setInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
  } = useChat();

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
          <form
            style={{
              display: 'flex',
              gap: '0.7rem',
              position: 'fixed',
              left: '50%',
              transform: 'translateX(-50%)',
              bottom: 0,
              background: '#fff',
              borderRadius: '0 0 10px 10px',
              boxShadow: '0 2px 8px #0001',
              padding: '1rem 1.5rem',
              zIndex: 100,
              borderTop: '1px solid #eee',
              width: '100%',
              maxWidth: 900,
              minWidth: 0,
              margin: '0',
            }}
            onSubmit={e => {
              e.preventDefault();
              sendMessage();
            }}
          >
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="ゲームについて質問してください..."
              style={{
                flex: 1,
                padding: '0.7rem 1rem',
                borderRadius: 18,
                border: '1px solid #ccc',
                fontSize: '1rem',
                outline: 'none',
              }}
              disabled={loading}
            />
            <button
              type="submit"
              style={{
                background: '#1976d2',
                color: '#fff',
                border: 'none',
                borderRadius: 18,
                padding: '0 1.3rem',
                fontSize: '1rem',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                opacity: loading || !input.trim() ? 0.7 : 1,
                marginLeft: '0.7rem',
              }}
              disabled={loading || !input.trim()}
            >
              送信
            </button>
          </form>
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
