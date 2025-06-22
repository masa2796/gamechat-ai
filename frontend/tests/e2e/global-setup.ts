import { FullConfig } from '@playwright/test';

async function globalSetup(_config: FullConfig) {
  // テスト用の環境変数を設定
  process.env.NEXT_PUBLIC_SKIP_RECAPTCHA = 'true';
  process.env.NEXT_PUBLIC_API_KEY = 'test-api-key';
  process.env.NEXT_PUBLIC_ENVIRONMENT = 'test';
  
  // Firebase設定をテスト用に設定
  process.env.NEXT_PUBLIC_FIREBASE_API_KEY = 'dummy-api-key-for-e2e';
  process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN = 'test.firebaseapp.com';
  process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID = 'test-project';
  process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET = 'test-project.appspot.com';
  process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID = '123456789';
  process.env.NEXT_PUBLIC_FIREBASE_APP_ID = '1:123456789:web:abcdef';
  
  console.log('E2E test environment setup completed');
}

export default globalSetup;
