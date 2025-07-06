import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useIsMobile } from '../use-mobile'

type ListenerMap = { change: Array<(e: { matches: boolean }) => void> }

describe('useIsMobile', () => {
  const originalMatchMedia = window.matchMedia
  const originalInnerWidth = window.innerWidth
  let listeners: ListenerMap = { change: [] }

  beforeEach(() => {
    listeners = { change: [] }
    window.matchMedia = vi.fn().mockImplementation((_query: string) => {
      return {
        matches: window.innerWidth < 768,
        addEventListener: (event: keyof ListenerMap, cb: (e: { matches: boolean }) => void) => {
          listeners[event].push(cb)
        },
        removeEventListener: (event: keyof ListenerMap, cb: (e: { matches: boolean }) => void) => {
          listeners[event] = listeners[event].filter((fn) => fn !== cb)
        },
      }
    })
  })
  afterEach(() => {
    window.matchMedia = originalMatchMedia
    Object.defineProperty(window, 'innerWidth', { value: originalInnerWidth, configurable: true })
  })

  it('モバイル判定: 767px以下でtrue', () => {
    Object.defineProperty(window, 'innerWidth', { value: 500, configurable: true })
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(true)
  })

  it('PC判定: 768px以上でfalse', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1024, configurable: true })
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(false)
  })

  it('ウィンドウ幅変更時に値が変わる', () => {
    Object.defineProperty(window, 'innerWidth', { value: 500, configurable: true })
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(true)
    // 画面幅をPCサイズに変更し、changeイベント発火
    Object.defineProperty(window, 'innerWidth', { value: 900, configurable: true })
    act(() => {
      listeners.change.forEach((cb) => cb({ matches: false }))
    })
    expect(result.current).toBe(false)
  })

  it('matchMedia未定義時でも例外を投げずfalse', () => {
    // @ts-expect-error matchMedia is deleted for this test to simulate missing API
    delete window.matchMedia
    const { result } = renderHook(() => useIsMobile())
    expect(typeof result.current).toBe('boolean')
  })

  it('addEventListenerが例外を投げても例外伝播しない', () => {
    window.matchMedia = vi.fn().mockImplementation(() => ({
      addEventListener: () => { throw new Error('fail') },
      removeEventListener: () => {},
      matches: false,
    }))
    expect(() => {
      renderHook(() => useIsMobile())
    }).not.toThrow()
  })

  it('返り値はboolean型である', () => {
    Object.defineProperty(window, 'innerWidth', { value: 400, configurable: true })
    const { result } = renderHook(() => useIsMobile())
    expect(typeof result.current).toBe('boolean')
  })
})
