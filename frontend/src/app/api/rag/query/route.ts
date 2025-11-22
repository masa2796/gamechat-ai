/**
 * ARCHIVE_CANDIDATE: MVPでは /chat を直接呼び出すため未使用。
 * テストや将来のバックワード互換向けに残置しています。
 */
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query } = body;
    
    // テスト環境用のシンプルなモック応答
    if (process.env.NEXT_PUBLIC_ENVIRONMENT === 'test') {
      // 少し遅延を入れてローディング状態をテストできるように
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return NextResponse.json({
        answer: `テストモック応答: ${query}について回答します。これはテスト用のダミー応答です。`,
        context: [],
        confidence: 0.95
      });
    }
    
    // 本番環境では外部APIにプロキシ
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const apiKey = process.env.NEXT_PUBLIC_API_KEY || '';
    const response = await fetch(`${apiUrl}/rag/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: { message: 'Internal server error' } },
      { status: 500 }
    );
  }
}
