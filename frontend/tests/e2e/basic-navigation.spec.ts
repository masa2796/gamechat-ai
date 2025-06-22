import { test, expect } from '@playwright/test';

test.describe('GameChat AI - Basic Navigation', () => {
  test('should display the main page', async ({ page }) => {
    await page.goto('/');
    
    // ページの読み込み完了を待機
    await page.waitForLoadState('networkidle');
    
    // アプリタイトルが表示されることを確認
    await expect(page.locator('[data-testid="app-title"]')).toHaveText('GameChat AI');
    
    // ウェルカムメッセージが表示されることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
    
    // 基本的なUI要素が表示されることを確認
    await expect(page.locator('[data-testid="message-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="send-button"]')).toBeVisible();
  });

  test('should navigate to chat interface', async ({ page }) => {
    await page.goto('/');
    
    // ページの読み込み完了を待機
    await page.waitForLoadState('networkidle');
    
    // チャットインターフェースが直接表示されることを確認（SPAなので遷移なし）
    await expect(page.locator('[data-testid="chat-messages"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-input-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
  });

  test('should handle responsive design', async ({ page }) => {
    // デスクトップサイズ
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="message-input"]')).toBeVisible();

    // タブレットサイズ
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('[data-testid="message-input"]')).toBeVisible();

    // モバイルサイズ
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('[data-testid="message-input"]')).toBeVisible();
  });
});
