import { NextResponse } from 'next/server';

// Static export用の設定
export const dynamic = 'force-static'
export const revalidate = false

export async function GET() {
  return NextResponse.json({ 
    status: 'healthy', 
    service: 'gamechat-ai-frontend',
    timestamp: new Date().toISOString()
  });
}
