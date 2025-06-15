/** @type {import('next').NextConfig} */
const nextConfig = {
  // Docker最適化設定
  output: 'standalone',
  
  // パフォーマンス最適化
  experimental: {
    // optimizeCss: true, // 一時的に無効化
    optimizePackageImports: ['@mui/material', '@mui/icons-material'],
  },
  
  // 画像最適化設定
  images: {
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 31536000, // 1年
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // 静的ファイル最適化
  assetPrefix: process.env.CDN_URL || '',
  
  // バンドル分析（開発時のみ）
  ...(process.env.ANALYZE === 'true' && {
    experimental: {
      bundlePagesRouterDependencies: true,
    },
  }),
  
  // Webpack最適化
  webpack: (config, { dev }) => {
    // プロダクションビルドの最適化
    if (!dev) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
        },
      };
    }
    
    return config;
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
