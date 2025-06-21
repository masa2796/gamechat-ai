import * as Sentry from '@sentry/nextjs';

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN || process.env.SENTRY_DSN;

// SentryはDSNが設定されている場合のみ初期化
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: 1.0,
    profilesSampleRate: 1.0,
    debug: false,
    replaysOnErrorSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    integrations: [
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
  });
} else {
  console.warn('Sentry DSN not found. Sentry monitoring disabled.');
}

// ナビゲーションのインストルメンテーション用フック
export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
