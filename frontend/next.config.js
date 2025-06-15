/** @type {import('next').NextConfig} */
const nextConfig = {
  // Docker最適化設定
  output: 'standalone',
  
  // パフォーマンス最適化（lightningcssの問題を回避）
  experimental: {
    // optimizeCss: true, // 一時的に無効化
  },
  
  // セキュリティ設定
  async headers() {
    const headers = [
      {
        key: 'X-Frame-Options',
        value: 'SAMEORIGIN',
      },
      {
        key: 'X-Content-Type-Options',
        value: 'nosniff',
      },
      {
        key: 'X-XSS-Protection',
        value: '1; mode=block',
      },
      {
        key: 'Referrer-Policy',
        value: 'strict-origin-when-cross-origin',
      },
    ];

    // 本番環境でのみ追加のセキュリティヘッダーを設定
    if (process.env.NODE_ENV === 'production') {
      headers.push(
        {
          key: 'Strict-Transport-Security',
          value: 'max-age=31536000; includeSubDomains',
        },
        {
          key: 'Content-Security-Policy',
          value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'self';",
        }
      );
    }

    return [
      {
        source: '/(.*)',
        headers,
      },
    ];
  },
  
  // 環境変数設定
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development',
  },
}

module.exports = nextConfig
