import { describe, it, beforeEach, afterEach, vi, expect } from 'vitest'

// Sentry Next.jsモジュールのモック
const mockCaptureException = vi.fn()
const mockCaptureMessage = vi.fn()
const mockAddBreadcrumb = vi.fn()
const mockSetUser = vi.fn()
const mockSetTag = vi.fn()
const mockSetContext = vi.fn()
const mockWithScope = vi.fn()
const mockStartSpan = vi.fn()

// スコープのモック
const mockScope = {
  setTag: vi.fn(),
  setLevel: vi.fn(),
  setContext: vi.fn(),
  setFingerprint: vi.fn(),
}

// Sentryモジュールのモック
vi.mock('@sentry/nextjs', () => ({
  captureException: mockCaptureException,
  captureMessage: mockCaptureMessage,
  addBreadcrumb: mockAddBreadcrumb,
  setUser: mockSetUser,
  setTag: mockSetTag,
  setContext: mockSetContext,
  withScope: mockWithScope,
  startSpan: mockStartSpan,
}))

// テスト対象のモジュール
import {
  captureAPIError,
  captureUserAction,
  startPerformanceTransaction,
  withPerformanceSpan,
  setSentryUser,
  captureMessage,
  setSentryTag,
  setSentryContext,
  testProductionMonitoring,
  captureProductionError,
  recordBusinessMetric,
} from '../sentry'

describe('Sentry Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // withScopeのモック設定
    mockWithScope.mockImplementation((callback) => {
      callback(mockScope)
    })
    // startSpanのモック設定
    mockStartSpan.mockImplementation((config, callback) => {
      if (typeof callback === 'function') {
        return callback(mockScope)
      }
      return Promise.resolve(mockScope)
    })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('captureAPIError', () => {
    it('should capture API error with context', async () => {
      const error = new Error('API Error')
      const context = { endpoint: '/api/test', method: 'GET' }

      captureAPIError(error, context)

      // dynamic importの完了を待つ
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockWithScope).toHaveBeenCalledWith(expect.any(Function))
      expect(mockScope.setTag).toHaveBeenCalledWith('error_type', 'api_error')
      expect(mockScope.setLevel).toHaveBeenCalledWith('error')
      expect(mockScope.setContext).toHaveBeenCalledWith('api_context', context)
      expect(mockCaptureException).toHaveBeenCalledWith(error)
    })

    it('should capture API error without context', async () => {
      const error = new Error('API Error')

      captureAPIError(error)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockWithScope).toHaveBeenCalledWith(expect.any(Function))
      expect(mockScope.setTag).toHaveBeenCalledWith('error_type', 'api_error')
      expect(mockScope.setLevel).toHaveBeenCalledWith('error')
      expect(mockScope.setContext).not.toHaveBeenCalled()
      expect(mockCaptureException).toHaveBeenCalledWith(error)
    })

    it('should not capture error on server side', () => {
      // window を undefined にする
      const originalWindow = global.window
      // @ts-expect-error テスト用にwindowを削除
      delete global.window

      const error = new Error('API Error')
      captureAPIError(error)

      expect(mockWithScope).not.toHaveBeenCalled()
      expect(mockCaptureException).not.toHaveBeenCalled()

      // window を復元
      global.window = originalWindow
    })
  })

  describe('captureUserAction', () => {
    it('should record user action with data', async () => {
      const action = 'button_click'
      const data = { buttonId: 'submit', page: 'form' }

      captureUserAction(action, data)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockAddBreadcrumb).toHaveBeenCalledWith({
        message: action,
        level: 'info',
        data,
      })
    })

    it('should record user action without data', async () => {
      const action = 'page_view'

      captureUserAction(action)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockAddBreadcrumb).toHaveBeenCalledWith({
        message: action,
        level: 'info',
        data: undefined,
      })
    })
  })

  describe('startPerformanceTransaction', () => {
    it('should start performance transaction', async () => {
      const name = 'test-transaction'
      const operation = 'test-operation'

      const result = await startPerformanceTransaction(name, operation)

      expect(mockStartSpan).toHaveBeenCalledWith({
        name,
        op: operation,
      }, expect.any(Function))
      expect(result).toBe(mockScope)
    })

    it('should return null on server side', async () => {
      const originalWindow = global.window
      // @ts-expect-error テスト用にwindowを削除
      delete global.window

      const result = await startPerformanceTransaction('test', 'test')

      expect(result).toBeNull()
      expect(mockStartSpan).not.toHaveBeenCalled()

      global.window = originalWindow
    })
  })

  describe('withPerformanceSpan', () => {
    it('should execute function with performance span', async () => {
      const name = 'test-span'
      const operation = 'test-op'
      const testFn = vi.fn().mockResolvedValue('test-result')

      const result = await withPerformanceSpan(name, operation, testFn)

      expect(mockStartSpan).toHaveBeenCalledWith({ name, op: operation }, testFn)
      expect(result).toBe('test-result')
    })

    it('should execute function without span on server side', async () => {
      const originalWindow = global.window
      // @ts-expect-error テスト用にwindowを削除
      delete global.window

      const testFn = vi.fn().mockResolvedValue('test-result')
      const result = await withPerformanceSpan('test', 'test', testFn)

      expect(result).toBe('test-result')
      expect(testFn).toHaveBeenCalled()
      expect(mockStartSpan).not.toHaveBeenCalled()

      global.window = originalWindow
    })
  })

  describe('setSentryUser', () => {
    it('should set user information', async () => {
      const user = { id: '123', email: 'test@example.com', username: 'testuser' }

      setSentryUser(user)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockSetUser).toHaveBeenCalledWith(user)
    })
  })

  describe('captureMessage', () => {
    it('should capture message with default level', async () => {
      const message = 'Test message'

      captureMessage(message)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockCaptureMessage).toHaveBeenCalledWith(message, 'info')
    })

    it('should capture message with custom level', async () => {
      const message = 'Error message'
      const level = 'error'

      captureMessage(message, level)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockCaptureMessage).toHaveBeenCalledWith(message, level)
    })
  })

  describe('setSentryTag', () => {
    it('should set tag', async () => {
      const key = 'feature'
      const value = 'chat'

      setSentryTag(key, value)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockSetTag).toHaveBeenCalledWith(key, value)
    })
  })

  describe('setSentryContext', () => {
    it('should set context', async () => {
      const key = 'user_action'
      const context = { action: 'click', target: 'button' }

      setSentryContext(key, context)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockSetContext).toHaveBeenCalledWith(key, context)
    })
  })

  describe('testProductionMonitoring', () => {
    it('should run monitoring tests in development environment', async () => {
      // 環境変数をモック
      vi.stubEnv('NODE_ENV', 'development')

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      testProductionMonitoring()

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(consoleSpy).toHaveBeenCalledWith('🧪 Testing Sentry error monitoring...')
      expect(consoleSpy).toHaveBeenCalledWith('🧪 Testing Sentry performance monitoring...')
      expect(consoleSpy).toHaveBeenCalledWith('🧪 Testing Sentry user action tracking...')
      expect(consoleSpy).toHaveBeenCalledWith('✅ Sentry monitoring test completed')
      expect(mockCaptureException).toHaveBeenCalledWith(expect.any(Error))
      expect(mockStartSpan).toHaveBeenCalledWith({ name: 'test-transaction', op: 'test' }, expect.any(Function))

      consoleSpy.mockRestore()
      vi.unstubAllEnvs()
    })

    it('should not run monitoring tests in production environment', () => {
      // 環境変数をモック
      vi.stubEnv('NODE_ENV', 'production')

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      testProductionMonitoring()

      expect(consoleSpy).not.toHaveBeenCalled()

      consoleSpy.mockRestore()
      vi.unstubAllEnvs()
    })
  })

  describe('captureProductionError', () => {
    it('should capture production error with default severity', async () => {
      const error = new Error('Production error')

      captureProductionError(error)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockWithScope).toHaveBeenCalledWith(expect.any(Function))
      expect(mockScope.setTag).toHaveBeenCalledWith('severity', 'medium')
      expect(mockScope.setTag).toHaveBeenCalledWith('environment', process.env.NODE_ENV)
      expect(mockScope.setLevel).toHaveBeenCalledWith('error')
      expect(mockCaptureException).toHaveBeenCalledWith(error)
    })

    it('should capture critical error with fatal level', async () => {
      const error = new Error('Critical error')
      const severity = 'critical'
      const context = { feature: 'payment' }

      captureProductionError(error, severity, context)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockScope.setTag).toHaveBeenCalledWith('severity', severity)
      expect(mockScope.setLevel).toHaveBeenCalledWith('fatal')
      expect(mockScope.setFingerprint).toHaveBeenCalledWith(['critical', error.name, error.message])
      expect(mockScope.setContext).toHaveBeenCalledWith('error_context', context)
      expect(mockCaptureException).toHaveBeenCalledWith(error)
    })

    it('should capture high severity error with error level', async () => {
      const error = new Error('High severity error')
      const severity = 'high'

      captureProductionError(error, severity)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockScope.setTag).toHaveBeenCalledWith('severity', severity)
      expect(mockScope.setLevel).toHaveBeenCalledWith('error')
      expect(mockScope.setFingerprint).not.toHaveBeenCalled()
    })
  })

  describe('recordBusinessMetric', () => {
    it('should record business metric with default unit', async () => {
      const metricName = 'user_signup'
      const value = 1

      recordBusinessMetric(metricName, value)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockAddBreadcrumb).toHaveBeenCalledWith({
        message: `Metric: ${metricName}`,
        level: 'info',
        data: {
          value,
          unit: 'count',
        },
        category: 'metric',
      })
    })

    it('should record business metric with custom unit and tags', async () => {
      const metricName = 'response_time'
      const value = 150
      const unit = 'milliseconds'
      const tags = { endpoint: '/api/chat', method: 'POST' }

      recordBusinessMetric(metricName, value, unit, tags)

      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockAddBreadcrumb).toHaveBeenCalledWith({
        message: `Metric: ${metricName}`,
        level: 'info',
        data: {
          value,
          unit,
          ...tags,
        },
        category: 'metric',
      })
    })
  })
})
