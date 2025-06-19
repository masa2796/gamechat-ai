/** @type {import('next').NextConfig} */
const nextConfig = {
  // Firebase Hosting用設定（静的エクスポート + Cloud Run連携）
  // CI環境では静的エクスポートを無効にして通常のNext.jsサーバーを使用
  ...(process.env.CI ? { 
    // CI環境では通常のNext.jsサーバーモードを使用
    distDir: '.next',
    generateEtags: false,
    output: 'standalone', // Docker用の最適化された出力
  } : { 
    output: 'export' 
  }),
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  
  // パフォーマンス最適化
  experimental: {
    // optimizeCss: true, // 一時的に無効化 
    optimizePackageImports: ['@radix-ui/react-dialog', '@radix-ui/react-separator', '@radix-ui/react-slot', '@radix-ui/react-tooltip'],
    webVitalsAttribution: ['CLS', 'LCP'],
    // esmExternals: 'loose', // 外部ESMパッケージの最適化
  },
  
  // 画像最適化設定
  images: {
    ...(process.env.CI ? { 
      unoptimized: true,
      domains: [],
    } : {
      formats: ['image/webp', 'image/avif'],
      minimumCacheTTL: 31536000, // 1年
      deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
      imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
      unoptimized: true,
    }),
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
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
    GOOGLE_SITE_VERIFICATION: process.env.GOOGLE_SITE_VERIFICATION,
    // CI環境用のデフォルト値を設定
    NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || (process.env.CI ? 'dummy-api-key-for-ci' : ''),
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || (process.env.CI ? 'dummy-project.firebaseapp.com' : ''),
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || (process.env.CI ? 'dummy-project' : ''),
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || (process.env.CI ? 'dummy-project.firebasestorage.app' : ''),
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || (process.env.CI ? '123456789012' : ''),
    NEXT_PUBLIC_FIREBASE_APP_ID: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || (process.env.CI ? '1:123456789012:web:dummy-app-id' : ''),
    NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || (process.env.CI ? 'G-DUMMY' : ''),
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY: process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || (process.env.CI ? 'dummy-recaptcha-site-key' : ''),
    NEXT_PUBLIC_API_KEY: process.env.NEXT_PUBLIC_API_KEY || (process.env.CI ? 'dummy-api-key-for-ci' : ''),
  },

  // PWA対応設定
  async rewrites() {
    return [
      {
        source: '/sw.js',
        destination: '/sw.js',
      },
      {
        source: '/manifest.json',
        destination: '/manifest.json',
      },
    ];
  },
}

module.exports = nextConfig
