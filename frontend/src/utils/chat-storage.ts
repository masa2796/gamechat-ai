/**
 * チャット履歴管理のためのストレージユーティリティ
 * LocalStorageの読み書き、データ圧縮・最適化を担当
 */

import { ChatSession, ChatHistoryState, STORAGE_KEYS } from '@/types/chat';

/**
 * ストレージの容量制限（バイト）
 * LocalStorageの一般的な制限は5-10MB
 */
const STORAGE_LIMITS = {
  MAX_STORAGE_SIZE: 5 * 1024 * 1024, // 5MB
  WARNING_THRESHOLD: 4 * 1024 * 1024, // 4MB で警告
  MAX_SESSIONS: 50,
  MAX_MESSAGES_PER_SESSION: 100,
} as const;

/**
 * エラータイプ定義
 */
export class ChatStorageError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'ChatStorageError';
  }
}

/**
 * ストレージサイズを計算（概算）
 */
export function calculateStorageSize(data: unknown): number {
  try {
    return new Blob([JSON.stringify(data)]).size;
  } catch {
    return 0;
  }
}

/**
 * データの圧縮（不要なメタデータを削除）
 */
export function compressSessionData(sessions: ChatSession[]): ChatSession[] {
  return sessions.map(session => ({
    ...session,
    messages: session.messages.map(message => ({
      role: message.role,
      content: message.content,
      // cardContextは大きい場合があるので必要時のみ保持
      ...(message.cardContext && message.cardContext.length > 0 && {
        cardContext: message.cardContext
      })
    }))
  }));
}

/**
 * LRU（Least Recently Used）でセッションを削除
 */
export function applyLRUCleanup(sessions: ChatSession[]): ChatSession[] {
  if (sessions.length <= STORAGE_LIMITS.MAX_SESSIONS) {
    return sessions;
  }

  // 更新日時でソート（新しい順）
  const sortedSessions = [...sessions].sort((a, b) => 
    new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );

  // 最大セッション数まで削減
  return sortedSessions.slice(0, STORAGE_LIMITS.MAX_SESSIONS);
}

/**
 * セッション内のメッセージ数を制限
 */
export function limitMessagesPerSession(sessions: ChatSession[]): ChatSession[] {
  return sessions.map(session => ({
    ...session,
    messages: session.messages.slice(-STORAGE_LIMITS.MAX_MESSAGES_PER_SESSION)
  }));
}

/**
 * データ最適化を適用
 */
export function optimizeStorageData(sessions: ChatSession[]): ChatSession[] {
  let optimizedSessions = compressSessionData(sessions);
  optimizedSessions = limitMessagesPerSession(optimizedSessions);
  optimizedSessions = applyLRUCleanup(optimizedSessions);
  
  return optimizedSessions;
}

/**
 * LocalStorageからチャットセッションを読み込み
 */
export function loadChatSessions(): ChatSession[] {
  try {
    // SSR中はlocalStorageが利用できないため、空配列を返す
    if (typeof window === 'undefined' || !window.localStorage) {
      return [];
    }
    
    const sessionsData = localStorage.getItem(STORAGE_KEYS.CHAT_SESSIONS);
    if (!sessionsData) {
      return [];
    }

    const sessions: ChatSession[] = JSON.parse(sessionsData);
    
    // Date オブジェクトに変換
    return sessions.map(session => ({
      ...session,
      createdAt: new Date(session.createdAt),
      updatedAt: new Date(session.updatedAt)
    }));
  } catch (error) {
    console.error('Failed to load chat sessions:', error);
    throw new ChatStorageError('チャット履歴の読み込みに失敗しました', 'LOAD_ERROR');
  }
}

/**
 * LocalStorageにチャットセッションを保存
 */
export function saveChatSessions(sessions: ChatSession[]): void {
  try {
    // SSR中はlocalStorageが利用できないため、何もしない
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    
    // データ最適化を適用
    const optimizedSessions = optimizeStorageData(sessions);
    
    // ストレージサイズをチェック
    const dataSize = calculateStorageSize(optimizedSessions);
    
    if (dataSize > STORAGE_LIMITS.MAX_STORAGE_SIZE) {
      throw new ChatStorageError(
        'ストレージ容量が上限を超えています。古いチャットを削除してください。',
        'STORAGE_FULL'
      );
    }
    
    if (dataSize > STORAGE_LIMITS.WARNING_THRESHOLD) {
      console.warn('ストレージ使用量が警告レベルに達しています:', dataSize, 'bytes');
    }

    const sessionsJson = JSON.stringify(optimizedSessions);
    localStorage.setItem(STORAGE_KEYS.CHAT_SESSIONS, sessionsJson);
  } catch (error) {
    if (error instanceof ChatStorageError) {
      throw error;
    }
    
    // LocalStorage容量不足エラー
    if (error instanceof DOMException && error.code === 22) {
      throw new ChatStorageError(
        'ブラウザのストレージ容量が不足しています。',
        'QUOTA_EXCEEDED'
      );
    }
    
    console.error('Failed to save chat sessions:', error);
    throw new ChatStorageError('チャット履歴の保存に失敗しました', 'SAVE_ERROR');
  }
}

/**
 * アクティブセッションIDを読み込み
 */
export function loadActiveSessionId(): string | null {
  try {
    // SSR中はlocalStorageが利用できないため、nullを返す
    if (typeof window === 'undefined' || !window.localStorage) {
      return null;
    }
    
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);
  } catch (error) {
    console.error('Failed to load active session ID:', error);
    return null;
  }
}

/**
 * アクティブセッションIDを保存
 */
export function saveActiveSessionId(sessionId: string | null): void {
  try {
    // SSR中はlocalStorageが利用できないため、何もしない
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    
    if (sessionId) {
      localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION, sessionId);
    } else {
      localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
    }
  } catch (error) {
    console.error('Failed to save active session ID:', error);
  }
}

/**
 * チャット履歴の全体状態を読み込み
 */
export function loadChatHistoryState(): ChatHistoryState {
  const sessions = loadChatSessions();
  const activeSessionId = loadActiveSessionId();
  
  return {
    sessions,
    activeSessionId,
    maxSessions: STORAGE_LIMITS.MAX_SESSIONS
  };
}

/**
 * チャット履歴の全体状態を保存
 */
export function saveChatHistoryState(state: ChatHistoryState): void {
  saveChatSessions(state.sessions);
  saveActiveSessionId(state.activeSessionId);
}

/**
 * 旧形式のチャット履歴が存在するかどうかをチェック
 */
export function detectOldChatHistory(): boolean {
  try {
    // SSR中はlocalStorageが利用できないため、falseを返す
    if (typeof window === 'undefined' || !window.localStorage) {
      return false;
    }
    
    const oldHistory = localStorage.getItem('chat-history');
    return oldHistory !== null;
  } catch {
    return false;
  }
}

/**
 * 旧形式からのマイグレーション
 */
export function migrateOldChatHistory(): ChatSession[] {
  try {
    // SSR中はlocalStorageが利用できないため、空配列を返す
    if (typeof window === 'undefined' || !window.localStorage) {
      return [];
    }
    
    const oldHistoryData = localStorage.getItem('chat-history');
    if (!oldHistoryData) {
      return [];
    }

    const oldMessages = JSON.parse(oldHistoryData);
    if (!Array.isArray(oldMessages) || oldMessages.length === 0) {
      return [];
    }

    // 旧データを新形式のセッションに変換
    const migratedSession: ChatSession = {
      id: crypto.randomUUID(),
      title: '過去のチャット履歴',
      messages: oldMessages.map(msg => ({
        role: msg.role || 'user',
        content: msg.content || '',
        ...(msg.cardContext && { cardContext: msg.cardContext })
      })),
      createdAt: new Date(Date.now() - 86400000), // 1日前
      updatedAt: new Date(),
      isActive: true
    };

    // 旧データをバックアップ用キーに移動
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, oldHistoryData);
      localStorage.removeItem('chat-history');
    }

    console.log('Successfully migrated old chat history');
    return [migratedSession];
  } catch (error) {
    console.error('Failed to migrate old chat history:', error);
    return [];
  }
}

/**
 * ストレージの使用状況を取得
 */
export function getStorageUsage(): {
  totalSize: number;
  sessionCount: number;
  averageSessionSize: number;
  isNearLimit: boolean;
  isOverWarningThreshold: boolean;
} {
  // SSR中はlocalStorageが利用できないため、デフォルト値を返す
  if (typeof window === 'undefined' || !window.localStorage) {
    return {
      totalSize: 0,
      sessionCount: 0,
      averageSessionSize: 0,
      isNearLimit: false,
      isOverWarningThreshold: false
    };
  }
  
  const sessions = loadChatSessions();
  const totalSize = calculateStorageSize(sessions);
  const sessionCount = sessions.length;
  const averageSessionSize = sessionCount > 0 ? totalSize / sessionCount : 0;
  
  return {
    totalSize,
    sessionCount,
    averageSessionSize,
    isNearLimit: totalSize > STORAGE_LIMITS.MAX_STORAGE_SIZE * 0.9,
    isOverWarningThreshold: totalSize > STORAGE_LIMITS.WARNING_THRESHOLD
  };
}

/**
 * ストレージをクリア（デバッグ用）
 */
export function clearChatStorage(): void {
  try {
    // SSR中はlocalStorageが利用できないため、何もしない
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    
    localStorage.removeItem(STORAGE_KEYS.CHAT_SESSIONS);
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
    localStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY);
    console.log('Chat storage cleared');
  } catch (error) {
    console.error('Failed to clear chat storage:', error);
  }
}

/**
 * エクスポート用のデータ取得
 */
export function exportChatData(): {
  sessions: ChatSession[];
  exportedAt: string;
  version: string;
} {
  const sessions = loadChatSessions();
  
  return {
    sessions,
    exportedAt: new Date().toISOString(),
    version: '1.0'
  };
}

/**
 * インポート用のデータ検証
 */
export function validateImportData(data: unknown): data is {
  sessions: ChatSession[];
  exportedAt: string;
  version: string;
} {
  if (!data || typeof data !== 'object') {
    return false;
  }

  const obj = data as Record<string, unknown>;
  
  return (
    Array.isArray(obj.sessions) &&
    typeof obj.exportedAt === 'string' &&
    typeof obj.version === 'string' &&
    obj.sessions.every((session: unknown) => {
      const s = session as Record<string, unknown>;
      return (
        typeof s.id === 'string' &&
        typeof s.title === 'string' &&
        Array.isArray(s.messages) &&
        s.createdAt &&
        s.updatedAt &&
        typeof s.isActive === 'boolean'
      );
    })
  );
}
