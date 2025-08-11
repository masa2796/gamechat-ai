/**
 * チャット履歴管理のためのカスタムフック
 * 複数のチャットセッションを管理し、LocalStorageとの同期を担当
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { ChatSession, ChatHistoryState, UseChatHistoryReturn, Message } from '@/types/chat';
import {
  loadChatHistoryState,
  saveChatHistoryState,
  detectOldChatHistory,
  migrateOldChatHistory,
  ChatStorageError,
  getStorageUsage
} from '@/utils/chat-storage';
import { generateDefaultTitle, generateSmartTitle } from '@/utils/time-format';

/**
 * チャット履歴管理フック
 */
export function useChatHistory(): UseChatHistoryReturn {
  // セッション状態管理
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * 初期データの読み込みとマイグレーション
   */
  useEffect(() => {
    const initializeHistory = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // SSRチェック - サーバーサイドでは何もしない
        if (typeof window === 'undefined') {
          setIsLoading(false);
          return;
        }

        // 旧形式のデータ検出とマイグレーション
        if (detectOldChatHistory()) {
          console.log('Detected old chat history, migrating...');
          const migratedSessions = migrateOldChatHistory();
          if (migratedSessions.length > 0) {
            setSessions(migratedSessions);
            setActiveSessionId(migratedSessions[0].id);
            
            // マイグレーション完了後にLocalStorageに保存
            const newState: ChatHistoryState = {
              sessions: migratedSessions,
              activeSessionId: migratedSessions[0].id,
              maxSessions: 50
            };
            saveChatHistoryState(newState);
            console.log('Migration completed successfully');
          }
        } else {
          // 既存データの読み込み
          const state = loadChatHistoryState();
          setSessions(state.sessions);
          setActiveSessionId(state.activeSessionId);
        }
      } catch (err) {
        console.error('Failed to initialize chat history:', err);
        const errorMessage = err instanceof ChatStorageError 
          ? err.message 
          : 'チャット履歴の初期化に失敗しました';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    initializeHistory();
  }, []);

  /**
   * 状態変更時のLocalStorage同期
   */
  useEffect(() => {
    // SSRチェック - サーバーサイドでは何もしない
    if (typeof window === 'undefined') {
      return;
    }

    if (!isLoading && sessions.length >= 0) {
      try {
        const state: ChatHistoryState = {
          sessions,
          activeSessionId,
          maxSessions: 50
        };
        saveChatHistoryState(state);
      } catch (err) {
        console.error('Failed to save chat history state:', err);
        if (err instanceof ChatStorageError) {
          setError(err.message);
        }
      }
    }
  }, [sessions, activeSessionId, isLoading]);

  /**
   * 新規チャット作成
   */
  const createNewChat = useCallback((initialMessage?: string): string => {
    try {
      const newSessionId = crypto.randomUUID();
      const now = new Date();
      
      // タイトル生成
      const title = initialMessage 
        ? generateSmartTitle(initialMessage)
        : generateDefaultTitle(now);

      const newSession: ChatSession = {
        id: newSessionId,
        title,
        messages: [],
        createdAt: now,
        updatedAt: now,
        isActive: true
      };

      // 他のセッションを非アクティブに
      setSessions(prevSessions => {
        const updatedSessions = prevSessions.map(session => ({
          ...session,
          isActive: false
        }));
        return [...updatedSessions, newSession];
      });

      setActiveSessionId(newSessionId);
      setError(null);

      console.log('Created new chat session:', newSessionId);
      return newSessionId;
    } catch (err) {
      console.error('Failed to create new chat:', err);
      setError('新しいチャットの作成に失敗しました');
      throw err;
    }
  }, []);

  /**
   * チャット切り替え
   */
  const switchToChat = useCallback((sessionId: string): void => {
    try {
      const targetSession = sessions.find(s => s.id === sessionId);
      if (!targetSession) {
        console.warn('Session not found:', sessionId);
        setError('指定されたチャットが見つかりません');
        return;
      }

      // 全セッションを非アクティブに設定し、対象セッションのみアクティブに
      setSessions(prevSessions => 
        prevSessions.map(session => ({
          ...session,
          isActive: session.id === sessionId
        }))
      );

      setActiveSessionId(sessionId);
      setError(null);

      console.log('Switched to chat session:', sessionId);
    } catch (err) {
      console.error('Failed to switch chat:', err);
      setError('チャットの切り替えに失敗しました');
    }
  }, [sessions]);

  /**
   * チャット削除
   */
  const deleteChat = useCallback((sessionId: string): void => {
    try {
      const sessionToDelete = sessions.find(s => s.id === sessionId);
      if (!sessionToDelete) {
        console.warn('Session not found for deletion:', sessionId);
        return;
      }

      const remainingSessions = sessions.filter(s => s.id !== sessionId);
      
      // 削除されたセッションがアクティブだった場合
      if (activeSessionId === sessionId) {
        if (remainingSessions.length > 0) {
          // 最新のセッションをアクティブに
          const latestSession = remainingSessions.reduce((latest, current) => 
            new Date(current.updatedAt) > new Date(latest.updatedAt) ? current : latest
          );
          
          setSessions(remainingSessions.map(session => ({
            ...session,
            isActive: session.id === latestSession.id
          })));
          setActiveSessionId(latestSession.id);
        } else {
          // 全てのセッションが削除された場合
          setSessions([]);
          setActiveSessionId(null);
        }
      } else {
        setSessions(remainingSessions);
      }

      setError(null);
      console.log('Deleted chat session:', sessionId);
    } catch (err) {
      console.error('Failed to delete chat:', err);
      setError('チャットの削除に失敗しました');
    }
  }, [sessions, activeSessionId]);

  /**
   * チャットタイトル更新
   */
  const updateChatTitle = useCallback((sessionId: string, newTitle: string): void => {
    try {
      if (!newTitle.trim()) {
        setError('タイトルを入力してください');
        return;
      }

      setSessions(prevSessions => 
        prevSessions.map(session => 
          session.id === sessionId 
            ? { ...session, title: newTitle.trim(), updatedAt: new Date() }
            : session
        )
      );

      setError(null);
      console.log('Updated chat title:', sessionId, newTitle);
    } catch (err) {
      console.error('Failed to update chat title:', err);
      setError('タイトルの更新に失敗しました');
    }
  }, []);

  /**
   * セッションのメッセージ更新
   */
  const updateSessionMessages = useCallback((sessionId: string, messages: Message[]): void => {
    try {
      setSessions(prevSessions => 
        prevSessions.map(session => 
          session.id === sessionId 
            ? { 
                ...session, 
                messages, 
                updatedAt: new Date(),
                // 最初のメッセージがある場合、スマートタイトル生成を試行
                title: session.messages.length === 0 && messages.length > 0 && messages[0].role === 'user'
                  ? generateSmartTitle(messages[0].content)
                  : session.title
              }
            : session
        )
      );

      setError(null);
    } catch (err) {
      console.error('Failed to update session messages:', err);
      setError('メッセージの更新に失敗しました');
    }
  }, []);

  /**
   * アクティブセッションの取得
   */
  const activeSession = useMemo(() => {
    return sessions.find(session => session.id === activeSessionId) || null;
  }, [sessions, activeSessionId]);

  /**
   * ソート済みセッションリスト（更新日時の降順）
   */
  const sortedSessions = useMemo(() => {
    return [...sessions].sort((a, b) => 
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  }, [sessions]);

  /**
   * ストレージ使用状況の監視
   */
  const storageUsage = useMemo(() => {
    try {
      return getStorageUsage();
    } catch {
      return {
        totalSize: 0,
        sessionCount: 0,
        averageSessionSize: 0,
        isNearLimit: false,
        isOverWarningThreshold: false
      };
    }
  }, []);

  /**
   * エラークリア
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * 全履歴削除（デバッグ用）
   */
  const clearAllHistory = useCallback(() => {
    try {
      setSessions([]);
      setActiveSessionId(null);
      setError(null);
      console.log('Cleared all chat history');
    } catch (err) {
      console.error('Failed to clear all history:', err);
      setError('履歴の削除に失敗しました');
    }
  }, []);

  return {
    // 状態
    sessions: sortedSessions,
    activeSessionId,
    activeSession,
    isLoading,
    error,
    storageUsage,

    // セッション管理
    createNewChat,
    switchToChat,
    deleteChat,
    updateChatTitle,
    updateSessionMessages,

    // ユーティリティ
    clearError,
    clearAllHistory
  };
}
