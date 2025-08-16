"use client";

import { useEffect, useState } from 'react';

// Define BeforeInstallPromptEvent interface
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

declare global {
  interface Window {
    showInstallPrompt?: () => Promise<void>;
  }
}

export function usePWA() {
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    if (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      process.env.NODE_ENV === 'production'
    ) {
      // Check if already installed (standalone mode)
      const checkInstallStatus = () => {
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        const isInWebApp = ('standalone' in window.navigator) && (window.navigator as unknown as { standalone: boolean }).standalone === true;
        setIsInstalled(isStandalone || isInWebApp);
      };
      
      checkInstallStatus();

      const registerSW = async () => {
        try {
          const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/',
          });

          console.log('Service Worker registered successfully:', registration);

          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // New update available
                  if (confirm('新しいバージョンが利用可能です。更新しますか？')) {
                    window.location.reload();
                  }
                }
              });
            }
          });

        } catch (error: unknown) {
          if (error instanceof Error) {
            console.error('Service Worker registration failed:', error);
          } else {
            console.error('Service Worker registration failed:', String(error));
          }
        }
      };

      // Register on page load
      registerSW();

      // Handle PWA install prompt
      let deferredPrompt: BeforeInstallPromptEvent | null = null;

      const handleBeforeInstallPrompt = (e: Event) => {
        e.preventDefault();
        deferredPrompt = e as BeforeInstallPromptEvent;
        setIsInstallable(true);
      };

      window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

      // Expose install function globally for potential use
      window.showInstallPrompt = async () => {
        if (deferredPrompt) {
          await deferredPrompt.prompt();
          const { outcome } = await deferredPrompt.userChoice;
          console.log(`PWA install prompt outcome: ${outcome}`);
          deferredPrompt = null;
          setIsInstallable(false);
        }
      };

      return () => {
        window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      };
    }
  }, []);

  return { isInstallable, isInstalled };
}
