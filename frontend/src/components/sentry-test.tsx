'use client';

import { useState } from 'react';
import { captureAPIError, captureMessage, captureUserAction } from '@/lib/sentry';

export function SentryTestComponent() {
  const [testResult, setTestResult] = useState<string>('');

  const testClientError = () => {
    try {
      captureUserAction('sentry_test_started', { testType: 'client_error' });
      throw new Error('This is a test client error from GameChat AI');
    } catch (error) {
      captureAPIError(error as Error, {
        testContext: 'manual_error_test',
        timestamp: new Date().toISOString()
      });
      setTestResult('Client error sent to Sentry successfully!');
    }
  };

  const testMessage = () => {
    captureUserAction('sentry_test_started', { testType: 'message' });
    captureMessage('Test message from GameChat AI frontend', 'info');
    setTestResult('Test message sent to Sentry successfully!');
  };

  const testUserAction = () => {
    captureUserAction('sentry_manual_test', {
      action: 'button_click',
      component: 'sentry_test',
      timestamp: new Date().toISOString()
    });
    setTestResult('User action tracked in Sentry successfully!');
  };

  if (process.env.NODE_ENV === 'production') {
    return null; // 本番環境では表示しない
  }

  return (
    <div className="p-4 border border-dashed border-gray-300 rounded-lg m-4">
      <h3 className="text-lg font-semibold mb-4">Sentry Test Panel (Development Only)</h3>
      
      <div className="space-y-2 mb-4">
        <button
          onClick={testClientError}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 mr-2"
        >
          Test Error Tracking
        </button>
        
        <button
          onClick={testMessage}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 mr-2"
        >
          Test Message Logging
        </button>
        
        <button
          onClick={testUserAction}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Test User Action
        </button>
      </div>
      
      {testResult && (
        <div className="p-2 bg-green-100 border border-green-300 rounded text-green-800">
          {testResult}
        </div>
      )}
      
      <p className="text-sm text-gray-600 mt-2">
        テストボタンをクリックしてSentryダッシュボードでイベントを確認してください。
      </p>
    </div>
  );
}
