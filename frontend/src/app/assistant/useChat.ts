"use client";
// MVP版: セッション・reCAPTCHA・履歴管理を除去した極小実装
import { useState, useCallback, useRef } from "react";
import type { Message, UseChatReturn } from "../../types/chat";
import type { RagResponse } from "../../types/rag";

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sendMode, setSendMode] = useState<"enter" | "mod+enter">("enter");
  const inputRef = useRef("");
  const updateInput = useCallback((v: string) => { setInput(v); inputRef.current = v; }, []);

  // メッセージ送信ロジック
  const sendMessage = useCallback(async () => {
    const current = (inputRef.current || input).trim();
    if (!current || loading) return;
    const userMessage: Message = { id: `user_${Date.now()}`, role: "user", content: current };
    setLoading(true);
    updateInput("");
    setMessages(prev => [...prev, userMessage]);
    const base = process.env.NEXT_PUBLIC_API_URL || "";
    const mvpMode = process.env.NEXT_PUBLIC_MVP_MODE === 'true';
    const apiUrl = mvpMode ? `${base}/chat` : `${base}/api/rag/query`;

    try {
      const res = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
        },
        body: JSON.stringify(mvpMode ? {
          message: userMessage.content,
          top_k: 5,
          with_context: true
        } : { question: userMessage.content, top_k: 5, with_context: true }),
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
        content: (data as any).answer || data.answer || "応答を受け取りました。",
        cardContext: Array.isArray((data as any).context) && typeof (data as any).context[0] === "object" ? (data as any).context : (Array.isArray(data.context) ? data.context : undefined)
      };
      
      console.log(`[useChat] API応答受信 - cardContext: ${assistantMessage.cardContext?.length || 0}件`);
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);
      const msg = error instanceof Error ? error.message : "エラーが発生しました";
      setMessages(prev => [...prev, { id: `err_${Date.now()}`, role: "assistant", content: `エラー: ${msg}` }]);
    } finally {
      setLoading(false);
    }
  }, [loading, input, updateInput]);

  const clearHistory = useCallback(() => { setMessages([]); }, []);

  return {
    messages,
    input,
    setInput: updateInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
    recaptchaReady: true,
    setRecaptchaReady: () => {},
    clearHistory,
    activeSessionId: null,
    activeSession: null,
    createNewChatAndSwitch: () => "",
    switchToChatAndClear: () => {}
  };
};
