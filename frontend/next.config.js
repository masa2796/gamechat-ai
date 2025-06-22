/** @type {import('next').NextConfig} */
const nextConfig = {
  // Docker環境またはCI環境では standalone モードを使用
  // ローカル開発でも standalone モードを使用（API Routesが必要なため）
  output: 'standalone',
  
  // 基本設定
  distDir: '.next',
  generateEtags: false,
  trailingSlash: true,
  
  // パフォーマンス最適化
  
  // パフォーマンス最適化
  experimental: {
    // optimizeCss: true, // 一時的に無効化 
    optimizePackageImports: ['@radix-ui/react-dialog', '@radix-ui/react-separator', '@radix-ui/react-slot', '@radix-ui/react-tooltip'],
    webVitalsAttribution: ['CLS', 'LCP'],
    // esmExternals: 'loose', // 外部ESMパッケージの最適化
  },
  
  // 画像最適化設定
  images: {
    unoptimized: true, // Docker/CI環境では画像最適化を無効化
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
  
  // セキュリティ設定（standalone モードでのみ有効）
  ...(process.env.DOCKER_BUILD || process.env.CI ? {
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
  } : {}),
  
  // 環境変数設定
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development',
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
    GOOGLE_SITE_VERIFICATION: process.env.GOOGLE_SITE_VERIFICATION,
    NEXT_PUBLIC_SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN,
    // CI環境用のデフォルト値を設定
    NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || (process.env.CI ? 'dummy-api-key-for-ci' : ''),
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || (process.env.CI ? 'dummy-project.firebaseapp.com' : ''),
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || (process.env.CI ? 'dummy-project' : ''),
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || (process.env.CI ? 'dummy-project.firebasestorage.app' : ''),
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || (process.env.CI ? '123456789012' : ''),
    NEXT_PUBLIC_FIREBASE_APP_ID: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || (process.env.CI ? '1:123456789012:web:dummy-app-id' : ''),
    NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || (process.env.CI ? 'G-DUMMY' : ''),
    NEXT_PUBLIC_RECAPTCHA_SITE_KEY: process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || (process.env.CI ? 'dummy-recaptcha-site-key' : ''),
    NEXT_PUBLIC_API_KEY: process.env.NEXT_PUBLIC_API_KEY || (process.env.CI ? 'dummy-api-key-for-ci' : 'dev-key-12345'),
  },

  // PWA対応設定（export モードでは無効化）
  ...(!(process.env.DOCKER_BUILD || process.env.CI) ? {} : {
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
  }),
}

// Injected content via Sentry wizard below

// eslint-disable-next-line @typescript-eslint/no-require-imports
const { withSentryConfig } = require("@sentry/nextjs");

// CI環境または開発環境でSENTRY_AUTH_TOKENが設定されていない場合はSentryを無効化
const shouldUseSentry = process.env.NODE_ENV === 'production' && 
                       !process.env.CI && 
                       process.env.SENTRY_AUTH_TOKEN;

module.exports = shouldUseSentry ? withSentryConfig(
  nextConfig,
  {
    // For all available options, see:
    // https://www.npmjs.com/package/@sentry/webpack-plugin#options

    org: "masaki-tanaka",
    project: "javascript-nextjs",

    // Only print logs for uploading source maps in CI
    silent: !process.env.CI,

    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // tunnelRoute を export モードでは無効化
    tunnelRoute: process.env.DOCKER_BUILD || process.env.CI ? "/monitoring" : undefined,

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    disableLogger: true,

    // Enables automatic instrumentation of Vercel Cron Monitors. (Does not yet work with App Router route handlers.)
    // See the following for more information:
    // https://docs.sentry.io/product/crons/
    // https://vercel.com/docs/cron-jobs
    automaticVercelMonitors: process.env.DOCKER_BUILD || process.env.CI || false,
  }
) : nextConfig;
