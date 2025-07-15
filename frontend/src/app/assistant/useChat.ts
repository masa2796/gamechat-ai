"use client";
import { useState, useEffect, useCallback } from "react";
import type { Message } from "../../types/chat";
import type { RagResponse } from "../../types/rag";

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recaptchaReady, setRecaptchaReady] = useState(false);
  const [sendMode, setSendMode] = useState<"enter" | "mod+enter">("enter");
  // context（カード詳細jsonリスト）を保持
  const [cardContext, setCardContext] = useState<import("../../types/rag").RagContextItem[] | undefined>(undefined);

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
    const userMessage: Message = { role: "user", content: input.trim() };
    setLoading(true);
    setInput("");

    // 「サンプル出力」ならCardListを表示する特殊メッセージを追加
    if (input.trim() === "サンプル出力") {
      setMessages(prev => [...prev, userMessage, { role: "assistant", content: "__show_sample_cards__" }]);
      setLoading(false);
      return;
    }

    setMessages(prev => [...prev, userMessage]);

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
      const data: RagResponse = await res.json();
      if (data.error) {
        throw new Error(data.error.message || "APIエラーが発生しました");
      }
      // context（カード詳細jsonリスト）をstateに格納
      setCardContext(data.context);
      // answerフィールドは利用せず、context配列の有無でUI側がCardList等を表示する
      // ここではassistantメッセージ自体は追加しない（CardList表示はUI側で制御）
    } catch (error) {
      let displayMessage = "エラーが発生しました。もう一度お試しください。";
      if (error instanceof Error) {
        if (
          error.message.includes("認証") ||
          error.message.includes("Invalid authentication credentials") ||
          error.message.includes("401")
        ) {
          displayMessage = "認証に失敗しました。APIキーの設定を確認してください。";
        } else {
          displayMessage = error.message;
        }
      }
      const errorMessage: Message = { 
        role: "assistant", 
        content: displayMessage
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, recaptchaReady]);

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
    cardContext,
    setCardContext
  };
};
