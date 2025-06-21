'use client';

import dynamic from 'next/dynamic';

// SSRを無効にしてクライアントサイドでのみレンダリング
const SentryTestComponent = dynamic(
  () => import('./sentry-test').then(mod => ({ default: mod.SentryTestComponent })),
  {
    ssr: false,
    loading: () => (
      <div className="p-4 border border-dashed border-gray-300 rounded-lg m-4 bg-gray-50">
        <h3 className="text-lg font-semibold mb-4 text-gray-600">
          🔧 Sentry Test Panel Loading...
        </h3>
        <div className="text-sm text-gray-500">コンポーネントを読み込み中...</div>
      </div>
    )
  }
);

export { SentryTestComponent as SentryTestComponentWrapper };
