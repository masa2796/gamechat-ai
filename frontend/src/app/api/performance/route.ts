import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const userAgent = request.headers.get('user-agent') || ''
  
  // Web Vitals計測用のエンドポイント
  const performance = {
    timestamp: new Date().toISOString(),
    userAgent,
    // パフォーマンス指標はクライアントサイドから送信される
  }

  return NextResponse.json({ status: 'ok', performance })
}

export async function POST(request: NextRequest) {
  try {
    const data = await request.json()
    
    // Web Vitalsデータをログに記録
    console.log('Performance metrics:', {
      timestamp: new Date().toISOString(),
      ...data
    })
    
    // 本番環境では分析サービス（Google Analytics、Datadog等）に送信
    if (process.env.NODE_ENV === 'production') {
      // 分析サービスへの送信ロジック
      // await sendToAnalytics(data)
    }
    
    return NextResponse.json({ status: 'recorded' })
  } catch (error) {
    console.error('Failed to record performance metrics:', error)
    return NextResponse.json({ error: 'Failed to record metrics' }, { status: 500 })
  }
}
