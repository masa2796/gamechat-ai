'use client';
import { useEffect } from 'react';
export function useWebVitals() {
    useEffect(() => {
        if (typeof window === 'undefined')
            return;
        const reportWebVitals = (metric) => {
            // 本番環境でのみ送信
            if (process.env.NODE_ENV === 'production') {
                fetch('/api/performance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: metric.name,
                        value: metric.value,
                        id: metric.id,
                        rating: metric.rating,
                        url: window.location.href,
                        userAgent: navigator.userAgent,
                    }),
                }).catch(console.error);
            }
            // 開発環境ではコンソールに出力
            if (process.env.NODE_ENV === 'development') {
                console.log('Web Vitals:', metric);
            }
        };
        // Web Vitalsライブラリが利用可能な場合のみ実行
        if ('web-vitals' in window || typeof window.webVitals !== 'undefined') {
            // Dynamic import for web-vitals
            import('web-vitals').then(async (webVitalsModule) => {
                const { onCLS, onFCP, onLCP, onTTFB } = webVitalsModule;
                onCLS(reportWebVitals);
                onFCP(reportWebVitals);
                onLCP(reportWebVitals);
                onTTFB(reportWebVitals);
                // onFID is deprecated in favor of onINP
                try {
                    const { onINP } = webVitalsModule;
                    onINP(reportWebVitals);
                }
                catch (_a) {
                    // onINP might not be available in older versions
                    console.log('onINP not available');
                }
            }).catch(() => {
                // web-vitalsが利用できない場合は代替実装
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.entryType === 'navigation') {
                            const navEntry = entry;
                            reportWebVitals({
                                name: 'FCP',
                                value: navEntry.loadEventEnd - navEntry.loadEventStart,
                                id: 'fallback-fcp',
                                rating: 'good'
                            });
                        }
                    }
                });
                if ('observe' in observer) {
                    observer.observe({ entryTypes: ['navigation'] });
                }
            });
        }
    }, []);
}
