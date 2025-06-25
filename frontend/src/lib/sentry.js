/**
 * APIエラーをSentryに報告するユーティリティ関数
 */
export function captureAPIError(error, context) {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            Sentry.withScope((scope) => {
                scope.setTag('error_type', 'api_error');
                scope.setLevel('error');
                if (context) {
                    scope.setContext('api_context', context);
                }
                Sentry.captureException(error);
            });
        });
    }
}
/**
 * ユーザーアクションをSentryに記録
 */
export function captureUserAction(action, data) {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            Sentry.addBreadcrumb({
                message: action,
                level: 'info',
                data,
            });
        });
    }
}
/**
 * パフォーマンス測定の開始
 */
export function startPerformanceTransaction(name, operation) {
    if (typeof window !== 'undefined') {
        return import('@sentry/nextjs').then((Sentry) => {
            return Sentry.startSpan({
                name,
                op: operation,
            }, (span) => span);
        });
    }
    return Promise.resolve(null);
}
/**
 * スパンを使った処理の実行
 */
export async function withPerformanceSpan(name, operation, fn) {
    if (typeof window !== 'undefined') {
        const Sentry = await import('@sentry/nextjs');
        return Sentry.startSpan({ name, op: operation }, fn);
    }
    return fn();
}
/**
 * ユーザー情報をSentryに設定
 */
export function setSentryUser(user) {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            Sentry.setUser(user);
        });
    }
}
/**
 * 手動でエラーを報告
 */
export function captureMessage(message, level = 'info') {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            Sentry.captureMessage(message, level);
        });
    }
}
/**
 * Sentryのタグを設定
 */
export function setSentryTag(key, value) {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            Sentry.setTag(key, value);
        });
    }
}
/**
 * Sentryのコンテキストを設定
 */
export function setSentryContext(key, context) {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            Sentry.setContext(key, context);
        });
    }
}
/**
 * 本番環境監視のテスト機能
 */
export function testProductionMonitoring() {
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
        import('@sentry/nextjs').then((Sentry) => {
            // エラー監視のテスト
            console.log('🧪 Testing Sentry error monitoring...');
            Sentry.captureException(new Error('Test error for monitoring setup'));
            // パフォーマンス監視のテスト
            console.log('🧪 Testing Sentry performance monitoring...');
            Sentry.startSpan({ name: 'test-transaction', op: 'test' }, () => {
                return new Promise(resolve => setTimeout(resolve, 100));
            });
            // ユーザーアクションのテスト
            console.log('🧪 Testing Sentry user action tracking...');
            captureUserAction('test_action', { testData: 'monitoring_setup' });
            console.log('✅ Sentry monitoring test completed');
        });
    }
}
/**
 * 本番環境での重要エラーの報告
 */
export function captureProductionError(error, severity = 'medium', context) {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            Sentry.withScope((scope) => {
                scope.setTag('severity', severity);
                scope.setTag('environment', process.env.NODE_ENV);
                scope.setLevel(severity === 'critical' ? 'fatal' : 'error');
                // 重要度に応じてfingerprint設定（グルーピング制御）
                if (severity === 'critical') {
                    scope.setFingerprint(['critical', error.name, error.message]);
                }
                if (context) {
                    scope.setContext('error_context', context);
                }
                Sentry.captureException(error);
            });
        });
    }
}
/**
 * ビジネスメトリクスの記録
 */
export function recordBusinessMetric(metricName, value, unit = 'count', tags) {
    if (typeof window !== 'undefined') {
        import('@sentry/nextjs').then((Sentry) => {
            // メトリクスの代わりにカスタムイベントとして記録
            Sentry.addBreadcrumb({
                message: `Metric: ${metricName}`,
                level: 'info',
                data: Object.assign({ value,
                    unit }, tags),
                category: 'metric',
            });
        });
    }
}
