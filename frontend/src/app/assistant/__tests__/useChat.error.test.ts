import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useChat } from '../useChat';

describe('useChat error handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // LocalStorageをクリア
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    });

    // reCAPTCHA無効に設定
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA = 'true';
  });

  it('APIエラー時にエラーメッセージがmessagesに追加される', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ error: { message: 'APIエラー' } }),
      })
    ) as unknown as typeof fetch;
    const { result } = renderHook(() => useChat());
    act(() => {
      result.current.setInput('error test');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    expect(result.current.messages.length).toBe(2); // user, error
    expect(result.current.messages[1].content).toContain('APIエラー');
  });

  it('認証エラー時は認証エラー文言が表示される', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: { message: 'Invalid authentication credentials' } }),
      })
    ) as unknown as typeof fetch;
    const { result } = renderHook(() => useChat());
    act(() => {
      result.current.setInput('auth error');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    expect(result.current.messages.length).toBe(2); // user, error
    expect(result.current.messages[1].content).toContain('認証に失敗しました');
  });
});
