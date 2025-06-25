'use client';
import { useEffect } from 'react';
// Sentryの初期化はすでにsentry.client.config.jsで行われているため、
// このコンポーネントはSentryのユーザーコンテキストやタグを設定するために使用
export function SentryProvider({ children }) {
    useEffect(() => {
        // Sentry is already initialized via sentry.client.config.js
        // Additional Sentry configuration can be done here if needed
        if (typeof window !== 'undefined') {
            // 動的にSentryを読み込み、基本設定を行う
            import('@sentry/nextjs').then((Sentry) => {
                // 基本的なタグを設定
                Sentry.setTag('app_version', process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0');
                Sentry.setTag('environment', process.env.NEXT_PUBLIC_ENVIRONMENT || 'development');
                // コンテキスト情報を設定
                Sentry.setContext('runtime', {
                    name: 'browser',
                    version: navigator.userAgent,
                });
                console.log('Sentry initialized successfully');
            }).catch((err) => {
                console.error('Failed to initialize Sentry:', err);
            });
        }
    }, []);
    return <>{children}</>;
}
