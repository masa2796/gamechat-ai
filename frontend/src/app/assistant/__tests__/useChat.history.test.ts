import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useChat } from '../useChat';

describe('useChat history functionality', () => {
  let originalLocalStorage: Storage;

  beforeEach(() => {
    // LocalStorageのモック
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      length: 0,
      key: vi.fn(),
    };

    originalLocalStorage = window.localStorage;
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });

    // fetchのモック
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ answer: 'テスト応答' }),
      })
    ) as unknown as typeof fetch;

    // 環境変数設定
    process.env = {
      ...process.env,
      NEXT_PUBLIC_DISABLE_RECAPTCHA: 'true',
      NEXT_PUBLIC_ENVIRONMENT: 'test',
    };
  });

  afterEach(() => {
    window.localStorage = originalLocalStorage;
    vi.clearAllMocks();
  });

  it('初期化時にLocalStorageからチャット履歴を読み込む', () => {
    const savedMessages = [
      { id: 'user_1', role: 'user', content: '保存されたメッセージ' },
      { id: 'assistant_1', role: 'assistant', content: '保存された応答' },
    ];

    vi.mocked(window.localStorage.getItem).mockReturnValue(JSON.stringify(savedMessages));

    const { result } = renderHook(() => useChat());

    expect(window.localStorage.getItem).toHaveBeenCalledWith('chat-history');
    expect(result.current.messages).toEqual(savedMessages);
  });

  it('メッセージが追加されるとLocalStorageに保存される', async () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.setInput('新しいメッセージ');
    });

    await act(async () => {
      await result.current.sendMessage();
    });

    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      'chat-history',
      expect.stringContaining('新しいメッセージ')
    );
  });

  it('clearHistory関数でメッセージとLocalStorageがクリアされる', () => {
    const { result } = renderHook(() => useChat());

    // メッセージを追加
    act(() => {
      result.current.setInput('テストメッセージ');
    });

    // 履歴をクリア
    act(() => {
      result.current.clearHistory();
    });

    expect(result.current.messages).toEqual([]);
    expect(window.localStorage.removeItem).toHaveBeenCalledWith('chat-history');
  });

  it('無効なJSONが保存されている場合は読み込みをスキップする', () => {
    vi.mocked(window.localStorage.getItem).mockReturnValue('invalid json');

    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to parse chat history:',
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });

  it('配列以外のデータが保存されている場合は読み込みをスキップする', () => {
    vi.mocked(window.localStorage.getItem).mockReturnValue(JSON.stringify({ invalid: 'data' }));

    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
  });
});
