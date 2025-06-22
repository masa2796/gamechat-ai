import { test, expect } from '@playwright/test';

test.describe('GameChat AI - Chat Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // ホームページ（Assistantコンポーネント）に移動
    await page.goto('/');
    
    // ページの読み込み完了を待機
    await page.waitForLoadState('networkidle');
    
    // 入力フィールドが表示されるまで待機
    await page.waitForSelector('[data-testid="message-input"]', { timeout: 10000 });
  });

  test('should display chat interface', async ({ page }) => {
    // ページタイトルを確認（data-testidを使用）
    await expect(page.locator('[data-testid="app-title"]')).toHaveText('GameChat AI');
    
    // ウェルカムメッセージが表示されることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
    await expect(page.locator('text=GameChat AIへようこそ！')).toBeVisible();
    await expect(page.locator('text=ゲームに関する質問をお気軽にどうぞ。')).toBeVisible();
    
    // チャット入力フィールドが表示されることを確認
    await expect(page.locator('[data-testid="message-input"]')).toBeVisible();
    
    // 送信ボタンが表示されることを確認
    await expect(page.locator('[data-testid="send-button"]')).toBeVisible();
  });

  test('should send and receive messages', async ({ page }) => {
    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // テストメッセージを入力
    await messageInput.fill('こんにちは、ゲームについて教えてください');
    
    // メッセージを送信
    await sendButton.click();
    
    // ウェルカムメッセージが消えることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).not.toBeVisible();
    
    // ユーザーメッセージが表示されることを確認
    await expect(page.locator('[data-testid="user-message"]').first()).toBeVisible();
    await expect(page.locator('[data-testid="user-message"]:has-text("こんにちは、ゲームについて教えてください")')).toBeVisible();
    
    // ローディング状態が表示されることを確認
    await expect(page.locator('[data-testid="loading-message"]')).toBeVisible();
    
    // AI応答を待機（最大30秒）
    await page.waitForSelector('[data-testid="ai-message"]', { timeout: 30000 });
    
    // ローディングが消えることを確認
    await expect(page.locator('[data-testid="loading-message"]')).not.toBeVisible();
    
    // AI応答が表示されることを確認
    await expect(page.locator('[data-testid="ai-message"]').first()).toBeVisible();
  });

  test('should handle empty message submission', async ({ page }) => {
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // 初期状態で送信ボタンが無効化されていることを確認
    await expect(sendButton).toBeDisabled();
    
    // 空のメッセージで送信を試行しても何も起こらないことを確認
    await sendButton.click({ force: true });
    
    // ウェルカムメッセージが残ることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
  });

  test('should maintain chat history', async ({ page }) => {
    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // 最初のメッセージを送信
    await messageInput.fill('最初のメッセージ');
    await sendButton.click();
    
    // メッセージがクリアされることを確認
    await expect(messageInput).toHaveValue('');
    
    // 最初のメッセージが表示されるまで待機
    await expect(page.locator('[data-testid="user-message"]:has-text("最初のメッセージ")')).toBeVisible();
    
    // 2番目のメッセージを送信
    await messageInput.fill('2番目のメッセージ');
    await sendButton.click();
    
    // 両方のメッセージが履歴に残ることを確認
    await expect(page.locator('[data-testid="user-message"]:has-text("最初のメッセージ")')).toBeVisible();
    await expect(page.locator('[data-testid="user-message"]:has-text("2番目のメッセージ")')).toBeVisible();
  });

  test('should enable/disable send button based on input', async ({ page }) => {
    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // 初期状態で送信ボタンが無効
    await expect(sendButton).toBeDisabled();
    
    // テキストを入力すると送信ボタンが有効になる
    await messageInput.fill('テストメッセージ');
    await expect(sendButton).toBeEnabled();
    
    // テキストを削除すると送信ボタンが無効になる
    await messageInput.clear();
    await expect(sendButton).toBeDisabled();
  });

  test('should handle Enter key for message submission', async ({ page }) => {
    const messageInput = page.locator('[data-testid="message-input"]');
    
    // テストメッセージを入力
    await messageInput.fill('Enterキーでのテスト');
    
    // Enterキーで送信
    await messageInput.press('Enter');
    
    // ウェルカムメッセージが消えることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).not.toBeVisible();
    
    // ユーザーメッセージが表示されることを確認
    await expect(page.locator('[data-testid="user-message"]:has-text("Enterキーでのテスト")')).toBeVisible();
  });
});
