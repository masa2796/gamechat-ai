"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { Message, UseChatReturn } from "../../types/chat";
import type { RagResponse } from "../../types/rag";
import { useChatHistory } from "@/hooks/useChatHistory";

export const useChat = (): UseChatReturn => {
  // ローカル状態（表示用・リアルタイム更新）
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sendMode, setSendMode] = useState<"enter" | "mod+enter">("enter");
  const [recaptchaReady, setRecaptchaReady] = useState(true); // MVP では常に true

  // チャット履歴の有効/無効（テスト環境では無効化して副作用を避ける）
  const isTestEnv = process.env.NEXT_PUBLIC_ENVIRONMENT === 'test' || process.env.NODE_ENV === 'test';
  const historyEnabled = !isTestEnv;
  
  // チャット履歴管理フック
  const chatHistoryHook = useChatHistory();
  
  console.log('[useChat] useChatHistory hook result:', {
    keys: Object.keys(chatHistoryHook),
    updateChatTitle: typeof chatHistoryHook.updateChatTitle,
    hasUpdateChatTitle: 'updateChatTitle' in chatHistoryHook
  });
  
  const { 
    sessions, 
    activeSessionId, 
    activeSession,
    createNewChat,
    switchToChat,
    updateChatTitle,
    updateSessionMessages
  } = chatHistoryHook;

  console.log('[useChat] チャット履歴フック状態:', {
    sessionsCount: sessions.length,
    activeSessionId,
    historyEnabled,
    isTestEnv
  });

  // 最後の更新ソースを追跡（無限ループ防止）
  const lastUpdateSource = useRef<'user' | 'session' | null>(null);

  // 統一的なsetMessages関数（履歴を更新し、ローカル状態も同期）
  const setMessages = useCallback((messages: Message[] | ((prev: Message[]) => Message[])) => {
    console.log('[useChat] setMessages called with:', typeof messages === 'function' ? 'function' : messages);
    
    const newMessages = typeof messages === 'function' ? messages(localMessages) : messages;
    console.log('[useChat] Computed new messages:', newMessages.length);
    
    // ローカル状態を更新
    lastUpdateSource.current = 'user';
    setLocalMessages(newMessages);
    
    // アクティブセッションがあれば履歴も更新
    if (historyEnabled && activeSessionId && updateSessionMessages) {
      console.log('[useChat] Updating session messages for:', activeSessionId);
      updateSessionMessages(activeSessionId, newMessages);
    }
  }, [localMessages, historyEnabled, activeSessionId, updateSessionMessages]);

  // input setter wrapper（副作用の統一化）
  const setInputWrapper = useCallback((value: string) => {
    setInput(value);
  }, []);

  // アクティブセッションが変更されたときのメッセージ同期
  useEffect(() => {
    // 履歴無効時は何もしない
    if (!historyEnabled) {
      console.log('[useChat] History disabled, skipping session sync');
      return;
    }

    // セッション起点の更新（ユーザー起点の更新と区別）
    if (lastUpdateSource.current === 'session') {
      console.log('[useChat] Skipping session sync - update source is session');
      return;
    }

    const target = activeSession;
    console.log('[useChat] Active session changed:', {
      activeSessionId,
      targetSessionExists: !!target,
      targetMessageCount: target?.messages.length || 0,
      currentLocalMessageCount: localMessages.length
    });

    // セッション起点の反映であることを明確化
    lastUpdateSource.current = 'session';
    setLocalMessages(target?.messages ?? []);
    
    console.log('[useChat] Messages synced from session');
  }, [activeSession, activeSessionId, historyEnabled, localMessages.length]);

  // メッセージ送信処理
  const sendMessage = useCallback(async () => {
    const currentInput = input.trim();
    if (!currentInput || loading) {
      console.log('[useChat] Send aborted:', { currentInput, loading });
      return;
    }

    console.log(`[useChat] ユーザーメッセージ送信前のメッセージ数: ${localMessages.length}`);

    // 最初の送信時にセッションがなければ作成（履歴が有効な場合のみ）
    let sessionId = activeSessionId;
    if (historyEnabled) {
      if (!sessionId) {
        sessionId = createNewChat();
        console.log('[useChat] セッション未作成のため新規作成:', sessionId);
      }
    }
    
    // 「サンプル出力」ならCardListを表示する特殊メッセージを追加
    if (currentInput === "サンプル出力") {
      console.log(`[useChat] サンプル出力モード`);
      setMessages(prev => {
        const sampleMessage: Message = { 
          id: `assistant_sample_${Date.now()}`,
          role: "assistant", 
          content: "[カードリスト表示]",
          cardContext: [
            { 
              id: "sample1", 
              title: "サンプルカード1", 
              summary: "これはサンプルです", 
              score: 0.9,
              type: "card"
            },
            { 
              id: "sample2", 
              title: "サンプルカード2", 
              summary: "これもサンプルです", 
              score: 0.8,
              type: "card"
            }
          ]
        };
        return [...prev, sampleMessage];
      });
      setInput("");
      return;
    }

    const userMessage: Message = { 
      id: `user_${Date.now()}`, 
      role: "user", 
      content: currentInput 
    };

    setLoading(true);
    setInput("");
    setMessages(prev => [...prev, userMessage]);

    try {
      // API エンドポイントの設定
      const rawBase = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();
      const trimmedBase = rawBase.replace(/\/+$/, "");
      const base = trimmedBase.length > 0 ? trimmedBase : ""; // 未設定時は相対パス
      const mvpMode = process.env.NEXT_PUBLIC_MVP_MODE === "true";
      const endpoint = mvpMode ? "/chat" : "/api/rag/query";
      const apiUrl = `${base}${endpoint}`;

      const payload = mvpMode
        ? {
            message: userMessage.content,
            top_k: 5,
            with_context: true,
          }
        : {
            question: userMessage.content,
            top_k: 5,
            with_context: true,
          };

      const res = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
        },
        body: JSON.stringify(payload),
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
        cardContext: Array.isArray(data.context) && data.context.length > 0 && typeof data.context[0] === "object" 
          ? data.context 
          : undefined
      };
      
      console.log(`[%cuseChat%c] API応答 @${apiUrl} (context: ${assistantMessage.cardContext?.length || 0})`, "color:#2563eb;font-weight:bold", "color:inherit");
      
      setMessages(prev => [...prev, assistantMessage]);

      // タイトル更新（最初のメッセージの場合）
      if (historyEnabled && sessionId && localMessages.length === 0 && updateChatTitle) {
        const title = currentInput.length > 20 ? `${currentInput.slice(0, 20)}...` : currentInput;
        updateChatTitle(sessionId, title);
      }

    } catch (error) {
      console.error(error);
      const msg = error instanceof Error ? error.message : "エラーが発生しました";
      setMessages(prev => [...prev, { 
        id: `err_${Date.now()}`, 
        role: "assistant", 
        content: `エラー: ${msg}` 
      }]);
    } finally {
      setLoading(false);
    }
  }, [loading, localMessages.length, setMessages, activeSessionId, createNewChat, updateChatTitle, setInput, historyEnabled, input]);

  // チャット履歴をクリアする関数（現在のセッションのメッセージをクリア）
  const clearHistory = useCallback(() => {
    setMessages([]);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chat-history');
    }
  }, [setMessages]);

  // 新しいチャットを作成して自動的に切り替え
  const createNewChatAndSwitch = useCallback(() => {
    console.log('[useChat] Creating new chat and switching...');
    console.log('[useChat] Current messages before creation:', localMessages.length);
    
    try {
      const newSessionId = createNewChat();
      console.log('[useChat] New session created with ID:', newSessionId);
      
      // メッセージをクリア
      setMessages([]);
      
      // 入力フィールドをクリア
      setInput("");
      
      console.log('[useChat] New chat creation completed');
      
      return newSessionId;
    } catch (error) {
      console.error('[useChat] Error creating new chat:', error);
      return "";
    }
  }, [createNewChat, setMessages, localMessages.length]);

  // 指定されたチャットに切り替えてメッセージをクリア
  const switchToChatAndClear = useCallback((sessionId: string) => {
    console.log('[useChat] Switching to chat and clearing:', sessionId);
    console.log('[useChat] Available sessions:', sessions.map(s => ({ id: s.id, title: s.title })));
    
    try {
      const target = sessions.find(s => s.id === sessionId);
      if (!target) {
        console.warn('[useChat] Target session not found:', sessionId);
        return;
      }
      
      // チャットを切り替え
      switchToChat(sessionId);
      
      // セッション起点の反映であることを明確化
      lastUpdateSource.current = 'session';
      setLocalMessages(target?.messages ?? []);
      
      // 入力フィールドをクリア
      setInput("");
      
      console.log('[useChat] Chat session switch completed');
    } catch (error) {
      console.error('[useChat] Error switching to chat:', error);
    }
  }, [switchToChat, sessions, setInput]);

  return {
    messages: localMessages,  // ローカル状態のメッセージを返す
    input,
    setInput: setInputWrapper, // Updated to use the new setInput wrapper
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
