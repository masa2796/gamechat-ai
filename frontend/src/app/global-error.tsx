'use client';

import { useEffect } from 'react';

interface ErrorBoundaryProps {
  error: Error & { digest?: string | undefined };
  reset: () => void;
}

export default function GlobalError({
  error,
  reset,
}: ErrorBoundaryProps) {
  useEffect(() => {
    // Monitoring removed (MVP) - no external error reporting
  }, [error]);

  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                申し訳ございません
              </h2>
              <p className="text-gray-600 mb-6">
                予期しないエラーが発生しました。しばらく時間をおいて再度お試しください。
              </p>
              <button
                onClick={reset}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                再試行
              </button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
