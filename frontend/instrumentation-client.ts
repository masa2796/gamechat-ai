import * as Sentry from '@sentry/nextjs';

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN || process.env.SENTRY_DSN;

// SentryはDSNが設定されている場合のみ初期化
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: 1.0,
    profilesSampleRate: 1.0,
    debug: process.env.NODE_ENV === 'development',
    replaysOnErrorSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    sendDefaultPii: true,
    integrations: [
      Sentry.replayIntegration({
        // Mask all text content, numbers, and input values
        maskAllText: true,
        // Mask all media elements (img, svg, video, object, embed, canvas)
        blockAllMedia: true,
      }),
    ],
  });
} else {
  console.warn('Sentry DSN not found. Sentry monitoring disabled.');
}

// ナビゲーションのインストルメンテーション用フック
export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
