'use client';
import { useState, useEffect } from 'react';
import { X, Download } from 'lucide-react';
import { usePWA } from '@/hooks/use-pwa';
export function PWAInstallBanner() {
    const [deferredPrompt, setDeferredPrompt] = useState(null);
    const [showBanner, setShowBanner] = useState(false);
    const { isInstalled } = usePWA();
    useEffect(() => {
        // テスト環境では PWA バナーを表示しない
        const isTestEnvironment = process.env.NEXT_PUBLIC_ENVIRONMENT === 'test' ||
            process.env.NODE_ENV === 'test' ||
            typeof window !== 'undefined' && window.location.href.includes('localhost:3000');
        if (isTestEnvironment) {
            setShowBanner(false);
            return;
        }
        const handler = (e) => {
            // デフォルトのブラウザプロンプトを防ぐ
            e.preventDefault();
            setDeferredPrompt(e);
            // インストール済みでない場合のみバナーを表示
            if (!isInstalled) {
                setShowBanner(true);
            }
        };
        window.addEventListener('beforeinstallprompt', handler);
        // iOS Safari用の判定
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        const isInStandaloneMode = ('standalone' in window.navigator) && window.navigator.standalone;
        if (isIOS && !isInStandaloneMode && !isInstalled) {
            setShowBanner(true);
        }
        return () => {
            window.removeEventListener('beforeinstallprompt', handler);
        };
    }, [isInstalled]);
    const handleInstall = async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                console.log('PWA install accepted');
            }
            setDeferredPrompt(null);
            setShowBanner(false);
        }
    };
    const handleDismiss = () => {
        setShowBanner(false);
        // 24時間後に再表示するためのフラグをローカルストレージに保存
        localStorage.setItem('pwa-banner-dismissed', Date.now().toString());
    };
    // 24時間以内に却下されている場合は表示しない
    useEffect(() => {
        const dismissed = localStorage.getItem('pwa-banner-dismissed');
        if (dismissed) {
            const dismissedTime = parseInt(dismissed);
            const now = Date.now();
            const dayInMs = 24 * 60 * 60 * 1000;
            if (now - dismissedTime < dayInMs) {
                setShowBanner(false);
            }
        }
    }, []);
    if (!showBanner || isInstalled) {
        return null;
    }
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    return (<div className="fixed bottom-4 left-4 right-4 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 max-w-sm mx-auto">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center">
              <span className="text-white text-sm">🎮</span>
            </div>
            <div>
              <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                GameChat AIをインストール
              </h3>
            </div>
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-300 mb-3">
            {isIOS
            ? 'Safariの共有ボタンから「ホーム画面に追加」でインストールできます'
            : 'ホーム画面に追加して、いつでもすぐにアクセス'}
          </p>
          {!isIOS && deferredPrompt && (<button onClick={handleInstall} className="flex items-center space-x-1 bg-blue-500 hover:bg-blue-600 text-white text-xs px-3 py-1.5 rounded-md transition-colors">
              <Download className="w-3 h-3"/>
              <span>インストール</span>
            </button>)}
        </div>
        <button onClick={handleDismiss} className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 ml-2">
          <X className="w-4 h-4"/>
        </button>
      </div>
    </div>);
}
