/** @type {import('next').NextConfig} */

// 基本実験的機能設定
const baseExperimental = {
  optimizePackageImports: ['@radix-ui/react-dialog', '@radix-ui/react-separator', '@radix-ui/react-slot', '@radix-ui/react-tooltip'],
  webVitalsAttribution: ['CLS', 'LCP'],
  // バンドル分析（開発時のみ）
  ...(process.env.ANALYZE === 'true' && {
    bundlePagesRouterDependencies: true,
  }),
};

// CI/テスト環境での追加設定
const ciTestExtraConfig = process.env.CI === 'true' || process.env.NODE_ENV === 'test' ? {
  // CI環境ではFirebase等の外部サービスエラーを無視
  allowMiddlewareResponseBody: true,
} : {};

// 実験的機能の最終設定
const experimental = {
  ...baseExperimental,
  ...ciTestExtraConfig,
};

// メイン設定
const nextConfig = {
  // Docker環境ではstandalone、Firebase Hosting用の静的エクスポート設定（本番ビルド時のみ）
  output: process.env.DOCKER_BUILD === 'true' || process.env.CI === 'true'
    ? 'standalone' 
    : process.env.NODE_ENV === 'production' 
      ? 'export' 
      : undefined,
  
  // 基本設定
  distDir: process.env.DOCKER_BUILD === 'true' || process.env.CI === 'true'
    ? '.next'
    : process.env.NODE_ENV === 'production' 
      ? 'out' 
      : '.next',
  generateEtags: false,
  trailingSlash: false,
  
  // CI環境ではReact Strict Modeを無効化（Firebase初期化エラーを防ぐため）
  reactStrictMode: process.env.CI !== 'true' && process.env.NODE_ENV !== 'test',

  // パフォーマンス最適化
  experimental,
  
  // 画像最適化設定
  images: {
    unoptimized: process.env.NODE_ENV === 'production' && process.env.DOCKER_BUILD !== 'true' && process.env.CI !== 'true', // Firebase Hosting用の静的エクスポート時のみ画像最適化を無効化
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 31536000, // 1年
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // 静的ファイル最適化
  assetPrefix: process.env.CDN_URL || '',
  
  // Webpack最適化
  webpack: (config, { dev, isServer }) => {
    // Critical dependency警告を無視
    config.ignoreWarnings = [
      {
        message: /the request of a dependency is an expression/,
      },
    ];

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

    // クライアントバンドル時にNode.jsコアモジュールを除外
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        module: false,
        path: false,
        os: false,
        crypto: false,
      };
    }

    // CI環境やサーバーサイドビルドでFirebaseエラーを無視
    if (process.env.CI === 'true' || isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
      };
      
      // Firebaseモジュールをサーバーサイドでは無視
      config.externals = [...(config.externals || []), 'firebase'];
    }

    return config;
  },
  
  // セキュリティ設定（standalone モードでのみ有効）
  ...(process.env.DOCKER_BUILD === 'true' || process.env.CI === 'true' ? {
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
          key: 'Referrer-Policy',
          value: 'origin-when-cross-origin',
        },
        {
          key: 'Permissions-Policy',
          value: 'camera=(), microphone=(), geolocation=()',
        },
      ];

      return [
        {
          source: '/(.*)',
          headers: headers,
        },
      ];
    },
  } : {}),
  
  // ルーティング最適化（standalone モードでのみ有効）
  ...(process.env.DOCKER_BUILD === 'true' || process.env.CI === 'true' ? {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: '/api/:path*',
        },
      ];
    },
  } : {}),
};

// CI/テスト環境での追加設定を後から適用
if (process.env.CI === 'true' || process.env.NODE_ENV === 'test') {
  // ビルド時にFirebaseエラーを無視
  nextConfig.transpilePackages = ['firebase'];
}

module.exports = nextConfig;
