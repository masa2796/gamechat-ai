import { useState, useEffect, useCallback } from "react";
import { captureAPIError, captureUserAction, setSentryTag } from "@/lib/sentry";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export type SendMode = 'enter' | 'mod+enter';

const isRecaptchaDisabled = () => {
  return (
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA === "true" ||
    process.env.NEXT_PUBLIC_ENVIRONMENT === "test" ||
    !process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY
  );
};

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recaptchaReady, setRecaptchaReady] = useState(false);
  const [sendMode, setSendMode] = useState<SendMode>('enter');

  // Sentry設定
  useEffect(() => {
    setSentryTag("component", "assistant");
    setSentryTag("environment", process.env.NEXT_PUBLIC_ENVIRONMENT || "development");
  }, []);

  // 送信モード初期化
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

  // reCAPTCHA読み込み
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
    setLoading(true);
    setInput("");
    setMessages(prev => [...prev, userMessage]);
    captureUserAction("message_sent", { messageLength: input.length });

    const apiUrl = process.env.NEXT_PUBLIC_API_URL
      ? `${process.env.NEXT_PUBLIC_API_URL}/api/rag/query`
      : "/api/rag/query";

    let idToken = "";
    if (typeof window !== "undefined" && window.firebaseAuth?.currentUser) {
      try {
        idToken = await window.firebaseAuth.currentUser.getIdToken();
      } catch (error) {
        console.warn("Failed to get auth token:", error);
      }
    }

    let recaptchaToken = "";
    try {
      if (isRecaptchaDisabled()) {
        recaptchaToken = "test";
      } else if (typeof window !== "undefined" && window.grecaptcha && recaptchaReady) {
        recaptchaToken = await window.grecaptcha.execute(
          process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || '',
          { action: "submit" }
        );
      } else {
        throw new Error("reCAPTCHA未準備");
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error("reCAPTCHA取得失敗");
      // 必ず reCAPTCHA取得失敗 を含むメッセージにする
      let displayMessage = "reCAPTCHA取得失敗";
      if (err.message && err.message !== "reCAPTCHA取得失敗") {
        displayMessage += `: ${err.message}`;
      }
      captureAPIError(err, {
        endpoint: apiUrl,
        userMessage: userMessage.content,
        timestamp: new Date().toISOString()
      });
      setMessages(prev => [...prev, { role: "assistant", content: displayMessage }]);
      setLoading(false);
      return;
    }

    try {
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
          recaptchaToken
        }),
        credentials: "include"
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ error: { message: `HTTP error! status: ${res.status}` } }));
        throw new Error(errorData.error?.message || `APIエラーが発生しました (ステータス: ${res.status})`);
      }

      const data = await res.json();
      if (data.error) throw new Error(data.error.message || "APIエラーが発生しました");

      // answerフィールドは利用せず、context配列の有無でUI側がCardList等を表示する
      // ここではassistantメッセージ自体は追加しない（CardList表示はUI側で制御）
    } catch (error) {
      const err = error instanceof Error ? error : new Error("APIエラー");
      console.error("Error:", err);

      let displayMessage = "エラーが発生しました。もう一度お試しください。";
      if (err.message.includes("Invalid authentication credentials") || err.message.includes("401")) {
        displayMessage = "認証に失敗しました。APIキーの設定を確認してください。";
      } else {
        displayMessage = err.message;
      }

      captureAPIError(err, {
        endpoint: apiUrl,
        userMessage: userMessage.content,
        timestamp: new Date().toISOString()
      });

      setMessages(prev => [...prev, { role: "assistant", content: displayMessage }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, recaptchaReady]);

  return {
    messages,
    setMessages,
    input,
    setInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
    recaptchaReady,
    setRecaptchaReady
  };
};

// window 型拡張
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
