import { useState, useEffect, useCallback } from "react";
import { auth as firebaseAuth } from "@/lib/firebase";
import { captureAPIError, captureUserAction, setSentryTag } from "@/lib/sentry";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

const isRecaptchaDisabled = () => {
  return (
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA === "true" ||
    process.env.NEXT_PUBLIC_ENVIRONMENT === "test" ||
    !process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY
  );
};

export type SendMode = 'enter' | 'mod+enter';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recaptchaReady, setRecaptchaReady] = useState(false);
  const [sendMode, setSendMode] = useState<SendMode>('enter');

  // Sentryタグ設定
  useEffect(() => {
    setSentryTag("component", "assistant");
    setSentryTag("environment", process.env.NEXT_PUBLIC_ENVIRONMENT || "development");
  }, []);

  // 送信モードの初期化
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('chat-send-mode');
      if (saved === 'enter' || saved === 'mod+enter') {
        setSendMode(saved);
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chat-send-mode', sendMode);
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

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMessage: Message = { role: "user", content: input.trim() };
    captureUserAction("message_sent", { messageLength: input.length });
    setLoading(true);
    setInput("");
    setMessages(prev => [...prev, userMessage]);
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
        recaptchaToken = "test";
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
  }, [input, loading, recaptchaReady, sendMode]);

  return {
    messages,
    setMessages,
    input,
    setInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
    recaptchaReady
  };
};
