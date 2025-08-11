/**
 * チャット履歴管理のためのカスタムフック
 * 複数のチャットセッションを管理し、LocalStorageと同期する
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  saveChatHistoryState,
  loadChatHistoryState
} from '@/utils/chat-storage'
import { ChatSession } from '@/types/chat'

// フック戻り値の型定義
export interface UseChatHistoryReturn {
  sessions: ChatSession[]
  activeSessionId: string | null
  activeSession: ChatSession | null
  isLoading: boolean
  error: string | null
  createNewChat: () => string
  switchToChat: (sessionId: string) => void
  deleteChat: (sessionId: string) => Promise<void>
  updateChatTitle: (sessionId: string, title: string) => void
  addMessageToChat: (sessionId: string, message: { role: 'user' | 'assistant', content: string }) => void
  updateSessionMessages: (sessionId: string, messages: { role: 'user' | 'assistant', content: string }[]) => void
}

/**
 * チャット履歴管理のカスタムフック
 */
export function useChatHistory(): UseChatHistoryReturn {
  // SSRセーフな初期化
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);

  // 現在のアクティブセッションを計算
  const activeSession = useMemo(() => {
    return sessions.find(session => session.id === activeSessionId) || null;
  }, [sessions, activeSessionId]);

  // デバッグ情報
  console.log('[useChatHistory] Hook initialized with state:', {
    sessionsCount: sessions.length,
    activeSessionId,
    isLoading,
    error,
    isClient,
    timestamp: new Date().toISOString()
  });

  // クライアントサイドマウント後の初期化
  useEffect(() => {
    console.log('[useChatHistory] Client-side initialization starting...');
    setIsClient(true);
    
    try {
      const state = loadChatHistoryState();
      console.log('[useChatHistory] Loaded state:', {
        sessionsCount: state.sessions.length,
        activeSessionId: state.activeSessionId
      });
      
      setSessions(state.sessions);
      setActiveSessionId(state.activeSessionId);
    } catch (err) {
      console.error('[useChatHistory] Initialization error:', err);
      setError(err instanceof Error ? err.message : 'Initialization failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // セッションが変更されたときの保存処理
  useEffect(() => {
    if (typeof window !== 'undefined' && sessions.length >= 0) {
      console.log('[useChatHistory] Saving sessions to localStorage:', {
        sessionsCount: sessions.length,
        activeSessionId
      });
      
      try {
        saveChatHistoryState({ 
          sessions, 
          activeSessionId,
          maxSessions: 50 // STORAGE_LIMITS.MAX_SESSIONSの値
        });
      } catch (err) {
        console.error('[useChatHistory] Failed to save state:', err);
        setError(err instanceof Error ? err.message : 'Failed to save state');
      }
    }
  }, [sessions, activeSessionId]);

  // 新しいチャットを作成
  const createNewChat = useCallback((): string => {
    console.log('[useChatHistory] Creating new chat...');
    
    const newSession: ChatSession = {
      id: crypto.randomUUID(),
      title: '新しいチャット',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      isActive: false
    };

    console.log('[useChatHistory] Created new session:', {
      id: newSession.id,
      title: newSession.title
    });

    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    
    return newSession.id;
  }, []);

  // チャットを切り替え
  const switchToChat = useCallback((sessionId: string) => {
    console.log('[useChatHistory] Switching to chat:', sessionId);
    
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setActiveSessionId(sessionId);
    } else {
      console.warn('[useChatHistory] Session not found:', sessionId);
      setError(`セッション ${sessionId} が見つかりません`);
    }
  }, [sessions]);

  // チャットを削除
  const deleteChat = useCallback(async (sessionId: string): Promise<void> => {
    console.log('[useChatHistory] Deleting chat:', sessionId);
    
    try {
      // セッション一覧から削除
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // アクティブセッションが削除されたら null に設定
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
      }
      
      console.log('[useChatHistory] Chat deleted successfully:', sessionId);
    } catch (err) {
      console.error('[useChatHistory] Failed to delete chat:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete chat');
      throw err;
    }
  }, [activeSessionId]);

  // チャットのタイトルを更新
  const updateChatTitle = useCallback((sessionId: string, title: string) => {
    console.log('[useChatHistory] Updating chat title:', { sessionId, title });
    
    setSessions(prev => 
      prev.map(session => 
        session.id === sessionId 
          ? { ...session, title, updatedAt: new Date() }
          : session
      )
    );
  }, []);

  // チャットにメッセージを追加
  const addMessageToChat = useCallback((sessionId: string, message: { role: 'user' | 'assistant', content: string }) => {
    console.log('[useChatHistory] Adding message to chat:', { sessionId, role: message.role });
    
    setSessions(prev => 
      prev.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              messages: [...session.messages, { ...message, id: crypto.randomUUID() }],
              updatedAt: new Date()
            }
          : session
      )
    );
  }, []);

  // セッションのメッセージを一括更新
  const updateSessionMessages = useCallback((sessionId: string, messages: { role: 'user' | 'assistant', content: string }[]) => {
    console.log('[useChatHistory] Updating session messages:', { sessionId, messageCount: messages.length });
    
    setSessions(prev => 
      prev.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              messages: messages.map(msg => ({ ...msg, id: crypto.randomUUID() })),
              updatedAt: new Date()
            }
          : session
      )
    );
  }, []);

  return {
    sessions,
    activeSessionId,
    activeSession,
    isLoading,
    error,
    createNewChat,
    switchToChat,
    deleteChat,
    updateChatTitle,
    addMessageToChat,
    updateSessionMessages
  };
}
