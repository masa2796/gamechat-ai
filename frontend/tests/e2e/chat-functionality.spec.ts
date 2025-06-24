import { test, expect } from '@playwright/test';

test.describe('GameChat AI - Chat Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // ホームページ（Assistantコンポーネント）に移動
    await page.goto('/');
    
    // テスト用データ属性を追加してアニメーションを高速化
    await page.addInitScript(() => {
      document.documentElement.setAttribute('data-test-mode', 'true');
    });
    
    // ページの読み込み完了を待機
    await page.waitForLoadState('networkidle');
    
    // 入力フィールドが表示されるまで待機
    await page.waitForSelector('[data-testid="message-input"]', { timeout: 10000 });
    
    // モバイルビューの場合、サイドバーを開いてからすぐに閉じる（app-title確認のため）
    const viewport = page.viewportSize();
    if (viewport && viewport.width < 768) {
      // サイドバートリガーがクリック可能になるまで待機
      await page.waitForSelector('[data-testid="sidebar-trigger"]', { state: 'visible' });
      await page.locator('[data-testid="sidebar-trigger"]').click({ force: true });
      
      // シートが開くまで待機（data-state=openを確認）
      await page.waitForSelector('[data-slot="sheet-content"][data-state="open"]', { timeout: 5000 });
      await page.waitForTimeout(50); // アニメーション安定化（短縮）
      
      // サイドバーを閉じる
      await page.locator('[data-testid="sidebar-trigger"]').click({ force: true });
      
      // シートが閉じるまで待機（要素が非表示になるまで）
      await page.waitForSelector('[data-slot="sheet-content"]', { state: 'detached', timeout: 5000 });
      await page.waitForTimeout(50); // アニメーション完了待機（短縮）
    }
  });

  test('should display chat interface', async ({ page }) => {
    // モバイルビューの場合、サイドバーを開いてapp-titleを確認
    const viewport = page.viewportSize();
    if (viewport && viewport.width < 768) {
      // サイドバートリガーがクリック可能になるまで待機
      await page.waitForSelector('[data-testid="sidebar-trigger"]', { state: 'visible' });
      await page.locator('[data-testid="sidebar-trigger"]').click({ force: true });
      
      // シートが開くまで待機（data-state=openを確認）
      await page.waitForSelector('[data-slot="sheet-content"][data-state="open"]', { timeout: 5000 });
      await page.waitForTimeout(50); // アニメーション安定化（短縮）
    }
    
    // ページタイトルを確認（data-testidを使用）
    await expect(page.locator('[data-testid="app-title"]')).toHaveText('GameChat AI');
    
    // モバイルビューの場合、サイドバーを閉じる
    if (viewport && viewport.width < 768) {
      await page.locator('[data-testid="sidebar-trigger"]').click({ force: true });
      
      // シートが閉じるまで待機（要素が非表示になるまで）
      await page.waitForSelector('[data-slot="sheet-content"]', { state: 'detached', timeout: 5000 });
      await page.waitForTimeout(50); // アニメーション完了待機（短縮）
    }
    
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
    // バックエンドAPIの疎通確認
    try {
      // より一般的なヘルスチェックエンドポイントを試行
      const healthEndpoints = [
        'http://localhost:8001/health',
        'http://localhost:8001/docs',
        'http://localhost:8001/',
      ];
      
      let backendAvailable = false;
      for (const endpoint of healthEndpoints) {
        try {
          const healthCheck = await fetch(endpoint);
          if (healthCheck.ok || healthCheck.status === 200) {
            backendAvailable = true;
            break;
          }
        } catch {
          // 次のエンドポイントを試行
        }
      }
      
      if (!backendAvailable) {
        console.log('Backend API not available, skipping test');
        return;
      }
    } catch (error) {
      console.log('Backend API not available, skipping test:', error);
      return;
    }

    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // テストメッセージを入力
    await messageInput.fill('こんにちは、ゲームについて教えてください');
    
    // DOM更新を確実にするため短時間待機
    await page.waitForTimeout(100);
    
    // 送信ボタンが有効で表示されていることを確認
    await expect(sendButton).toBeVisible();
    await expect(sendButton).toBeEnabled();
    
    // メッセージを送信
    await sendButton.click();
    
    // 状態の更新を少し待つ
    await page.waitForTimeout(200);
    
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
    // バックエンドAPIの疎通確認
    try {
      const healthEndpoints = [
        'http://localhost:8001/health',
        'http://localhost:8001/docs',
        'http://localhost:8001/',
      ];
      
      let backendAvailable = false;
      for (const endpoint of healthEndpoints) {
        try {
          const healthCheck = await fetch(endpoint);
          if (healthCheck.ok || healthCheck.status === 200) {
            backendAvailable = true;
            break;
          }
        } catch {
          // 次のエンドポイントを試行
        }
      }
      
      if (!backendAvailable) {
        console.log('Backend API not available, skipping test');
        return;
      }
    } catch (error) {
      console.log('Backend API not available, skipping test:', error);
      return;
    }

    const messageInput = page.locator('[data-testid="message-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    
    // 最初のメッセージを送信
    await messageInput.fill('最初のメッセージ');
    await page.waitForTimeout(100); // DOM更新待機
    await expect(sendButton).toBeVisible();
    await expect(sendButton).toBeEnabled();
    await sendButton.click();
    
    // メッセージがクリアされることを確認
    await expect(messageInput).toHaveValue('');
    
    // 最初のメッセージが表示されるまで待機
    await expect(page.locator('[data-testid="user-message"]:has-text("最初のメッセージ")')).toBeVisible();
    
    // 2番目のメッセージを送信
    await messageInput.fill('2番目のメッセージ');
    await page.waitForTimeout(100); // DOM更新待機
    await expect(sendButton).toBeVisible();
    await expect(sendButton).toBeEnabled();
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
    await messageInput.click(); // フォーカスを当てる
    await messageInput.fill('テストメッセージ');
    // DOM更新を確実にするため待機
    await page.waitForTimeout(100);
    await expect(sendButton).toBeEnabled();
    
    // テキストを削除すると送信ボタンが無効になる
    await messageInput.click();
    await messageInput.clear();
    // DOM更新を確実にするため待機
    await page.waitForTimeout(100);
    await expect(sendButton).toBeDisabled();
  });

  test('should handle Enter key for message submission', async ({ page }) => {
    // バックエンドAPIの疎通確認
    try {
      const healthEndpoints = [
        'http://localhost:8001/health',
        'http://localhost:8001/docs',
        'http://localhost:8001/',
      ];
      
      let backendAvailable = false;
      for (const endpoint of healthEndpoints) {
        try {
          const healthCheck = await fetch(endpoint);
          if (healthCheck.ok || healthCheck.status === 200) {
            backendAvailable = true;
            break;
          }
        } catch {
          // 次のエンドポイントを試行
        }
      }
      
      if (!backendAvailable) {
        console.log('Backend API not available, skipping test');
        return;
      }
    } catch (error) {
      console.log('Backend API not available, skipping test:', error);
      return;
    }

    const messageInput = page.locator('[data-testid="message-input"]');
    
    // テストメッセージを入力
    await messageInput.fill('Enterキーでのテスト');
    await page.waitForTimeout(100); // DOM更新待機
    
    // Enterキーで送信
    await messageInput.press('Enter');
    
    // 状態の更新を少し待つ
    await page.waitForTimeout(200);
    
    // ウェルカムメッセージが消えることを確認
    await expect(page.locator('[data-testid="welcome-message"]')).not.toBeVisible();
    
    // ユーザーメッセージが表示されることを確認
    await expect(page.locator('[data-testid="user-message"]:has-text("Enterキーでのテスト")')).toBeVisible();
  });
});
