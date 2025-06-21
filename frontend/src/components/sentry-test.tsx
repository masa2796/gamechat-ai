'use client';

import { useState, useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';

export function SentryTestComponent() {
  const [testResult, setTestResult] = useState<string>('');
  const [eventId, setEventId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    // Sentryの初期化状態を確認
    const checkSentryStatus = () => {
      const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
      const nodeEnv = process.env.NODE_ENV;
      
      if (!dsn) {
        setTestResult('❌ DSN not configured');
        return;
      }
      
      // Sentryクライアントの状態を確認
      try {
        // Sentryのクライアントが初期化されているかテスト
        Sentry.withScope((scope) => {
          if (scope) {
            setTestResult(`✅ Sentry client initialized (${nodeEnv})`);
          } else {
            setTestResult('❌ Sentry scope not available');
          }
        });
      } catch (error) {
        setTestResult('❌ Sentry client error: ' + String(error));
      }
    };

    checkSentryStatus();
  }, []);

  const testClientError = async () => {
    setIsLoading(true);
    setTestResult('Sending error to Sentry...');
    setEventId(null);
    try {
      Sentry.addBreadcrumb({
        message: 'Sentry test error triggered',
        level: 'info',
        data: { testType: 'client_error', timestamp: new Date().toISOString() }
      });
      Sentry.withScope((scope) => {
        scope.setTag('test_type', 'manual_error_test');
        scope.setTag('environment', process.env.NODE_ENV || 'development');
        scope.setLevel('error');
        scope.setContext('test_context', {
          component: 'SentryTestComponent',
          action: 'manual_error_test',
          timestamp: new Date().toISOString(),
          userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown'
        });
        const id = Sentry.captureException(new Error('🔥 Test error from GameChat AI - Sentry integration test'));
        setEventId(id as string);
      });
      setTestResult('✅ Client error sent to Sentry!');
    } catch (error) {
      setTestResult('❌ Failed to send error to Sentry');
    } finally {
      setIsLoading(false);
    }
  };

  const testMessage = async () => {
    setIsLoading(true);
    setTestResult('Sending message to Sentry...');
    setEventId(null);
    try {
      Sentry.addBreadcrumb({
        message: 'Sentry test message triggered',
        level: 'info',
        data: { testType: 'message', timestamp: new Date().toISOString() }
      });
      Sentry.withScope((scope) => {
        scope.setTag('test_type', 'manual_message_test');
        scope.setTag('environment', process.env.NODE_ENV || 'development');
        scope.setLevel('info');
        scope.setContext('message_context', {
          component: 'SentryTestComponent',
          action: 'manual_message_test',
          timestamp: new Date().toISOString()
        });
        const id = Sentry.captureMessage('📨 Test message from GameChat AI frontend - Sentry integration test', 'info');
        setEventId(id as string);
      });
      setTestResult('✅ Test message sent to Sentry!');
    } catch (error) {
      setTestResult('❌ Failed to send message to Sentry');
    } finally {
      setIsLoading(false);
    }
  };

  const testUserAction = async () => {
    setIsLoading(true);
    setTestResult('Recording user action in Sentry...');
    setEventId(null);
    try {
      Sentry.withScope((scope) => {
        scope.setTag('test_type', 'user_action_test');
        scope.setTag('environment', process.env.NODE_ENV || 'development');
        scope.setLevel('info');
        Sentry.addBreadcrumb({
          message: '🎯 Manual user action test',
          level: 'info',
          data: {
            action: 'button_click',
            component: 'sentry_test',
            timestamp: new Date().toISOString(),
            test_id: `test_${Date.now()}`
          }
        });
        const id = Sentry.captureMessage('👤 User action tracked - Sentry integration test', 'info');
        setEventId(id as string);
      });
      setTestResult('✅ User action tracked in Sentry!');
    } catch (error) {
      setTestResult('❌ Failed to record user action in Sentry');
    } finally {
      setIsLoading(false);
    }
  };

  const testDirectSentry = async () => {
    setIsLoading(true);
    setTestResult('Testing direct Sentry connection...');
    setEventId(null);
    try {
      const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
      Sentry.withScope((scope) => {
        scope.setTag('test_type', 'direct_connection_test');
        scope.setContext('dsn', { dsn });
        const id = Sentry.captureException(new Error('🧪 Direct Sentry test - Connection verification'));
        setEventId(id as string);
      });
      setTestResult('✅ Direct Sentry test completed!');
    } catch (error) {
      setTestResult('❌ Direct Sentry test failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (process.env.NODE_ENV === 'production') {
    return null; // 本番環境では表示しない
  }

  return (
    <div className="p-4 border border-dashed border-orange-300 rounded-lg m-4 bg-orange-50">
      <h3 className="text-lg font-semibold mb-4 text-orange-800">
        🔧 Sentry Test Panel (Development Only)
      </h3>
      <div className="space-y-2 mb-4">
        <button
          onClick={testClientError}
          disabled={isLoading}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 mr-2 disabled:bg-gray-400"
        >
          {isLoading ? '送信中...' : '🔥 Test Error Tracking'}
        </button>
        <button
          onClick={testMessage}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 mr-2 disabled:bg-gray-400"
        >
          {isLoading ? '送信中...' : '📨 Test Message Logging'}
        </button>
        <button
          onClick={testUserAction}
          disabled={isLoading}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 mr-2 disabled:bg-gray-400"
        >
          {isLoading ? '送信中...' : '👤 Test User Action'}
        </button>
        <button
          onClick={testDirectSentry}
          disabled={isLoading}
          className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-400"
        >
          {isLoading ? '送信中...' : '🧪 Test Direct Connection'}
        </button>
      </div>
      {testResult && (
        <div className={`p-3 border rounded text-sm ${
          testResult.includes('✅') 
            ? 'bg-green-100 border-green-300 text-green-800' 
            : testResult.includes('❌')
            ? 'bg-red-100 border-red-300 text-red-800'
            : 'bg-blue-100 border-blue-300 text-blue-800'
        }`}>
          {testResult}
          {eventId && (
            <div className="mt-2 text-xs text-gray-700">Event ID: {eventId}</div>
          )}
        </div>
      )}
      <div className="text-sm text-gray-600 mt-4 space-y-1">
        <p>🔍 <strong>使用方法:</strong></p>
        <p>1. テストボタンをクリック</p>
        <p>2. ブラウザのDevToolsでコンソールログを確認</p>
        <p>3. Sentryダッシュボードでイベントを確認</p>
        <p>4. DSN: {process.env.NEXT_PUBLIC_SENTRY_DSN ? '設定済み ✅' : '未設定 ❌'}</p>
        <p>5. NODE_ENV: {process.env.NODE_ENV}</p>
      </div>
    </div>
  );
}
