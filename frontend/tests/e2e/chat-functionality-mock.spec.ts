import { test, expect } from '@playwright/test';

test.describe('GameChat AI - Chat Functionality with API Mock', () => {
  test.beforeEach(async ({ page }) => {
    // API呼び出しをモック（少し遅延を追加）
    await page.route('/api/rag/query', async (route) => {
      const request = route.request();
      console.log('API mock called with method:', request.method());
      
      // 少し遅延を追加してローディング状態をテスト可能にする
      await new Promise(resolve => setTimeout(resolve, 500));
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: 'これはテスト用のAI応答です。ゲームに関する質問にお答えします。',
          context: ['テストコンテキスト1', 'テストコンテキスト2'],
          status: 'success'
        })
      });
    });

    // ホームページ（Assistantコンポーネント）に移動
    await page.goto('/');
    
    // ページの読み込み完了を待機
    await page.waitForLoadState('networkidle');
    
    // 入力フィールドが表示されるまで待機
    await page.waitForSelector('[data-testid="message-input"]', { timeout: 10000 });
  });

  test('should display chat interface with mocked API', async ({ page }) => {
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

  test('should send and receive mocked messages', async ({ page }) => {
    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // テストメッセージを入力
    await messageInput.fill('テスト用の質問です');
    
    // メッセージを送信
    await sendButton.click();
    
    // ウェルカムメッセージが消えることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).not.toBeVisible();
    
    // ユーザーメッセージが表示されることを確認
    await expect(page.locator('[data-testid="user-message"]:has-text("テスト用の質問です")')).toBeVisible();
    
    // ローディング状態が表示されることを確認（遅延があるので表示されるはず）
    await expect(page.locator('[data-testid="loading-message"]')).toBeVisible();
    
    // AI応答を待機
    await page.waitForSelector('[data-testid="ai-message"]', { timeout: 10000 });
    
    // ローディングが消えることを確認
    await expect(page.locator('[data-testid="loading-message"]')).not.toBeVisible();
    
    // AI応答が表示されることを確認
    await expect(page.locator('[data-testid="ai-message"]').first()).toBeVisible();
    await expect(page.locator('[data-testid="ai-message"]:has-text("これはテスト用のAI応答です")')).toBeVisible();
    
    // 入力フィールドがクリアされることを確認
    await expect(messageInput).toHaveValue('');
  });

  test('should handle multiple messages with mock', async ({ page }) => {
    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // 最初のメッセージを送信
    await messageInput.fill('最初の質問');
    await sendButton.click();
    
    // 最初のメッセージペアが表示されるまで待機
    await expect(page.locator('[data-testid="user-message"]:has-text("最初の質問")')).toBeVisible();
    await expect(page.locator('[data-testid="ai-message"]').first()).toBeVisible();
    
    // 2番目のメッセージを送信
    await messageInput.fill('2番目の質問');
    await sendButton.click();
    
    // 両方のメッセージペアが表示されることを確認
    await expect(page.locator('[data-testid="user-message"]:has-text("最初の質問")')).toBeVisible();
    await expect(page.locator('[data-testid="user-message"]:has-text("2番目の質問")')).toBeVisible();
    await expect(page.locator('[data-testid="ai-message"]')).toHaveCount(2);
  });

  test('should handle API error gracefully', async ({ page }) => {
    // エラーレスポンスを返すようにモックを変更
    await page.route('/api/rag/query', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: { message: 'Internal Server Error' }
        })
      });
    });

    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // テストメッセージを入力
    await messageInput.fill('エラーテスト');
    
    // メッセージを送信
    await sendButton.click();
    
    // ユーザーメッセージが表示されることを確認
    await expect(page.locator('[data-testid="user-message"]:has-text("エラーテスト")')).toBeVisible();
    
    // エラーメッセージが表示されることを確認
    await expect(page.locator('[data-testid="ai-message"]:has-text("エラーが発生しました")')).toBeVisible();
  });

  test('should handle network timeout', async ({ page }) => {
    // タイムアウトを返すようにモックを設定
    await page.route('/api/rag/query', async (route) => {
      // 長時間待機してタイムアウトをシミュレート
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 408,
        contentType: 'application/json',
        body: JSON.stringify({
          error: { message: 'Request Timeout' }
        })
      });
    });

    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // テストメッセージを入力
    await messageInput.fill('タイムアウトテスト');
    
    // メッセージを送信
    await sendButton.click();
    
    // ローディング状態が表示されることを確認
    await expect(page.locator('[data-testid="loading-message"]')).toBeVisible();
    
    // エラーメッセージが表示されることを確認
    await expect(page.locator('[data-testid="ai-message"]:has-text("エラーが発生しました")')).toBeVisible();
  });
});
