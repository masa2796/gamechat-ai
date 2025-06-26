import { FullConfig } from '@playwright/test';
import { config } from 'dotenv';
import path from 'path';

async function globalSetup(_config: FullConfig) {
  // Load test environment variables from .env.test
  const envPath = path.resolve(__dirname, '../../.env.test');
  console.log('Loading test environment from:', envPath);
  
  const result = config({ path: envPath });
  if (result.error) {
    console.warn('Failed to load .env.test:', result.error);
  } else {
    console.log('Test environment loaded successfully');
  }

  // テスト用の環境変数を設定/上書き
  process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA = 'true';
  process.env.NEXT_PUBLIC_ENVIRONMENT = 'test';
  process.env.NEXT_PUBLIC_API_KEY = 'test-api-key';
  process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY = ''; // reCAPTCHAを完全に無効化
  
  // Firebase設定をテスト用に設定
  process.env.NEXT_PUBLIC_FIREBASE_API_KEY = 'dummy-api-key-for-e2e';
  process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN = 'test.firebaseapp.com';
  process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID = 'test-project';
  process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET = 'test-project.appspot.com';
  process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID = '123456789';
  process.env.NEXT_PUBLIC_FIREBASE_APP_ID = '1:123456789:web:abcdef';
  
  // E2Eテスト用の追加環境変数（必要に応じて）
  process.env.NEXT_PUBLIC_TEST_MODE = 'true';
  
  console.log('E2E test environment setup completed');
  console.log('NEXT_PUBLIC_DISABLE_RECAPTCHA:', process.env.NEXT_PUBLIC_DISABLE_RECAPTCHA);
  console.log('NEXT_PUBLIC_ENVIRONMENT:', process.env.NEXT_PUBLIC_ENVIRONMENT);
}

export default globalSetup;
