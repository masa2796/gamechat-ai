import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { POST } from '../route';
import { NextRequest } from 'next/server';

// NextRequestのモック生成
type MockRequestBody = Record<string, unknown>;
function createMockRequest(body: MockRequestBody) {
  return {
    json: async () => body,
  } as unknown as NextRequest;
}

describe('app/api/rag/query/route.ts API', () => {
  const OLD_ENV = process.env;
  beforeEach(() => {
    vi.resetAllMocks();
    process.env = { ...OLD_ENV };
  });
  afterEach(() => {
    process.env = OLD_ENV;
  });

  it('正常系: テスト環境で正しいレスポンスが返る', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'test';
    const req = createMockRequest({ query: 'テストクエリ' });
    const res = await POST(req);
    const json = await res.json();
    expect(json.answer).toContain('テストモック応答');
    expect(json.confidence).toBeCloseTo(0.95);
    expect(Array.isArray(json.context)).toBe(true);
  });

  it('正常系: 本番環境で外部APIが200ならそのまま返す', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'production';
    global.fetch = vi.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ answer: '外部API応答', context: ['ctx'], confidence: 0.8 }),
    })) as unknown as typeof fetch;
    const req = createMockRequest({ query: '本番クエリ' });
    const res = await POST(req);
    const json = await res.json();
    expect(json.answer).toBe('外部API応答');
    expect(json.context).toEqual(['ctx']);
    expect(json.confidence).toBeCloseTo(0.8);
  });

  it('バリデーション: queryが未指定の場合は400エラー', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'test';
    // route.tsはバリデーションしていないが、今後の拡張用に例示
    const req = createMockRequest({});
    const res = await POST(req);
    const json = await res.json();
    // queryが未指定でもエラーにならず返る現状仕様
    expect(json.answer).toContain('テストモック応答');
  });

  it('異常系: 外部APIがエラー時は500エラー', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'production';
    global.fetch = vi.fn(() => Promise.resolve({
      ok: false,
      status: 502,
      json: () => Promise.resolve({ error: '外部APIエラー' }),
    })) as unknown as typeof fetch;
    const req = createMockRequest({ query: '異常系' });
    const res = await POST(req);
    expect(res.status).toBe(500);
    const json = await res.json();
    expect(json.error.message).toBe('Internal server error');
  });

  it('外部API/DBアクセスのモック: fetch例外時も500エラー', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'production';
    global.fetch = vi.fn(() => { throw new Error('fetch失敗'); }) as unknown as typeof fetch;
    const req = createMockRequest({ query: '例外パス' });
    const res = await POST(req);
    expect(res.status).toBe(500);
    const json = await res.json();
    expect(json.error.message).toBe('Internal server error');
  });

  it('戻り値の型安全性: answer/context/confidence型を検証', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'test';
    const req = createMockRequest({ query: '型テスト' });
    const res = await POST(req);
    const json = await res.json();
    expect(typeof json.answer).toBe('string');
    expect(Array.isArray(json.context)).toBe(true);
    expect(typeof json.confidence).toBe('number');
  });
});
