import * as Sentry from '@sentry/nextjs';

export async function register() {
  const SENTRY_DSN = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;

  if (SENTRY_DSN) {
    if (process.env.NEXT_RUNTIME === 'nodejs') {
      // Server-side initialization
      Sentry.init({
        dsn: SENTRY_DSN,
        tracesSampleRate: 1.0,
        profilesSampleRate: 1.0,
        debug: false,
      });
    }

    if (process.env.NEXT_RUNTIME === 'edge') {
      // Edge runtime initialization
      Sentry.init({
        dsn: SENTRY_DSN,
        tracesSampleRate: 1.0,
        profilesSampleRate: 1.0,
        debug: false,
      });
    }
  } else {
    console.warn('Sentry DSN not found. Sentry monitoring disabled.');
  }
}

// React Server Componentsからのエラーを捕捉するフック
export const onRequestError = Sentry.captureRequestError;
