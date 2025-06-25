"use client";
import React from 'react';
export class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.resetError = () => {
            this.setState({ hasError: false, error: undefined, errorInfo: undefined });
        };
        this.state = { hasError: false };
    }
    static getDerivedStateFromError(error) {
        return {
            hasError: true,
            error,
        };
    }
    componentDidCatch(error, errorInfo) {
        console.error('ErrorBoundary caught an error:', error);
        console.error('Error Info:', errorInfo);
        // Call custom error handler if provided
        if (this.props.onError) {
            this.props.onError(error, errorInfo);
        }
        // In production, you might want to send this to an error reporting service
        if (process.env.NODE_ENV === 'production') {
            // Example: Send to monitoring service
            // sendErrorToService(error, errorInfo);
        }
        this.setState({
            error,
            errorInfo,
        });
    }
    render() {
        if (this.state.hasError) {
            // Custom fallback component
            if (this.props.fallback) {
                const FallbackComponent = this.props.fallback;
                return <FallbackComponent error={this.state.error} resetError={this.resetError}/>;
            }
            // Default error UI
            return <DefaultErrorFallback error={this.state.error} resetError={this.resetError}/>;
        }
        return this.props.children;
    }
}
// Default error fallback component
function DefaultErrorFallback({ error, resetError }) {
    return (<div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-4">
            <div className="flex-shrink-0">
              <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.966-.833-2.732 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z"/>
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                エラーが発生しました
              </h3>
            </div>
          </div>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              申し訳ございません。予期しないエラーが発生しました。ページを再読み込みするか、しばらく時間をおいてから再度お試しください。
            </p>
            
            {process.env.NODE_ENV === 'development' && error && (<details className="mt-4">
                <summary className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">
                  エラー詳細（開発環境のみ表示）
                </summary>
                <pre className="mt-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded overflow-auto">
                  {error.toString()}
                  {error.stack && (<>
                      {'\n\nStack trace:\n'}
                      {error.stack}
                    </>)}
                </pre>
              </details>)}
          </div>

          <div className="flex space-x-3">
            <button onClick={resetError} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
              再試行
            </button>
            <button onClick={() => window.location.reload()} className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2">
              ページを再読み込み
            </button>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              問題が解決しない場合は、サポートまでお問い合わせください。
            </p>
          </div>
        </div>
      </div>
    </div>);
}
// Hook for functional components
export function useErrorHandler() {
    return (error, errorInfo) => {
        console.error('Uncaught error:', error);
        if (errorInfo) {
            console.error('Error info:', errorInfo);
        }
        // In production, send to error reporting service
        if (process.env.NODE_ENV === 'production') {
            // sendErrorToService(error, errorInfo);
        }
    };
}
// HOC for wrapping components with error boundary
export function withErrorBoundary(Component, errorBoundaryProps) {
    const WrappedComponent = (props) => (<ErrorBoundary {...errorBoundaryProps}>
      <Component {...props}/>
    </ErrorBoundary>);
    WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
    return WrappedComponent;
}
