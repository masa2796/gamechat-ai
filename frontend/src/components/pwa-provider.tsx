"use client";

import { usePWA } from "@/hooks/use-pwa";
import { useWebVitals } from "@/hooks/use-web-vitals";
import { GlobalErrorHandler } from "@/components/global-error-handler";
import { PWAInstallBanner } from "@/components/pwa-install-banner";

export function PWAProvider({ children }: { children: React.ReactNode }) {
  // Initialize PWA functionality
  usePWA();
  
  // Initialize Web Vitals measurement
  useWebVitals();

  return (
    <>
      <GlobalErrorHandler />
      <PWAInstallBanner />
      {children}
    </>
  );
}
