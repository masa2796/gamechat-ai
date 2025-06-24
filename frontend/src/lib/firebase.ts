// Firebase設定と初期化
import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import { getAuth, Auth } from "firebase/auth";

// Firebase設定（環境変数から取得）
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

// Firebase初期化（サーバーサイドでは無効化、CI環境では安全に初期化）
let app: FirebaseApp | null = null;
let auth: Auth | null = null;

// Firebase初期化の条件チェック
const shouldInitializeFirebase = () => {
  // CI環境では初期化しない
  if (process.env.CI === 'true' || process.env.NODE_ENV === 'test') {
    return false;
  }
  
  // ビルド時（サーバーサイド）では初期化しない
  if (typeof window === 'undefined') {
    return false;
  }
  
  // ダミー値の場合は初期化しない
  if (!firebaseConfig.apiKey || 
      firebaseConfig.apiKey.includes('dummy') || 
      firebaseConfig.apiKey.includes('Dummy') ||
      firebaseConfig.projectId === 'dummy-project') {
    return false;
  }
  
  // 必須設定が不足している場合は初期化しない
  if (!firebaseConfig.authDomain || !firebaseConfig.projectId) {
    return false;
  }
  
  return true;
};

// クライアントサイドでのみFirebaseを初期化
if (shouldInitializeFirebase()) {
  try {
    app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
    auth = getAuth(app);
    console.log('Firebase initialized successfully');
  } catch (error) {
    console.warn('Firebase initialization failed:', error);
    // エラーが発生してもアプリケーションを停止させない
    app = null;
    auth = null;
  }
} else {
  console.log('Firebase initialization skipped (CI/build environment or dummy configuration)');
}

export { auth, app };

// CI/ビルド環境用のダミーオブジェクトもエクスポート
export const firebaseAuth = auth;
export const firebaseApp = app;

// Firebase設定の状態をエクスポート（デバッグ用）
export const isFirebaseInitialized = !!app && !!auth;
export const firebaseInitStatus = {
  isInitialized: isFirebaseInitialized,
  isCIEnvironment: process.env.CI === 'true' || process.env.NODE_ENV === 'test',
  isServerSide: typeof window === 'undefined',
  hasValidConfig: shouldInitializeFirebase()
};
