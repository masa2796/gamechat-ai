import { test, expect } from '@playwright/test';

test.describe('GameChat AI - Basic Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      document.documentElement.setAttribute('data-test-mode', 'true');
    });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('[data-testid="app-title"]', { timeout: 15000 });
  });

  test('should display the main page', async ({ page }) => {
    // ページの読み込み完了を待機
    await page.waitForLoadState('networkidle');
    
    // モバイルビューの場合、サイドバーを開く
    const viewport = page.viewportSize();
    if (viewport && viewport.width < 768) {
      await page.locator('[data-testid="sidebar-trigger"]').click();
      await page.waitForTimeout(500); // サイドバーアニメーション待機
    }
    
    // アプリタイトルが表示されることを確認
    await expect(page.locator('[data-testid="app-title"]')).toHaveText('GameChat AI');
    
    // ウェルカムメッセージが表示されることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).toBeVisible();
    
    // 基本的なUI要素が表示されることを確認
    await expect(page.locator('[data-testid="message-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="send-button"]')).toBeVisible();
  });

  test('should navigate to chat interface', async ({ page }) => {
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
    
    // モバイルビューでサイドバーを開いてapp-titleを確認
    await page.locator('[data-testid="sidebar-trigger"]').click();
    await page.waitForTimeout(500); // サイドバーアニメーション待機
    await expect(page.locator('[data-testid="app-title"]')).toHaveText('GameChat AI');
  });
});
