/**
 * チャット履歴管理のためのカスタムフック
 * 複数のチャットセッションを管理し、LocalStorageと同期する
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
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
  const safeRandomId = useCallback((): string => {
    try {
      if (typeof crypto !== 'undefined' && crypto && typeof (crypto as { randomUUID?: () => string }).randomUUID === 'function') {
        return (crypto as { randomUUID: () => string }).randomUUID();
      }
    } catch {}
    // フォールバック
    return `id_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  }, []);
  // SSRセーフな初期化
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);
  // 初回ロード完了フラグ（保存副作用の暴発防止）
  const hasLoadedRef = useRef(false);
  // 直近保存スナップショット（無変化保存を回避）
  const lastSavedSnapshotRef = useRef<string | null>(null);

  const buildSnapshot = useCallback((s: ChatSession[], activeId: string | null) => {
    try {
      return JSON.stringify({
        activeId,
        sessions: s.map(sess => ({
          id: sess.id,
          title: sess.title,
          updatedAt: sess.updatedAt instanceof Date ? sess.updatedAt.toISOString() : String(sess.updatedAt),
          createdAt: sess.createdAt instanceof Date ? sess.createdAt.toISOString() : String(sess.createdAt),
          isActive: sess.isActive,
          messages: sess.messages.map(m => ({ id: m.id, role: m.role, content: m.content }))
        }))
      });
    } catch {
      return '';
    }
  }, []);

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
    console.log('[useChatHistory] Window check:', typeof window !== 'undefined');
    
    setIsClient(true);
    
    try {
      console.log('[useChatHistory] Loading chat history state...');
      const state = loadChatHistoryState();
      console.log('[useChatHistory] Loaded state:', {
        sessionsCount: state.sessions.length,
        activeSessionId: state.activeSessionId,
        state: state
      });
      
  // ロードした状態をそのまま設定（空でも自動作成はしない）
      setSessions(state.sessions);
      setActiveSessionId(state.activeSessionId);
  // 初期ロード完了をマーク
  hasLoadedRef.current = true;
  // 現在のスナップショットを記録（初回保存の重複を避ける）
  lastSavedSnapshotRef.current = buildSnapshot(state.sessions, state.activeSessionId);
      
      console.log('[useChatHistory] State updated successfully');
      console.log('[useChatHistory] Final state after initialization:', {
        sessionsCount: state.sessions.length,
        activeSessionId: state.activeSessionId
      });
    } catch (err) {
      console.error('[useChatHistory] Initialization error:', err);
      setError(err instanceof Error ? err.message : 'Initialization failed');
    } finally {
      console.log('[useChatHistory] Setting isLoading to false');
      setIsLoading(false);
    }
  }, [buildSnapshot]); // 初期化時に一度（buildSnapshotは安定）

  // 他インスタンスからの更新を購読して状態を再読み込み
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      try {
        const state = loadChatHistoryState();
        const incomingSnapshot = buildSnapshot(state.sessions, state.activeSessionId);
        const currentSnapshot = buildSnapshot(sessions, activeSessionId);
        if (incomingSnapshot === currentSnapshot) {
          // 変化なしなら無視
          return;
        }
        // 再読み込み時も保存副作用を走らせたいので hasLoadedRef を維持
        setSessions(state.sessions);
        setActiveSessionId(state.activeSessionId);
      } catch (e) {
        console.warn('[useChatHistory] Failed to refresh on external update', e);
      }
    };
    window.addEventListener('chat-history:updated', handler as EventListener);
    return () => window.removeEventListener('chat-history:updated', handler as EventListener);
  }, [sessions, activeSessionId, buildSnapshot]);

  // セッションが変更されたときの保存処理
  useEffect(() => {
    // 初回ロードが完了するまで保存はスキップ（空配列で上書きしない）
    if (!hasLoadedRef.current) {
      console.log('[useChatHistory] Skip saving before initial load completes');
      return;
    }
    if (typeof window !== 'undefined' && sessions.length >= 0) {
      const currentSnapshot = buildSnapshot(sessions, activeSessionId);
      if (lastSavedSnapshotRef.current === currentSnapshot) {
        // 無変化なら保存しない
        return;
      }
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
        lastSavedSnapshotRef.current = currentSnapshot;
      } catch (err) {
        console.error('[useChatHistory] Failed to save state:', err);
        setError(err instanceof Error ? err.message : 'Failed to save state');
      }
    }
  }, [sessions, activeSessionId, buildSnapshot]);

  // 新しいチャットを作成
  const createNewChat = useCallback((): string => {
    console.log('[useChatHistory] Creating new chat...');
    console.log('[useChatHistory] Current sessions before creation:', sessions.length);
    console.log('[useChatHistory] Current activeSessionId before creation:', activeSessionId);
    
    const newSession: ChatSession = {
      id: safeRandomId(),
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

    // 新しいセッションをリストの先頭に追加
    setSessions(prev => {
      const updatedSessions = [newSession, ...prev];
      console.log('[useChatHistory] Sessions after adding new chat:', updatedSessions.length);
      return updatedSessions;
    });
    
    // 新しいセッションをアクティブにする
    setActiveSessionId(newSession.id);
    console.log('[useChatHistory] Setting activeSessionId to:', newSession.id);
    
    // エラーをクリア
    setError(null);
    
    return newSession.id;
  }, [sessions.length, activeSessionId, safeRandomId]);

  // チャットを切り替え
  const switchToChat = useCallback((sessionId: string) => {
    console.log('[useChatHistory] Switching to chat:', sessionId);
    console.log('[useChatHistory] Available sessions:', sessions.map(s => ({ id: s.id, title: s.title })));
    
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      console.log('[useChatHistory] Found session:', {
        id: session.id,
        title: session.title,
        messageCount: session.messages.length
      });
      
      // アクティブセッションを切り替え
      setActiveSessionId(sessionId);
      console.log('[useChatHistory] ActiveSessionId updated to:', sessionId);
      
      // エラーをクリア
      setError(null);
    } else {
      console.warn('[useChatHistory] Session not found:', sessionId);
      console.log('[useChatHistory] Available sessions:', sessions.map(s => s.id));
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
              messages: [...session.messages, { ...message, id: safeRandomId() }],
              updatedAt: new Date()
            }
          : session
      )
    );
  }, [safeRandomId]);

  // セッションのメッセージを一括更新
  const updateSessionMessages = useCallback((sessionId: string, messages: Array<{ id?: string; role: 'user' | 'assistant'; content: string; cardContext?: import("../types/rag").RagContextItem[] }>) => {
    console.log('[useChatHistory] Updating session messages:', { sessionId, messageCount: messages.length });
    
    setSessions(prev => 
      prev.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              messages: messages.map(msg => ({ 
                ...msg, 
                id: msg.id || safeRandomId() // 既存のIDを保持、無い場合は生成
              })),
              updatedAt: new Date()
            }
          : session
      )
    );
  }, [safeRandomId]);

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

// デフォルトエクスポートも追加
export default useChatHistory;
