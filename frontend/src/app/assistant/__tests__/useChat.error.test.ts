import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useChat } from '../useChat';

describe('useChat error handling', () => {
  it('APIエラー時にエラーメッセージがmessagesに追加される', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ error: { message: 'APIエラー' } }),
      })
    ) as any;
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
        json: () => Promise.resolve({ error: { message: 'Invalid authentication credentials' } }),
      })
    ) as any;
    const { result } = renderHook(() => useChat());
    act(() => {
      result.current.setInput('auth error');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    expect(result.current.messages[1].content).toContain('認証に失敗しました');
  });
});
