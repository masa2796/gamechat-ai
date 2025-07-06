import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { FirebaseApp } from 'firebase/app';
import type { Auth } from 'firebase/auth';
import type { Analytics } from 'firebase/analytics';

// Firebase SDKをモック化
vi.mock('firebase/app', () => ({
  initializeApp: vi.fn(),
  getApps: vi.fn(),
  getApp: vi.fn(),
}));

vi.mock('firebase/auth', () => ({
  getAuth: vi.fn(),
}));

vi.mock('firebase/analytics', () => ({
  getAnalytics: vi.fn(),
  isSupported: vi.fn(),
}));

describe('Firebase Configuration', () => {
  let originalWindow: typeof window;
  let originalConsole: typeof console;

  beforeEach(() => {
    // windowオブジェクトを保存
    originalWindow = globalThis.window;
    
    // console.logとconsole.warnをモック
    originalConsole = { ...console };
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    // モジュールキャッシュをクリア
    vi.resetModules();
  });

  afterEach(() => {
    // windowオブジェクトを復元
    globalThis.window = originalWindow;
    
    // consoleを復元
    console.log = originalConsole.log;
    console.warn = originalConsole.warn;
    
    // モックをリセット
    vi.restoreAllMocks();
  });

  describe('shouldInitializeFirebase logic', () => {
    it('should skip initialization in CI environment', async () => {
      vi.stubEnv('CI', 'true');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック（クライアント環境をシミュレート）
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      expect(firebase.firebaseInitStatus.isCIEnvironment).toBe(true);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
      expect(console.log).toHaveBeenCalledWith(
        'Firebase initialization skipped (CI/build environment or dummy configuration)'
      );
    });

    it('should skip initialization in test environment', async () => {
      vi.stubEnv('NODE_ENV', 'test');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      expect(firebase.firebaseInitStatus.isCIEnvironment).toBe(true);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });

    it('should skip initialization on server-side', async () => {
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトを削除（サーバーサイド環境をシミュレート）
      delete (globalThis as unknown as { window?: typeof window }).window;

      const firebase = await import('../firebase');
      
      expect(firebase.firebaseInitStatus.isServerSide).toBe(true);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });

    it('should skip initialization with dummy API key', async () => {
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'dummy-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      expect(firebase.firebaseInitStatus.hasValidConfig).toBe(false);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });

    it('should skip initialization with Dummy API key (capital D)', async () => {
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'Dummy-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      expect(firebase.firebaseInitStatus.hasValidConfig).toBe(false);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });

    it('should skip initialization with dummy project ID', async () => {
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'dummy-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      expect(firebase.firebaseInitStatus.hasValidConfig).toBe(false);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });

    it('should skip initialization with missing required fields', async () => {
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      // authDomainを明示的にundefinedに設定
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', undefined);
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      expect(firebase.firebaseInitStatus.hasValidConfig).toBe(false);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });
  });

  describe('Firebase initialization', () => {
    it('should initialize Firebase successfully with valid configuration', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      const { getAuth } = await import('firebase/auth');
      
      // モックのセットアップ
      const mockApp = { name: 'test-app' } as FirebaseApp;
      const mockAuth = { currentUser: null } as Auth;
      
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockReturnValue(mockApp);
      vi.mocked(getAuth).mockReturnValue(mockAuth);
      
      // 有効な設定
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET', 'test-bucket');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID', '123456789');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_APP_ID', '1:123456789:web:abcdef');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // Firebase初期化の関数が呼ばれることを確認
      expect(getApps).toHaveBeenCalled();
      expect(initializeApp).toHaveBeenCalledWith({
        apiKey: 'valid-key',
        authDomain: 'test.firebaseapp.com',
        projectId: 'test-project',
        storageBucket: 'test-bucket',
        messagingSenderId: '123456789',
        appId: '1:123456789:web:abcdef',
        measurementId: undefined,
      });
      expect(getAuth).toHaveBeenCalledWith(mockApp);
      
      // 成功ログが出力されることを確認
      expect(console.log).toHaveBeenCalledWith('Firebase initialized successfully');
      
      // エクスポートされた値を確認
      expect(firebase.firebaseInitStatus.isInitialized).toBe(true);
      expect(firebase.firebaseApp).toBe(mockApp);
      expect(firebase.firebaseAuth).toBe(mockAuth);
    });

    it('should use existing app when already initialized', async () => {
      const { getApps, getApp } = await import('firebase/app');
      const { getAuth } = await import('firebase/auth');
      
      // モックのセットアップ
      const mockApp = { name: 'existing-app' } as FirebaseApp;
      const mockAuth = { currentUser: null } as Auth;
      
      vi.mocked(getApps).mockReturnValue([mockApp]);
      vi.mocked(getApp).mockReturnValue(mockApp);
      vi.mocked(getAuth).mockReturnValue(mockAuth);
      
      // 有効な設定
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // 既存のアプリが使われることを確認
      expect(getApps).toHaveBeenCalled();
      expect(getApp).toHaveBeenCalled();
      expect(getAuth).toHaveBeenCalledWith(mockApp);
      
      expect(firebase.firebaseApp).toBe(mockApp);
      expect(firebase.firebaseAuth).toBe(mockAuth);
    });

    it('should handle initialization errors gracefully', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      
      // モックのセットアップ - 初期化エラーを発生させる
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockImplementation(() => {
        throw new Error('Firebase initialization failed');
      });
      
      // 有効な設定
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // エラーログが出力されることを確認
      expect(console.warn).toHaveBeenCalledWith(
        'Firebase initialization failed:',
        expect.any(Error)
      );
      
      // アプリケーションが停止しないことを確認
      expect(firebase.firebaseApp).toBe(null);
      expect(firebase.firebaseAuth).toBe(null);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });

    it('should handle non-Error exceptions gracefully', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      
      // モックのセットアップ - 非Errorオブジェクトを投げる
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockImplementation(() => {
        throw 'String error';
      });
      
      // 有効な設定
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // エラーログが出力されることを確認
      expect(console.warn).toHaveBeenCalledWith(
        'Firebase initialization failed:',
        'String error'
      );
      
      // アプリケーションが停止しないことを確認
      expect(firebase.firebaseApp).toBe(null);
      expect(firebase.firebaseAuth).toBe(null);
      expect(firebase.firebaseInitStatus.isInitialized).toBe(false);
    });
  });

  describe('Firebase exports', () => {
    it('should export all required Firebase objects', async () => {
      const firebase = await import('../firebase');
      
      // 必要なエクスポートが存在することを確認
      expect(firebase).toHaveProperty('auth');
      expect(firebase).toHaveProperty('app');
      expect(firebase).toHaveProperty('firebaseAuth');
      expect(firebase).toHaveProperty('firebaseApp');
      expect(firebase).toHaveProperty('isFirebaseInitialized');
      expect(firebase).toHaveProperty('firebaseInitStatus');
      
      // firebaseInitStatusの構造を確認
      expect(firebase.firebaseInitStatus).toHaveProperty('isInitialized');
      expect(firebase.firebaseInitStatus).toHaveProperty('isCIEnvironment');
      expect(firebase.firebaseInitStatus).toHaveProperty('isServerSide');
      expect(firebase.firebaseInitStatus).toHaveProperty('hasValidConfig');
    });

    it('should maintain consistency between auth exports', async () => {
      const firebase = await import('../firebase');
      
      // auth と firebaseAuth が同じオブジェクトを参照していることを確認
      expect(firebase.auth).toBe(firebase.firebaseAuth);
      expect(firebase.app).toBe(firebase.firebaseApp);
      expect(firebase.isFirebaseInitialized).toBe(firebase.firebaseInitStatus.isInitialized);
    });
  });

  describe('Firebase Analytics', () => {
    it('should initialize Analytics when measurementId is provided', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      const { getAuth } = await import('firebase/auth');
      const { getAnalytics, isSupported } = await import('firebase/analytics');
      
      // モックのセットアップ
      const mockApp = { name: 'test-app' } as FirebaseApp;
      const mockAuth = { currentUser: null } as Auth;
      const mockAnalytics = { app: mockApp } as Analytics;
      
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockReturnValue(mockApp);
      vi.mocked(getAuth).mockReturnValue(mockAuth);
      vi.mocked(isSupported).mockResolvedValue(true);
      vi.mocked(getAnalytics).mockReturnValue(mockAnalytics);
      
      // 有効な設定（measurementIdを含む）
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID', 'G-XXXXXXXXXX');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // Analytics初期化の確認（非同期処理のため少し待機）
      await new Promise(resolve => setTimeout(resolve, 10));
      
      expect(isSupported).toHaveBeenCalled();
      expect(getAnalytics).toHaveBeenCalledWith(mockApp);
      expect(console.log).toHaveBeenCalledWith('Firebase Analytics initialized successfully');
      
      // 初期化ステータスの確認
      expect(firebase.firebaseInitStatus.hasAnalyticsConfig).toBe(true);
    });

    it('should skip Analytics initialization when measurementId is not provided', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      const { getAuth } = await import('firebase/auth');
      const { getAnalytics, isSupported } = await import('firebase/analytics');
      
      // モックのセットアップ
      const mockApp = { name: 'test-app' } as FirebaseApp;
      const mockAuth = { currentUser: null } as Auth;
      
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockReturnValue(mockApp);
      vi.mocked(getAuth).mockReturnValue(mockAuth);
      
      // 有効な設定（measurementIdなし）
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      // measurementIdを明示的にundefinedに設定
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID', undefined);
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // Analytics初期化が呼ばれないことを確認
      expect(isSupported).not.toHaveBeenCalled();
      expect(getAnalytics).not.toHaveBeenCalled();
      
      // 初期化ステータスの確認
      expect(firebase.firebaseInitStatus.hasAnalyticsConfig).toBe(false);
      expect(firebase.firebaseAnalytics).toBe(null);
    });

    it('should handle Analytics initialization when not supported', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      const { getAuth } = await import('firebase/auth');
      const { getAnalytics, isSupported } = await import('firebase/analytics');
      
      // モックのセットアップ
      const mockApp = { name: 'test-app' } as FirebaseApp;
      const mockAuth = { currentUser: null } as Auth;
      
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockReturnValue(mockApp);
      vi.mocked(getAuth).mockReturnValue(mockAuth);
      vi.mocked(isSupported).mockResolvedValue(false); // サポートされていない
      
      // 有効な設定（measurementIdあり）
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID', 'G-XXXXXXXXXX');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // Analytics初期化の確認（非同期処理のため少し待機）
      await new Promise(resolve => setTimeout(resolve, 0));
      
      expect(isSupported).toHaveBeenCalled();
      expect(getAnalytics).not.toHaveBeenCalled();
      expect(console.log).toHaveBeenCalledWith('Firebase Analytics not supported in this environment');
      
      expect(firebase.firebaseAnalytics).toBe(null);
    });

    it('should handle Analytics support check errors', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      const { getAuth } = await import('firebase/auth');
      const { getAnalytics, isSupported } = await import('firebase/analytics');
      
      // モックのセットアップ
      const mockApp = { name: 'test-app' } as FirebaseApp;
      const mockAuth = { currentUser: null } as Auth;
      
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockReturnValue(mockApp);
      vi.mocked(getAuth).mockReturnValue(mockAuth);
      vi.mocked(isSupported).mockRejectedValue(new Error('Support check failed'));
      
      // 有効な設定（measurementIdあり）
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID', 'G-XXXXXXXXXX');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // Analytics初期化の確認（非同期処理のため少し待機）
      await new Promise(resolve => setTimeout(resolve, 0));
      
      expect(isSupported).toHaveBeenCalled();
      expect(getAnalytics).not.toHaveBeenCalled();
      expect(console.warn).toHaveBeenCalledWith(
        'Firebase Analytics support check failed:',
        expect.any(Error)
      );
      
      expect(firebase.firebaseAnalytics).toBe(null);
    });

    it('should have initAnalytics function available', async () => {
      // このテストでは、initAnalytics関数が存在することを確認します
      const firebase = await import('../firebase');
      
      // 関数が存在することを確認
      expect(firebase.initAnalytics).toBeInstanceOf(Function);
      
      // 関数が呼び出し可能であることを確認
      const result = await firebase.initAnalytics();
      
      // CI環境では初期化がスキップされるため、nullが返されることを確認
      expect(result).toBe(null);
    });

    it('should return null from initAnalytics when not supported', async () => {
      const { initializeApp, getApps } = await import('firebase/app');
      const { getAuth } = await import('firebase/auth');
      const { isSupported } = await import('firebase/analytics');
      
      // モックのセットアップ
      const mockApp = { name: 'test-app' } as FirebaseApp;
      const mockAuth = { currentUser: null } as Auth;
      
      vi.mocked(getApps).mockReturnValue([]);
      vi.mocked(initializeApp).mockReturnValue(mockApp);
      vi.mocked(getAuth).mockReturnValue(mockAuth);
      vi.mocked(isSupported).mockResolvedValue(false); // サポートされていない
      
      // 有効な設定（measurementIdあり）
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID', 'G-XXXXXXXXXX');
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // initAnalytics関数を呼び出し
      const result = await firebase.initAnalytics();
      
      expect(result).toBe(null);
      expect(isSupported).toHaveBeenCalled();
    });

    it('should return null from initAnalytics when config is invalid', async () => {
      // measurementIdがない場合
      vi.stubEnv('CI', 'false');
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'valid-key');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN', 'test.firebaseapp.com');
      vi.stubEnv('NEXT_PUBLIC_FIREBASE_PROJECT_ID', 'test-project');
      // measurementIdを設定しない
      
      // windowオブジェクトをモック
      Object.defineProperty(globalThis, 'window', {
        value: {},
        writable: true,
        configurable: true,
      });

      const firebase = await import('../firebase');
      
      // initAnalytics関数を呼び出し
      const result = await firebase.initAnalytics();
      
      expect(result).toBe(null);
    });
  });

  describe('Firebase exports with Analytics', () => {
    it('should export Analytics-related objects', async () => {
      const firebase = await import('../firebase');
      
      // Analytics関連のエクスポートが存在することを確認
      expect(firebase).toHaveProperty('analytics');
      expect(firebase).toHaveProperty('firebaseAnalytics');
      expect(firebase).toHaveProperty('isAnalyticsInitialized');
      expect(firebase).toHaveProperty('initAnalytics');
      
      // firebaseInitStatusにAnalytics関連の情報が含まれることを確認
      expect(firebase.firebaseInitStatus).toHaveProperty('isAnalyticsInitialized');
      expect(firebase.firebaseInitStatus).toHaveProperty('hasAnalyticsConfig');
      
      // analytics と firebaseAnalytics が同じオブジェクトを参照していることを確認
      expect(firebase.analytics).toBe(firebase.firebaseAnalytics);
      expect(firebase.isAnalyticsInitialized).toBe(firebase.firebaseInitStatus.isAnalyticsInitialized);
    });
  });
});
