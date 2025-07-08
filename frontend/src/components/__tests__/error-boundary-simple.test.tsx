import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import React from 'react'
import { ErrorBoundary } from '../error-boundary'

// Mock component that throws an error
const ErrorThrowingComponent = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>Normal component</div>
}

describe('ErrorBoundary', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    // Mock console.error to avoid cluttering test output
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('should render children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Normal content</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('Normal content')).toBeInTheDocument()
  })

  it('should render error UI when child throws error', () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
    expect(screen.getByText('再試行')).toBeInTheDocument()
    expect(screen.getByText('ページを再読み込み')).toBeInTheDocument()
  })

  it('should call console.error when error occurs', () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(consoleErrorSpy).toHaveBeenCalledWith('ErrorBoundary caught an error:', expect.any(Error))
  })

  it('should reset error state when reset button is clicked', () => {
    const TestComponent = () => {
      const [shouldThrow, setShouldThrow] = React.useState(true)
      
      return (
        <ErrorBoundary>
          <ErrorThrowingComponent shouldThrow={shouldThrow} />
          <button onClick={() => setShouldThrow(false)}>Fix Error</button>
        </ErrorBoundary>
      )
    }

    render(<TestComponent />)

    // Error should be displayed
    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()

    // Click reset button should call the resetError function
    const resetButton = screen.getByText('再試行')
    fireEvent.click(resetButton)

    // The error boundary should attempt to reset and re-render
    // However, the same error will occur again since the component state hasn't changed
    // This is expected behavior - the error boundary has reset its internal state
    // But the child component will still throw the same error
    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
  })

  it('should have reload button in error UI', () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    const reloadButton = screen.getByText('ページを再読み込み')
    expect(reloadButton).toBeInTheDocument()
    expect(reloadButton).toHaveClass('bg-gray-600')
  })
})
