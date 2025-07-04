import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useChat } from '../useChat';

global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ answer: 'テスト応答' }),
  })
) as any;

describe('useChat', () => {
  it('初期状態は空', () => {
    const { result } = renderHook(() => useChat());
    expect(result.current.messages).toEqual([]);
    expect(result.current.input).toBe('');
    expect(result.current.loading).toBe(false);
  });

  it('メッセージ送信でmessagesが増える', async () => {
    const { result } = renderHook(() => useChat());
    act(() => {
      result.current.setInput('こんにちは');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    expect(result.current.messages.length).toBe(2); // user, assistant
    expect(result.current.messages[0].content).toBe('こんにちは');
    expect(result.current.messages[1].content).toBe('テスト応答');
  });
});
