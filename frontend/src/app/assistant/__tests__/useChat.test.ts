// src/app/assistant/__tests__/useChat.test.ts

import { renderHook, act } from '@testing-library/react';
import { waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useChat } from '../useChat';

// Mock global.fetch outside of the describe block for general use,
// but override it within specific tests if needed.
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ answer: 'テスト応答' }),
  })
) as any;

describe('useChat', () => {
  // 環境変数を保存するための変数
  let originalEnv: NodeJS.ProcessEnv;

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ answer: 'テスト応答' }),
      })
    ) as any;
    delete (window as any).grecaptcha;

    // 環境変数を保存
    originalEnv = process.env;
    // テストごとに環境変数をリセットして、reCAPTCHAが有効になるように設定
    process.env = {
      ...originalEnv, // 既存の環境変数をコピー
      NEXT_PUBLIC_DISABLE_RECAPTCHA: 'false',
      NEXT_PUBLIC_ENVIRONMENT: 'development', // 'test' 以外に設定
      NEXT_PUBLIC_RECAPTCHA_SITE_KEY: 'test-site-key', // reCAPTCHAが有効になるようにキーを設定
    };
  });

  afterEach(() => {
    // 各テストの後に環境変数を元に戻す
    process.env = originalEnv;
  });

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

  it('APIエラー時はassistantロールのエラーメッセージが追加される', async () => {
    (global.fetch as any) = vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ error: { message: 'APIエラー発生' } }),
        status: 500,
      })
    );
    const { result } = renderHook(() => useChat());
    act(() => {
      result.current.setInput('エラーを起こす');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    expect(result.current.messages.length).toBe(2); // user, assistant(error)
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toContain('APIエラー発生');
  });

  it('認証失敗時はassistantロールの認証エラーメッセージが追加される', async () => {
    (global.fetch as unknown) = vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ error: { message: 'Invalid authentication credentials' } }),
        status: 401,
      })
    );
    const { result } = renderHook(() => useChat());
    act(() => {
      result.current.setInput('認証エラーを起こす');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    expect(result.current.messages.length).toBe(2); // user, assistant(error)
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toContain('認証に失敗しました');
  });

  it('reCAPTCHA失敗時はassistantロールのエラーメッセージが追加される', async () => {
    // fetchが呼ばれないことを確認するためのモック。
    // 万が一呼ばれても、エラーになるように設定し、内容がテストに影響しないようにする。
    const fetchSpy = vi.fn(() => Promise.resolve({
      ok: false,
      json: () => Promise.resolve({ error: { message: 'MOCKED_FETCH_ERROR_SHOULD_NOT_BE_SEEN' } }),
      status: 500,
    }));
    (global.fetch as unknown) = fetchSpy;

    // grecaptcha.executeがエラーを返すようにモックする
    (window as any).grecaptcha = {
      execute: vi.fn().mockRejectedValue(new Error('reCAPTCHA取得失敗')),
    };

    const { result } = renderHook(() => useChat());

    // recaptchaReadyをtrueに設定するのは、grecaptchaがモックされた後かつ、
    // sendMessageが呼び出される前に行う。
    act(() => {
      // isRecaptchaDisabled() が false を返すため、setRecaptchaReady(true) は必要ないはずですが、
      // 念のため明示的にtrueに設定して、reCAPTCHAの実行パスを確保します。
      result.current.setRecaptchaReady(true);
      result.current.setInput('reCAPTCHAエラー');
    });

    // sendMessageを呼び出すと、内部でreCAPTCHAの実行が試みられ、エラーが発生するはず
    await act(async () => {
      await result.current.sendMessage();
    });

    // 非同期処理が完了し、メッセージが更新されるのを待つ
    await waitFor(() => {
      expect(result.current.messages.length).toBe(2); // ユーザーメッセージとアシスタントのエラーメッセージ
      expect(result.current.messages[0].content).toBe('reCAPTCHAエラー'); // ユーザーメッセージの確認
      expect(result.current.messages[1].role).toBe('assistant');
      expect(result.current.messages[1].content).toContain('reCAPTCHA取得失敗');
      expect(result.current.messages[1].content).not.toContain('MOCKED_FETCH_ERROR_SHOULD_NOT_BE_SEEN');
    });

    // fetchが呼び出されていないことを確認
    expect(fetchSpy).not.toHaveBeenCalled();

  });
});