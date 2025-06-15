import { NextResponse } from 'next/server';

// 静的エクスポートではAPIルートは動作しないため、
// この設定は開発・本番サーバー用のみ
export const dynamic = 'force-dynamic'
export const revalidate = false

export async function GET() {
  return NextResponse.json({ 
    status: 'healthy', 
    service: 'gamechat-ai-frontend',
    timestamp: new Date().toISOString()
  });
}
