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
    return [
      {
        source: '/(.*)',
        headers: [
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
        ],
      },
    ]
  },
  
  // 本番環境用API URL設定
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
