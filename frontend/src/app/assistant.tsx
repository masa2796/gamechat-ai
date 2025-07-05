"use client";

import { useChat } from "@/hooks/useChat";
import { ErrorBoundary } from "@/components/error-boundary";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Separator } from "@/components/ui/separator";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { SentryTestComponentWrapper as SentryTestComponent } from "@/components/sentry-test-wrapper";

export const Assistant = () => {
  const {
    messages,
    input,
    setInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
  } = useChat();

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (loading || input.trim().length === 0) return;
    if (sendMode === 'enter') {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    } else if (sendMode === 'mod+enter') {
      if ((e.key === 'Enter') && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        sendMessage();
      }
    }
  };

  return (
    <ErrorBoundary>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger data-testid="sidebar-trigger" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink href="#">
                    GameChat AI
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  <BreadcrumbPage>
                    Chat
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </header>
          {process.env.NODE_ENV === 'development' && <SentryTestComponent />}
          <div className="flex flex-col h-[calc(100vh-4rem)]">
            <div className="flex-1 overflow-y-auto p-4" data-testid="chat-messages">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-8" data-testid="welcome-message">
                  <p>GameChat AIへようこそ！</p>
                  <p>ゲームに関する質問をお気軽にどうぞ。</p>
                </div>
              ) : (
                <div className="space-y-4 max-w-3xl mx-auto">
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div 
                        className={`max-w-[80%] p-3 rounded-lg ${
                          msg.role === 'user' 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-gray-100 text-gray-900'
                        }`}
                        data-testid={msg.role === 'user' ? 'user-message' : 'ai-message'}
                      >
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 text-gray-900 p-3 rounded-lg" data-testid="loading-message">
                        <div className="flex items-center gap-2">
                          <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-gray-600 rounded-full"></div>
                          考え中...
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="border-t p-4" data-testid="chat-input-area">
              <div className="max-w-3xl mx-auto">
                <div className="mb-2 flex gap-4 items-center">
                  <label className="flex items-center gap-1 text-sm">
                    <input
                      type="radio"
                      name="send-mode"
                      value="enter"
                      checked={sendMode === 'enter'}
                      onChange={() => setSendMode('enter')}
                    />
                    Enterで送信
                  </label>
                  <label className="flex items-center gap-1 text-sm">
                    <input
                      type="radio"
                      name="send-mode"
                      value="mod+enter"
                      checked={sendMode === 'mod+enter'}
                      onChange={() => setSendMode('mod+enter')}
                    />
                    Command/Ctrl+Enterで送信
                  </label>
                  <span className="text-xs text-gray-400">（改行: {sendMode === 'enter' ? 'Shift+Enter' : 'Enter'}）</span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleInputKeyDown}
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ゲームについて質問してください..."
                    disabled={loading}
                    data-testid="message-input"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={loading || input.trim().length === 0}
                    className="px-6 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
                    data-testid="send-button"
                  >
                    送信
                  </button>
                </div>
              </div>
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ErrorBoundary>
  );
};
