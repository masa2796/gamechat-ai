// src/app/assistant/__tests__/useChat.test.ts

import { renderHook, act } from '@testing-library/react';
import { waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useChat } from '../useChat';

// Mock global.fetch outside of the describe block for general use,
// but override it within specific tests if needed.
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ answer: 'テスト応答' }),
  })
) as unknown as typeof fetch;

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
    ) as unknown as typeof fetch;
    delete ((window as unknown) as Record<string, unknown>).grecaptcha;
    delete ((window as unknown) as Record<string, unknown>).firebaseAuth;

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

    // 環境変数を保存
    originalEnv = process.env;
    // テストごとに環境変数をリセットして、reCAPTCHAが無効になるように設定
    process.env = {
      ...originalEnv, // 既存の環境変数をコピー
      NEXT_PUBLIC_DISABLE_RECAPTCHA: 'true', // reCAPTCHAを無効に
      NEXT_PUBLIC_ENVIRONMENT: 'test',
      NEXT_PUBLIC_RECAPTCHA_SITE_KEY: 'test-site-key',
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
    // assistant応答も確認（mock応答）
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toBe('テスト応答');
  });

  it('APIエラー時はassistantロールのエラーメッセージが追加される', async () => {
    const fetchSpy = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: { message: 'APIエラー発生' } }),
        headers: new Headers(),
        redirected: false,
        statusText: 'APIエラー発生',
        type: 'basic',
        url: '',
        clone: () => new Response(),
        body: null,
        bodyUsed: false,
        arrayBuffer: async () => new ArrayBuffer(0),
        blob: async () => new Blob(),
        formData: async () => new FormData(),
        text: async () => '',
      } as unknown as Response)
    );
    global.fetch = fetchSpy;
    
    const { result } = renderHook(() => useChat());
    
    // 初期状態を確認
    expect(result.current.messages.length).toBe(0);
    
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
    const fetchSpy = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: { message: 'Invalid authentication credentials' } }),
        headers: new Headers(),
        redirected: false,
        statusText: '認証エラー発生',
        type: 'basic',
        url: '',
        clone: () => new Response(),
        body: null,
        bodyUsed: false,
        arrayBuffer: async () => new ArrayBuffer(0),
        blob: async () => new Blob(),
        formData: async () => new FormData(),
        text: async () => '',
      } as unknown as Response)
    );
    global.fetch = fetchSpy;
    
    const { result } = renderHook(() => useChat());
    
    // 初期状態を確認
    expect(result.current.messages.length).toBe(0);
    
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
    // reCAPTCHAを有効にするため環境変数を設定
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA = 'false';
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'development'; // testではなくdevelopmentに
    process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY = 'test-site-key';
    
    // fetchが呼ばれないことを確認するためのモック
    const fetchSpy = vi.fn(() => Promise.resolve({
      ok: false,
      json: () => Promise.resolve({ error: { message: 'MOCKED_FETCH_ERROR_SHOULD_NOT_BE_SEEN' } }),
      status: 500,
    })) as unknown as typeof fetch;
    global.fetch = fetchSpy;

    // grecaptcha.executeがエラーを返すようにモックする
    ((window as unknown) as Record<string, unknown>).grecaptcha = {
      execute: vi.fn().mockRejectedValue(new Error('reCAPTCHA取得失敗')),
    };

    const { result } = renderHook(() => useChat());

    // 初期状態を確認
    expect(result.current.messages.length).toBe(0);

    act(() => {
      result.current.setRecaptchaReady(true);
      result.current.setInput('reCAPTCHAエラー');
    });

    await act(async () => {
      await result.current.sendMessage();
    });

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

  it('APIリクエストの内容とレスポンスを正しく処理する', async () => {
    const mockAnswer = 'APIからの応答メッセージ';
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: mockAnswer }),
    }) as unknown as typeof fetch;
    global.fetch = fetchSpy;

    const { result } = renderHook(() => useChat());
    
    // 初期状態を確認
    expect(result.current.messages.length).toBe(0);
    
    act(() => {
      result.current.setInput('APIリクエストテスト');
    });
    await act(async () => {
      await result.current.sendMessage();
    });

    // fetchが正しい引数で呼ばれているか
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const fetchCall = (fetchSpy as unknown as { mock: { calls: [string, RequestInit][] } }).mock.calls[0];
    const [url, options] = fetchCall;
    expect(url).toMatch(/\/api\/rag\/query/);
    expect(options.method).toBe('POST');
    expect((options.headers as Record<string, string>)['Content-Type']).toBe('application/json');
    const body = JSON.parse(options.body as string);
    expect(body.question).toBe('APIリクエストテスト');
    expect(body.top_k).toBe(5);
    expect(body.with_context).toBe(true);
    expect(body.recaptchaToken).toBeDefined();

    // レスポンスがmessagesに反映されているか
    expect(result.current.messages.length).toBe(2);
    expect(result.current.messages[0].content).toBe('APIリクエストテスト');
    expect(result.current.messages[1].content).toBe(mockAnswer);
  });

  it('API失敗時にリトライで成功した場合、エラーメッセージの後に正常応答が追加される', async () => {
    let callCount = 0;
    const fetchSpy = vi.fn().mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ error: { message: '一時的なAPIエラー' } }),
          status: 500,
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ answer: 'リトライ成功応答' }),
      });
    }) as unknown as typeof fetch;
    global.fetch = fetchSpy;

    const { result } = renderHook(() => useChat());
    
    // 初期状態を確認
    expect(result.current.messages.length).toBe(0);
    
    act(() => {
      result.current.setInput('リトライテスト');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    // 1回目はエラー
    expect(result.current.messages.length).toBe(2);
    expect(result.current.messages[1].content).toContain('一時的なAPIエラー');

    // 2回目（リトライ）
    act(() => {
      result.current.setInput('リトライテスト');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    // 2回目は成功応答
    expect(result.current.messages.length).toBe(4);
    expect(result.current.messages[3].content).toBe('リトライ成功応答');
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it('reCAPTCHA無効時はreCAPTCHAトークンが"test"でAPIリクエストされる', async () => {
    // reCAPTCHAを無効に戻す
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA = 'true';
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'test';
    
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'reCAPTCHA無効応答' }),
    }) as unknown as typeof fetch;
    global.fetch = fetchSpy;

    const { result } = renderHook(() => useChat());
    
    // 初期状態を確認
    expect(result.current.messages.length).toBe(0);
    
    act(() => {
      result.current.setInput('reCAPTCHA無効テスト');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    const fetchCall = (fetchSpy as unknown as { mock: { calls: [string, RequestInit][] } }).mock.calls[0];
    const [, options] = fetchCall;
    const body = JSON.parse(options.body as string);
    expect(body.recaptchaToken).toBe('test');
    expect(result.current.messages[1].content).toBe('reCAPTCHA無効応答');
  });

  it('firebase認証トークンが取得できた場合はAuthorizationヘッダーに付与される', async () => {
    // reCAPTCHAを無効に戻す
    process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA = 'true';
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'test';
    
    const mockIdToken = 'dummy-id-token';
    ((window as unknown) as Record<string, unknown>).firebaseAuth = {
      currentUser: {
        getIdToken: vi.fn().mockResolvedValue(mockIdToken),
      },
    };
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: '認証トークン応答' }),
    }) as unknown as typeof fetch;
    global.fetch = fetchSpy;

    const { result } = renderHook(() => useChat());
    
    // 初期状態を確認
    expect(result.current.messages.length).toBe(0);
    
    act(() => {
      result.current.setInput('認証トークンテスト');
    });
    await act(async () => {
      await result.current.sendMessage();
    });
    const fetchCall = (fetchSpy as unknown as { mock: { calls: [string, RequestInit][] } }).mock.calls[0];
    const [, options] = fetchCall;
    expect((options.headers as Record<string, string>).Authorization).toBe(`Bearer ${mockIdToken}`);
    expect(result.current.messages[1].content).toBe('認証トークン応答');
  });
});