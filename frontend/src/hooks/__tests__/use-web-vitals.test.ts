import { renderHook } from '@testing-library/react'
import { describe, it, beforeEach, afterEach, vi, expect } from 'vitest'

// web-vitalsのトップレベルモック
vi.mock('web-vitals', () => {
  return {
    onCLS: vi.fn((cb: (metric: any) => void) => cb({ name: 'CLS', value: 0.1, id: '1', rating: 'good' })),
    onLCP: vi.fn((cb: (metric: any) => void) => cb({ name: 'LCP', value: 1.2, id: '2', rating: 'good' })),
    onFCP: vi.fn(),
    onTTFB: vi.fn(),
    onINP: vi.fn(),
  }
})

describe('useWebVitals', () => {
  const origConsoleLog = console.log
  let origTestEnv: unknown
  let origLocation: Location | undefined
  let origNavigator: Navigator | undefined

  beforeEach(() => {
    if (!('__TEST_ENV__' in globalThis)) {
      (globalThis as any).__TEST_ENV__ = undefined
    }
    origTestEnv = (globalThis as any).__TEST_ENV__
    delete (globalThis as any).webVitals
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    }))
    console.log = vi.fn()
    origLocation = global.window.location
    origNavigator = global.window.navigator
    Object.defineProperty(global.window, 'location', {
      value: { href: 'http://localhost/' },
      writable: true,
    })
    Object.defineProperty(global.window, 'navigator', {
      value: { userAgent: 'test-agent' },
      writable: true,
    })
  })

  afterEach(() => {
    console.log = origConsoleLog
    if ('__TEST_ENV__' in globalThis) {
      (globalThis as any).__TEST_ENV__ = origTestEnv
    }
    if (origLocation) Object.defineProperty(global.window, 'location', { value: origLocation, writable: true })
    if (origNavigator) Object.defineProperty(global.window, 'navigator', { value: origNavigator, writable: true })
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('should register web-vitals metrics and call callback (development)', async () => {
    (globalThis as any).__TEST_ENV__ = 'development'
    ;(globalThis as any).webVitals = {
      getCLS: vi.fn(),
      getLCP: vi.fn(),
      getFID: vi.fn(),
      getFCP: vi.fn(),
      getTTFB: vi.fn(),
    }
    // ESM対応: await import
    const { useWebVitals } = await import('../use-web-vitals')
    renderHook(() => useWebVitals())
    await Promise.resolve()
    const webVitalsModule = await import('web-vitals')
    expect(webVitalsModule.onCLS).toHaveBeenCalled()
    expect(webVitalsModule.onLCP).toHaveBeenCalled()
    expect(console.log).toHaveBeenCalledWith('Web Vitals:', expect.objectContaining({ name: expect.any(String) }))
  })

  it('should call fetch in production', async () => {
    (globalThis as any).__TEST_ENV__ = 'production'
    ;(globalThis as any).webVitals = {
      getCLS: vi.fn(),
      getLCP: vi.fn(),
      getFID: vi.fn(),
      getFCP: vi.fn(),
      getTTFB: vi.fn(),
    }
    const { useWebVitals } = await import('../use-web-vitals')
    renderHook(() => useWebVitals())
    await Promise.resolve()
    const webVitalsModule = await import('web-vitals')
    expect(webVitalsModule.onCLS).toHaveBeenCalled()
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/performance',
      expect.objectContaining({
        method: 'POST',
        headers: expect.any(Object),
        body: expect.any(String),
      })
    )
  })
})
