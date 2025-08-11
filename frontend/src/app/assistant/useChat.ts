"use client";
import { useState, useEffect, useCallback, useMemo } from "react";
import type { Message } from "../../types/chat";
import type { RagResponse } from "../../types/rag";
import { useChatHistory } from "../../hooks/useChatHistory";

// reCAPTCHAが無効かどうかを判定するヘルパー関数
const isRecaptchaDisabled = () => {
  return (
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA === "true" ||
    process.env.NEXT_PUBLIC_ENVIRONMENT === "test" ||
    !process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY
  );
};

// window.grecaptcha型定義を追加
interface WindowWithRecaptcha extends Window {
  grecaptcha?: {
    execute(siteKey: string, options: { action: string }): Promise<string>;
  };
  firebaseAuth?: {
    currentUser?: {
      getIdToken(): Promise<string>;
    };
  };
}

declare const window: WindowWithRecaptcha;

export const useChat = () => {
  // チャット履歴管理フックの統合
  const {
    activeSessionId,
    activeSession,
    updateSessionMessages,
    updateChatTitle,
    createNewChat,
    switchToChat,
  } = useChatHistory();

  // 現在のセッションのメッセージを取得（useMemoで最適化）
  const messages = useMemo(() => {
    const sessionMessages = activeSession?.messages || [];
    console.log('[useChat] Messages computed:', {
      activeSessionId,
      sessionMessagesCount: sessionMessages.length,
      activeSession: !!activeSession
    });
    return sessionMessages;
  }, [activeSession, activeSessionId]);
  
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recaptchaReady, setRecaptchaReady] = useState(false);
  const [sendMode, setSendMode] = useState<"enter" | "mod+enter">("enter");

  // セッション変更時の入力フィールドクリア
  useEffect(() => {
    setInput("");
  }, [activeSessionId]);

  // メッセージ更新時にセッションに同期
  const setMessages = useCallback((newMessages: Message[] | ((prev: Message[]) => Message[])) => {
    console.log('[useChat] setMessages called:', {
      activeSessionId,
      hasActiveSession: !!activeSession,
      messagesType: typeof newMessages
    });
    
    if (!activeSessionId) {
      console.warn('[useChat] No active session, cannot set messages');
      return;
    }
    
    const updatedMessages = typeof newMessages === 'function' 
      ? newMessages(messages) 
      : newMessages;
    
    console.log('[useChat] Updating messages:', {
      previousCount: messages.length,
      newCount: updatedMessages.length
    });
    
    // Message型からuseChatHistoryが期待する型に変換
    const convertedMessages = updatedMessages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));
    
    updateSessionMessages(activeSessionId, convertedMessages);
    
    // 最初のユーザーメッセージの場合、タイトルを自動生成
    if (updatedMessages.length === 1 && updatedMessages[0].role === 'user' && activeSession) {
      const firstMessage = updatedMessages[0].content;
      if (firstMessage.trim() && activeSession.title.startsWith('新しいチャット')) {
        // タイトル自動生成（generateSmartTitleは既にtime-format.tsに実装済み）
        import('../../utils/time-format').then(({ generateSmartTitle }) => {
          const newTitle = generateSmartTitle(firstMessage);
          console.log('[useChat] Auto-generating title:', newTitle);
          updateChatTitle(activeSessionId, newTitle);
        });
      }
    }
  }, [activeSessionId, messages, updateSessionMessages, updateChatTitle, activeSession]);

  // 送信モードの初期化
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("chat-send-mode");
      if (saved === "enter" || saved === "mod+enter") {
        setSendMode(saved);
      }
    }
  }, []);

  // 送信モードの保存
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("chat-send-mode", sendMode);
    }
  }, [sendMode]);

  // reCAPTCHAスクリプトの動的ロード
  useEffect(() => {
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

  // メッセージ送信ロジック
  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMessage: Message = { 
      id: `user_${Date.now()}`,
      role: "user", 
      content: input.trim() 
    };
    setLoading(true);
    setInput("");

    console.log(`[useChat] ユーザーメッセージ送信前のメッセージ数: ${messages.length}`);
    
    // 「サンプル出力」ならCardListを表示する特殊メッセージを追加
    if (input.trim() === "サンプル出力") {
      console.log(`[useChat] サンプル出力モード`);
      setMessages(prev => {
        const sampleMessage: Message = { 
          id: `assistant_sample_${Date.now()}`,
          role: "assistant", 
          content: "__show_sample_cards__" 
        };
        const newMessages = [...prev, userMessage, sampleMessage];
        console.log(`[useChat] サンプル出力後のメッセージ数: ${newMessages.length}`);
        return newMessages;
      });
      setLoading(false);
      return;
    }

    console.log(`[useChat] 通常メッセージ送信`);
    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      console.log(`[useChat] ユーザーメッセージ追加後: ${newMessages.length}件`);
      return newMessages;
    });

    const apiUrl = process.env.NEXT_PUBLIC_API_URL 
      ? `${process.env.NEXT_PUBLIC_API_URL}/api/rag/query`
      : "/api/rag/query";

    try {
      let idToken = "";
      if (typeof window !== "undefined" && window.firebaseAuth && window.firebaseAuth.currentUser) {
        try {
          idToken = await window.firebaseAuth.currentUser.getIdToken();
        } catch (error) {
          console.warn("Failed to get auth token:", error);
        }
      }
      
      let recaptchaToken = "";
      if (isRecaptchaDisabled()) {
        recaptchaToken = "test";
      } else if (typeof window !== "undefined" && window.grecaptcha && recaptchaReady) {
        try {
          recaptchaToken = await window.grecaptcha.execute(
            process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || '',
            { action: "submit" }
          );
        } catch (recaptchaError) {
          // reCAPTCHAエラー時の処理
          const errorMessage = recaptchaError instanceof Error ? recaptchaError.message : "reCAPTCHAの処理中にエラーが発生しました";
          const assistantMessage: Message = { 
            id: `assistant_recaptcha_error_${Date.now()}`,
            role: "assistant", 
            content: errorMessage 
          };
          setMessages(prev => [...prev, assistantMessage]);
          setLoading(false);
          return;
        }
      } else if (!isRecaptchaDisabled()) {
        // reCAPTCHAが有効なのに準備ができていない場合
        const assistantMessage: Message = { 
          id: `assistant_recaptcha_notready_${Date.now()}`,
          role: "assistant", 
          content: "reCAPTCHA未準備" 
        };
        setMessages(prev => [...prev, assistantMessage]);
        setLoading(false);
        return;
      }
      
      const res = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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
        const errorData = await res.json().catch(() => ({ error: { message: `HTTP error! status: ${res.status}` } }));
        throw new Error(errorData.error?.message || `APIエラーが発生しました (ステータス: ${res.status})`);
      }
      
      const data: RagResponse = await res.json();
      if (data.error) {
        throw new Error(data.error.message || "APIエラーが発生しました");
      }
      
      // 正常な応答の場合、answerを使ってassistantメッセージを追加
      const assistantMessage: Message = { 
        id: `assistant_${Date.now()}`,
        role: "assistant", 
        content: data.answer || "応答を受け取りました。",
        cardContext: Array.isArray(data.context) && typeof data.context[0] === "object" ? data.context : undefined
      };
      
      console.log(`[useChat] API応答受信 - cardContext: ${assistantMessage.cardContext?.length || 0}件`);
      
      setMessages(prev => {
        const newMessages = [...prev, assistantMessage];
        console.log(`[useChat] API応答後のメッセージ数: ${newMessages.length}`);
        newMessages.forEach((msg, idx) => {
          console.log(`[useChat] メッセージ${idx}: role=${msg.role}, cardContext=${msg.cardContext?.length || 0}件`);
        });
        return newMessages;
      });
    } catch (error) {
      // APIエラー時の処理
      console.error(error);
      
      let errorMessage = "申し訳ありませんが、エラーが発生しました。";
      if (error instanceof Error) {
        // 認証エラーの特別な処理
        if (error.message.includes("Invalid authentication credentials") || 
            error.message.includes("認証エラー") ||
            error.message.includes("authentication") ||
            error.message.includes("認証に失敗しました")) {
          errorMessage = "認証に失敗しました。再度ログインしてお試しください。";
        } else {
          errorMessage = `申し訳ありませんが、エラーが発生しました: ${error.message}`;
        }
      }
      
      const assistantMessage: Message = { 
        id: `assistant_error_${Date.now()}`,
        role: "assistant", 
        content: errorMessage 
      };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, recaptchaReady, messages.length, setMessages]);

  // チャット履歴をクリアする関数（現在のセッションのメッセージをクリア）
  const clearHistory = useCallback(() => {
    if (activeSessionId) {
      setMessages([]);
    }
  }, [activeSessionId, setMessages]);

  // 新しいチャットを作成して自動的に切り替え
  const createNewChatAndSwitch = useCallback(() => {
    const newSessionId = createNewChat();
    // 入力フィールドもクリア
    setInput("");
    return newSessionId;
  }, [createNewChat]);

  // チャットセッションを切り替え
  const switchToChatAndClear = useCallback((sessionId: string) => {
    switchToChat(sessionId);
    // 入力フィールドをクリア
    setInput("");
  }, [switchToChat]);

  return {
    messages,
    input,
    setInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
    recaptchaReady,
    setRecaptchaReady,
    clearHistory,
    // チャット履歴管理機能を公開
    activeSessionId,
    activeSession,
    // セッション操作機能
    createNewChatAndSwitch,
    switchToChatAndClear
  };
};
