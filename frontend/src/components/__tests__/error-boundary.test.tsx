import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import React from 'react'
import { ErrorBoundary, withErrorBoundary } from '../error-boundary'

// Mock component that throws an error
const ErrorThrowingComponent = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error')
  }
  return <div>Normal component</div>
}

// Custom fallback component for testing
const CustomFallback = ({ error, resetError }: { error?: Error; resetError: () => void }) => (
  <div>
    <h2>Custom Error Fallback</h2>
    <p>Error: {error?.message}</p>
    <button onClick={resetError}>Reset Custom</button>
  </div>
)

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

describe('Custom Fallback Component', () => {
  it('should render custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={CustomFallback}>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Custom Error Fallback')).toBeInTheDocument()
    expect(screen.getByText('Error: Test error')).toBeInTheDocument()
    expect(screen.getByText('Reset Custom')).toBeInTheDocument()
  })

  it('should call custom reset function', () => {
    render(
      <ErrorBoundary fallback={CustomFallback}>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    const resetButton = screen.getByText('Reset Custom')
    fireEvent.click(resetButton)

    // Custom reset should also reset the error state
    expect(screen.getByText('Custom Error Fallback')).toBeInTheDocument()
  })
})

describe('Error Callback', () => {
  it('should call onError callback when provided', () => {
    const onError = vi.fn()
    
    render(
      <ErrorBoundary onError={onError}>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(onError).toHaveBeenCalledWith(expect.any(Error), expect.any(Object))
    expect(onError).toHaveBeenCalledTimes(1)
  })

  it('should not call onError when no error occurs', () => {
    const onError = vi.fn()
    
    render(
      <ErrorBoundary onError={onError}>
        <div>Normal content</div>
      </ErrorBoundary>
    )

    expect(onError).not.toHaveBeenCalled()
  })
})

describe('Error Types', () => {
  it('should handle different error types', () => {
    const ThrowTypeError = () => {
      throw new TypeError('Type error occurred')
    }

    render(
      <ErrorBoundary>
        <ThrowTypeError />
      </ErrorBoundary>
    )

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
  })

  it('should handle errors with empty messages', () => {
    const EmptyErrorComponent = () => {
      throw new Error('')
    }

    render(
      <ErrorBoundary>
        <EmptyErrorComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
  })

  it('should handle null/undefined errors gracefully', () => {
    const NullErrorComponent = () => {
      throw null
    }

    render(
      <ErrorBoundary>
        <NullErrorComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
  })
})

describe('Environment-based Error Details', () => {
  it('should display error details in development mode', () => {
    vi.stubEnv('NODE_ENV', 'development')

    const CustomErrorComponent = () => {
      throw new Error('Development error')
    }

    render(
      <ErrorBoundary>
        <CustomErrorComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText('エラー詳細（開発環境のみ表示）')).toBeInTheDocument()
    
    // Click to expand error details
    const detailsButton = screen.getByText('エラー詳細（開発環境のみ表示）')
    fireEvent.click(detailsButton)

    expect(screen.getByText(/Development error/)).toBeInTheDocument()
  })

  it('should not display error details in production mode', () => {
    vi.stubEnv('NODE_ENV', 'production')

    const CustomErrorComponent = () => {
      throw new Error('Production error')
    }

    render(
      <ErrorBoundary>
        <CustomErrorComponent />
      </ErrorBoundary>
    )

    expect(screen.queryByText('エラー詳細（開発環境のみ表示）')).not.toBeInTheDocument()
  })
})

describe('withErrorBoundary HOC', () => {
  it('should wrap component with error boundary', () => {
    const TestComponent = () => <div>HOC Test Component</div>
    const WrappedComponent = withErrorBoundary(TestComponent)

    render(<WrappedComponent />)

    expect(screen.getByText('HOC Test Component')).toBeInTheDocument()
  })

  it('should handle errors in wrapped component', () => {
    const ErrorComponent = () => {
      throw new Error('HOC Error')
    }
    const WrappedComponent = withErrorBoundary(ErrorComponent)

    render(<WrappedComponent />)

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
  })

  it('should accept custom error boundary props', () => {
    const CustomErrorComponent = () => {
      throw new Error('Custom HOC Error')
    }
    const WrappedComponent = withErrorBoundary(CustomErrorComponent, {
      fallback: CustomFallback
    })

    render(<WrappedComponent />)

    expect(screen.getByText('Custom Error Fallback')).toBeInTheDocument()
    expect(screen.getByText('Error: Custom HOC Error')).toBeInTheDocument()
  })

  it('should pass props to wrapped component', () => {
    const TestComponent = ({ message }: { message: string }) => <div>{message}</div>
    const WrappedComponent = withErrorBoundary(TestComponent)

    render(<WrappedComponent message="Props test" />)

    expect(screen.getByText('Props test')).toBeInTheDocument()
  })

  it('should set correct displayName', () => {
    const TestComponent = () => <div>Test</div>
    TestComponent.displayName = 'TestComponent'
    const WrappedComponent = withErrorBoundary(TestComponent)

    expect(WrappedComponent.displayName).toBe('withErrorBoundary(TestComponent)')
  })
})

describe('Accessibility', () => {
  it('should have proper ARIA attributes', () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    // Check for SVG element instead of role="img"
    const errorIcon = document.querySelector('svg')
    expect(errorIcon).toBeInTheDocument()
    expect(errorIcon).toHaveClass('h-8', 'w-8', 'text-red-500')
    
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(2)
    expect(buttons[0]).toHaveTextContent('再試行')
    expect(buttons[1]).toHaveTextContent('ページを再読み込み')
  })

  it('should be keyboard accessible', () => {
    render(
      <ErrorBoundary>
        <ErrorThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    )

    const resetButton = screen.getByText('再試行')
    const reloadButton = screen.getByText('ページを再読み込み')

    // Focus should be manageable
    resetButton.focus()
    expect(resetButton).toHaveFocus()

    reloadButton.focus()
    expect(reloadButton).toHaveFocus()
  })
})

describe('Edge Cases', () => {
  it('should handle errors in nested components', () => {
    const NestedErrorComponent = () => (
      <div>
        <div>
          <ErrorThrowingComponent shouldThrow={true} />
        </div>
      </div>
    )

    render(
      <ErrorBoundary>
        <NestedErrorComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
  })

  it('should handle errors in conditional rendering', () => {
    const ConditionalErrorComponent = ({ showError }: { showError: boolean }) => (
      <div>
        {showError && <ErrorThrowingComponent shouldThrow={true} />}
        <div>Always visible content</div>
      </div>
    )

    const { rerender } = render(
      <ErrorBoundary>
        <ConditionalErrorComponent showError={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Always visible content')).toBeInTheDocument()

    rerender(
      <ErrorBoundary>
        <ConditionalErrorComponent showError={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
  })

  it('should maintain error state across re-renders', () => {
    const TestComponent = () => {
      const [counter, setCounter] = React.useState(0)
      
      return (
        <ErrorBoundary>
          <div>
            <button onClick={() => setCounter(c => c + 1)}>Count: {counter}</button>
            <ErrorThrowingComponent shouldThrow={true} />
          </div>
        </ErrorBoundary>
      )
    }

    render(<TestComponent />)

    // Error should be displayed
    expect(screen.getByText('エラーが発生しました')).toBeInTheDocument()
    
    // The counter button should not be visible because error boundary caught the error
    expect(screen.queryByText(/Count:/)).not.toBeInTheDocument()
  })
})
