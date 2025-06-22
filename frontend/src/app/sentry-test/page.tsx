'use client';

import React from 'react';

export default function SentryTestPage() {
  const handleError = () => {
    throw new Error('This is a test error for Sentry');
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">Sentry Test Page</h1>
      <p className="mb-4">This page is used to test Sentry error reporting.</p>
      <button
        onClick={handleError}
        className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
      >
        Trigger Test Error
      </button>
    </div>
  );
}