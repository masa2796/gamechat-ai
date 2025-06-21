"use client";

import { useState, useEffect } from "react";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Separator } from "@/components/ui/separator";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { ErrorBoundary } from "@/components/error-boundary";
import { SentryTestComponent } from "@/components/sentry-test";
import { getAuth } from "firebase/auth";
import { initializeApp } from "firebase/app";
import { captureAPIError, captureUserAction, setSentryTag } from "@/lib/sentry";

interface Message {
  role: "user" | "assistant";
  content: string;
}

// Firebase設定（環境変数から取得）
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

// Firebase初期化をクライアントサイドでのみ実行
let app: ReturnType<typeof initializeApp> | null = null;
let auth: ReturnType<typeof getAuth> | null = null;

// Firebase初期化の安全なチェック
const shouldInitializeFirebase = () => {
  if (typeof window === "undefined") return false; // サーバーサイドでは初期化しない
  if (process.env.CI) return false; // CI環境では初期化しない
  if (!firebaseConfig.apiKey || firebaseConfig.apiKey === "dummy-api-key-for-ci") return false;
  return true;
};

if (shouldInitializeFirebase()) {
  try {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
  } catch (error) {
    console.warn("Firebase initialization failed:", error);
  }
}

declare global {
  interface Window {
    grecaptcha?: {
      execute: (siteKey: string, options: { action: string }) => Promise<string>;
      ready: (callback: () => void) => void;
    };
  }
}

export const Assistant = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recaptchaReady, setRecaptchaReady] = useState(false);

  // reCAPTCHAスクリプトの動的ロード
  useEffect(() => {
    // Sentryタグを設定
    setSentryTag("component", "assistant");
    setSentryTag("environment", process.env.NEXT_PUBLIC_ENVIRONMENT || "development");
    
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
    
    const userMessage: Message = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    
    // Sentryにユーザーアクションを記録
    captureUserAction("message_sent", { messageLength: input.length });
    
    setInput("");
    setLoading(true);

    try {
      let idToken = "";
      if (auth && auth.currentUser) {
        try {
          idToken = await auth.currentUser.getIdToken();
        } catch (error) {
          console.warn("Failed to get auth token:", error);
        }
      }
      let recaptchaToken = "";
      // reCAPTCHA認証をスキップするかチェック
      if (process.env.NEXT_PUBLIC_SKIP_RECAPTCHA === "true") {
        recaptchaToken = "test"; // バックエンドでテストトークンとして認識される
        console.log("reCAPTCHA verification skipped due to NEXT_PUBLIC_SKIP_RECAPTCHA=true");
      } else if (window.grecaptcha && recaptchaReady) {
        recaptchaToken = await window.grecaptcha.execute(process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY, { action: "submit" });
      }
      const res = await fetch("/api/rag/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // APIキー認証ヘッダーを追加
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
          ...(idToken ? { Authorization: `Bearer ${idToken}` } : {})
        },
        body: JSON.stringify({ 
          question: input,
          top_k: 5,
          with_context: true,
          recaptchaToken
        }),
        credentials: "include"
      });
      
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
      
      // Sentryにエラーを報告
      captureAPIError(error as Error, {
        endpoint: "/api/rag/query",
        userMessage: userMessage.content,
        timestamp: new Date().toISOString()
      });
      
      const errorMessage: Message = { 
        role: "assistant", 
        content: "エラーが発生しました。もう一度お試しください。" 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ErrorBoundary>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger />
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
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <p>GameChat AIへようこそ！</p>
                <p>ゲームに関する質問をお気軽にどうぞ。</p>
              </div>
            ) : (
              <div className="space-y-4 max-w-3xl mx-auto">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] p-3 rounded-lg ${
                      msg.role === 'user' 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-900 p-3 rounded-lg">
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
          <div className="border-t p-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="ゲームについて質問してください..."
                  disabled={loading}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
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
