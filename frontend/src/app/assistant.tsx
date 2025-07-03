"use client";

import { useState, useEffect } from "react";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Separator } from "@/components/ui/separator";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { ErrorBoundary } from "@/components/error-boundary";
import { SentryTestComponentWrapper as SentryTestComponent } from "@/components/sentry-test-wrapper";
import { auth as firebaseAuth } from "@/lib/firebase";
import { captureAPIError, captureUserAction, setSentryTag } from "@/lib/sentry";

interface Message {
  role: "user" | "assistant";
  content: string;
}

declare global {
  interface Window {
    grecaptcha?: {
      execute: (siteKey: string, options: { action: string }) => Promise<string>;
      ready: (callback: () => void) => void;
    };
  }
}

// reCAPTCHAが無効かどうかを判定するヘルパー関数
const isRecaptchaDisabled = () => {
  return (
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA === "true" ||
    process.env.NEXT_PUBLIC_ENVIRONMENT === "test" ||
    !process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY
  );
};

export const Assistant = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recaptchaReady, setRecaptchaReady] = useState(false);
  // 送信モード: 'enter' or 'mod+enter'
  const [sendMode, setSendMode] = useState<'enter' | 'mod+enter'>('enter');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('chat-send-mode');
      if (saved === 'enter' || saved === 'mod+enter') {
        setSendMode(saved);
      }
    }
  }, []);

  // 送信モードのローカルストレージ保存
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chat-send-mode', sendMode);
    }
  }, [sendMode]);

  // reCAPTCHAスクリプトの動的ロード
  useEffect(() => {
    // Sentryタグを設定
    setSentryTag("component", "assistant");
    setSentryTag("environment", process.env.NEXT_PUBLIC_ENVIRONMENT || "development");
    
    
    // テスト環境またはreCAPTCHA無効化フラグが設定されている場合はスクリプトを読み込まない
    if (isRecaptchaDisabled()) {
      setRecaptchaReady(true);
      return;
    }
    
    if (typeof window !== "undefined" && !window.grecaptcha) {
      const script = document.createElement("script");
      script.src = `https://www.google.com/recaptcha/api.js?render=${process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}`;
      script.async = true;
      script.onload = () => setRecaptchaReady(true);
      document.body.appendChild(script);
    } else {
      setRecaptchaReady(true);
    }
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage: Message = { role: "user", content: input.trim() };
    
    // Sentryにユーザーアクションを記録
    captureUserAction("message_sent", { messageLength: input.length });
    
    // 状態を更新（ローディング開始、入力クリア、メッセージ追加）
    setLoading(true);
    setInput("");
    setMessages(prev => [...prev, userMessage]);

    // API URLを環境変数から取得（テスト環境では外部API、本番では内部API Routes）
    const apiUrl = process.env.NEXT_PUBLIC_API_URL 
      ? `${process.env.NEXT_PUBLIC_API_URL}/api/rag/query`
      : "/api/rag/query";

    try {
      let idToken = "";
      if (firebaseAuth && firebaseAuth.currentUser) {
        try {
          idToken = await firebaseAuth.currentUser.getIdToken();
        } catch (error) {
          console.warn("Failed to get auth token:", error);
        }
      }
      let recaptchaToken = "";
    
      if (isRecaptchaDisabled()) {
        recaptchaToken = "test"; // バックエンドでテストトークンとして認識される
    
      } else if (window.grecaptcha && recaptchaReady) {
        recaptchaToken = await window.grecaptcha.execute(
          process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || '',
          { action: "submit" }
        );
      }

     
      const res = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // APIキー認証ヘッダーを追加
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
          ...(idToken ? { Authorization: `Bearer ${idToken}` } : {})
        },
        body: JSON.stringify({ 
          question: userMessage.content,
          top_k: 5,
          with_context: true,
          recaptchaToken: recaptchaToken
        }),
        credentials: "include"
      });
      
      if (!res.ok) {
        // サーバーからのエラーレスポンスをより詳細に処理
        const errorData = await res.json().catch(() => ({ error: { message: `HTTP error! status: ${res.status}` } }));
        throw new Error(errorData.error?.message || `APIエラーが発生しました (ステータス: ${res.status})`);
      }

      const data = await res.json();
      
      if (data.error) {
        throw new Error(data.error.message || "APIエラーが発生しました");
      }
      
      const botMessage: Message = { 
        role: "assistant", 
        content: data.answer || "エラーが発生しました" 
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      
      let displayMessage = "エラーが発生しました。もう一度お試しください。";
      if (error instanceof Error) {
        if (error.message.includes("Invalid authentication credentials") || error.message.includes("401")) {
          displayMessage = "認証に失敗しました。APIキーの設定を確認してください。";
        } else {
          displayMessage = error.message;
        }
      }

      // Sentryにエラーを報告
      captureAPIError(error as Error, {
        endpoint: apiUrl,
        userMessage: userMessage.content,
        timestamp: new Date().toISOString()
      });
      
      const errorMessage: Message = { 
        role: "assistant", 
        content: displayMessage
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (loading || input.trim().length === 0) return;
    if (sendMode === 'enter') {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
      // Shift+Enterは改行（inputなら無視、textareaなら改行）
    } else if (sendMode === 'mod+enter') {
      // Mac: Command+Enter, Windows: Ctrl+Enter
      if ((e.key === 'Enter') && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        sendMessage();
      }
      // Enter単体は改行（inputなら無視、textareaなら改行）
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
        
        {/* 開発環境用Sentryテストパネル */}
        {process.env.NODE_ENV === 'development' && <SentryTestComponent />}
        
        {/* チャット画面 */}
        <div className="flex flex-col h-[calc(100vh-4rem)]">
          {/* メッセージ履歴 */}
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
          
          {/* 入力エリア */}
          <div className="border-t p-4" data-testid="chat-input-area">
            <div className="max-w-3xl mx-auto">
              {/* 送信モード選択UI */}
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
