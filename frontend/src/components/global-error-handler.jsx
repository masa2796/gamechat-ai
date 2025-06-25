"use client";
import { useEffect } from 'react';
export function GlobalErrorHandler() {
    useEffect(() => {
        // Handle unhandled promise rejections
        const handleUnhandledRejection = (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            // In production, you might want to send this to an error reporting service
            if (process.env.NODE_ENV === 'production') {
                // sendErrorToService(new Error(event.reason), { type: 'unhandledRejection' });
            }
            // Prevent the default handling (which would log the error to console again)
            event.preventDefault();
        };
        // Handle uncaught errors
        const handleError = (event) => {
            console.error('Uncaught error:', event.error);
            // In production, you might want to send this to an error reporting service
            if (process.env.NODE_ENV === 'production') {
                // sendErrorToService(event.error, { type: 'uncaughtError' });
            }
        };
        // Add event listeners
        window.addEventListener('unhandledrejection', handleUnhandledRejection);
        window.addEventListener('error', handleError);
        // Cleanup
        return () => {
            window.removeEventListener('unhandledrejection', handleUnhandledRejection);
            window.removeEventListener('error', handleError);
        };
    }, []);
    return null; // This component doesn't render anything
}
